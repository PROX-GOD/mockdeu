import asyncio
import json
import random
import datetime
import logging
from termcolor import colored

from mockdeu.config import Config
from mockdeu.core.stt import OptimizedSTTClient
from mockdeu.core.tts import NonBlockingTTS
from mockdeu.core.llm import OptimizedLLMClient
from mockdeu.logic.ds160 import DS160Manager
from mockdeu.logic.interview import InterviewState, build_realistic_officer_prompt, parse_ai_with_ap
from mockdeu.logic.analysis import AnswerAnalysis, VisaScorer, AdministrativeProcessingTracker
from mockdeu.logic.feedback import DetailedFeedbackGenerator
from mockdeu.utils import save_outputs
from mockdeu.data.seed_data import SEED_QA
from mockdeu.interfaces.base import InterviewInterface

logger = logging.getLogger(__name__)

class InterviewSession:
    """Controller for the interview process"""
    
    def __init__(self, cfg: Config, interface: InterviewInterface):
        self.cfg = cfg
        self.interface = interface
        self.tts = NonBlockingTTS(cfg)
        self.stt = OptimizedSTTClient(cfg)
        self.llm = OptimizedLLMClient(cfg)
        self.ap_tracker = AdministrativeProcessingTracker()
        self.scorer = VisaScorer()
        self.istate = InterviewState()
        self.history = []
        self.transcript = []
        self.ds = DS160Manager()
        
    async def run(self):
        """Run the interview session"""
        if not await self.interface.initialize():
            return
            
        if not await self.stt.initialize_async():
            logger.error("STT initialization failed")
            return

        # DS-160 Data Collection (Simplified for GUI/CLI abstraction)
        # For now, we'll use the CLI-based DS160Manager inside the logic, 
        # but ideally this should also be abstracted via the interface.
        # Since DS160Manager uses `input()`, it might block GUI. 
        # TODO: Refactor DS160Manager to use self.interface.get_input()
        # For this iteration, we assume CLI input for DS-160 or pre-loaded.
        
        # Hack: If GUI, we might want to skip DS-160 input or show a dialog.
        # For now, let's just load it.
        data = self.ds.load() 
        case_id = data["case_id"]
        
        # Pass details to interface for display
        await self.interface.set_case_details(data)

        style = await self.interface.get_input("Enter style (1=strict, 2=skeptical, 3=thorough, 4=friendly): ", ["1", "2", "3", "4"])
        style_map = {"1": "strict", "2": "skeptical", "3": "thorough", "4": "friendly_strict"}
        style = style_map.get(style, self.cfg.default_style)

        embassy = await self.interface.get_input("Enter embassy (1=Kathmandu, 2=Mumbai, 3=Beijing, 4=Generic): ", ["1", "2", "3", "4"])
        emb_map = {"1": "kathmandu", "2": "mumbai", "3": "beijing", "4": "generic"}
        embassy = emb_map.get(embassy, self.cfg.default_embassy)

        system_prompt = build_realistic_officer_prompt(
            json.dumps(data), style, embassy, self.cfg.max_question_words, json.dumps(SEED_QA), data.get("visa_type", "F1")
        )
        
        opening_question = random.choice([
            "Good morning. What's the purpose of your trip to the United States?",
            "Hello, pass me your documents.",
            "Morning. What is the purpose of your trip to the United States?"
        ])
        
        await self._speak_and_log(opening_question)
        self.history.append({"role": "assistant", "content": f"QUESTION: {opening_question}\nSCORE: intent:0"})
        
        decision = None

        for turn in range(self.cfg.max_turns):
            await self.interface.update_status("Listening...")
            
            # STT needs to update interface status
            # We can pass a callback or just let STT print to stdout (which CLI captures)
            # For GUI, we need to poll or use the callback.
            # OptimizedSTTClient currently prints to stdout. 
            # We will wrap it or modify it to use interface later. 
            # For now, let's just use it as is, but we might miss partials in GUI.
            
            user_text = await self.stt.listen_async(
                timeout_sec=self.cfg.per_turn_timeout_sec,
                beep=self.cfg.beep_enabled,
                show_partial=True 
            )
            
            await self.interface.update_status("Processing...")
            
            if not user_text:
                if turn < 2:
                    await self._speak_and_log("I need you to answer the question clearly.")
                    continue
                else:
                    decision = ("DENIED", "Unable to provide clear responses during interview.")
                    break
                    
            await self.interface.display_applicant(user_text)
            self.transcript.append(f"APPLICANT: {user_text}")
            self.history.append({"role": "user", "content": user_text})
            
            # Analysis & Logic (Same as before)
            analysis = AnswerAnalysis(user_text)
            target_cat = self.istate.next_target_category()
            
            if (not self.istate.darwin_check_used) and (analysis.bio_hint or ("biology" in data.get("major", "").lower())):
                target_cat = "academics"
                self.istate.darwin_check_used = True
            
            analysis_injection = (
                "ANALYSIS (INTERNAL - DO NOT OUTPUT):\n"
                f"- Turn: {turn + 1}\n" 
                f"- Answer: {user_text[:200]}\n"
                f"- Primary Category: {analysis.primary or 'unclear'}\n"
                f"- Suggested Next Category: {target_cat}\n"
                "REMINDER: Ask natural follow-up questions."
            )
            self.history.append({"role": "assistant", "content": analysis_injection})
            
            ai_text = await self.llm.reply_async(system_prompt, self.history)
            
            self.history = [m for m in self.history if not m.get("content", "").startswith("ANALYSIS (INTERNAL")]

            if not ai_text:
                fallback = "Let me ask you another question. What confirms you'll return home after studies?"
                await self._speak_and_log(fallback)
                self.history.append({"role": "assistant", "content": f"QUESTION: {fallback}\nSCORE: intent:0"})
                continue
                
            q, decision, done, score_line, dec_line = self._parse_ai(ai_text, user_text)
            
            if done:
                await self._handle_decision(decision)
                break
                
            if q:
                await self._speak_and_log(q)
                self.history.append({"role": "assistant", "content": ai_text})
                
            self.istate.turn += 1
            self.istate.record(q or "", None)

        if not decision:
            decision = self._make_final_decision()
            await self._handle_decision(decision)
            
        self._save_results(case_id, style, embassy, decision)
        
        # Feedback
        feedback_gen = DetailedFeedbackGenerator(self.cfg)
        # We need to capture the feedback output to show in GUI
        # DetailedFeedbackGenerator currently prints and saves.
        # We should modify it or just read the saved file.
        await feedback_gen.generate_feedback(self.history, case_id)
        
        # Read feedback file to show in GUI
        try:
            with open(f"{self.cfg.cases_dir}/{case_id}_feedback.md", "r", encoding="utf-8") as f:
                fb_text = f.read()
            await self.interface.show_feedback(fb_text)
        except Exception:
            pass
            
        self.interface.close()
        self.tts.close()
        self.stt.disconnect()

    async def _speak_and_log(self, text: str):
        await self.interface.display_officer(text)
        await self.tts.speak_async(text)
        self.transcript.append(f"OFFICER: {text}")

    def _parse_ai(self, ai_text, user_text):
        return parse_ai_with_ap(ai_text, user_text, self.scorer)

    async def _handle_decision(self, decision):
        decision_type, reason = decision
        message = f"Decision: {decision_type}. {reason}"
        await self._speak_and_log(message)

    def _make_final_decision(self):
        """Make final decision based on scoring and AP triggers"""
        final_score = self.scorer.score()
        
        if self.ap_tracker.should_escalate_to_ap():
            return ("ADMINISTRATIVE PROCESSING", 
                    f"Case requires verification: {self.ap_tracker.get_ap_reason()}")
        
        if final_score >= 70 and not self.scorer.fraud_flags and not self.scorer.contradictions:
            return ("APPROVED", "Credible non-immigrant intent demonstrated.")
        else:
            reasons = []
            if self.scorer.contradictions:
                reasons.append("inconsistent information")
            if self.scorer.fraud_flags:
                reasons.append("credibility concerns") 
            if final_score < 70:
                reasons.append("insufficient ties demonstration")
                
            reason_text = "; ".join(reasons) or "insufficient evidence of non-immigrant intent"
            return ("DENIED", f"{reason_text} under INA 214(b).")

    def _save_results(self, case_id, style, embassy, decision):
        rep = {
            "case_id": case_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "style": style,
            "embassy": embassy,
            "score": self.scorer.score(),
            "final_decision": {"type": decision[0], "reason": decision[1]}
        }
        save_outputs(case_id, self.transcript, rep, [], cases_dir=self.cfg.cases_dir)
