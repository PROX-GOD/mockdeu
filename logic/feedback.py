import os
import logging
from typing import List, Dict
from termcolor import colored
from mockdeu.core.llm import OptimizedLLMClient

logger = logging.getLogger(__name__)

class DetailedFeedbackGenerator:
    """Generates detailed feedback and critique for the interview"""
    def __init__(self, cfg):
        self.cfg = cfg
        self.llm = OptimizedLLMClient(cfg)

    async def generate_feedback(self, history: List[Dict], case_id: str):
        print(colored("\n🔄 Generating detailed feedback... (this may take a moment)", "magenta"))
        
        # Filter relevant history
        conversation = []
        for msg in history:
            if msg["role"] == "user":
                conversation.append(f"APPLICANT: {msg['content']}")
            elif msg["role"] == "assistant":
                 content = msg["content"]
                 # Skip internal analysis logs
                 if "ANALYSIS (INTERNAL" in content:
                     continue
                 
                 if "QUESTION:" in content:
                     try:
                        q = content.split("QUESTION:")[1].split("\n")[0].strip()
                        conversation.append(f"OFFICER: {q}")
                     except:
                        conversation.append(f"OFFICER: {content}")
                 else:
                     conversation.append(f"OFFICER: {content}")

        transcript_text = "\n".join(conversation)
        
        prompt = f"""
You are an expert F-1/B1/B2 Visa Interview Coach. Analyze the following interview transcript and provide detailed feedback.

TRANSCRIPT:
{transcript_text}

OUTPUT FORMAT (Markdown):
# Interview Feedback

## Overall Assessment
<Brief summary of performance>

## Question-by-Question Analysis

### Turn 1
**Officer**: <Question>
**You**: <Answer>
**Critique**: <What was wrong? Vague? Too short? Nervous?>
**Improvement**: <How to fix it>
**Better Answer**: <Write a perfect example answer>

... (repeat for all turns)

## Final Tips
- <Tip 1>
- <Tip 2>
""".strip()
        
        system_prompt = "You are a helpful and strict Visa Coach."
        feedback_history = [{"role": "user", "content": prompt}]
        
        feedback = await self.llm.reply_async(system_prompt, feedback_history)
        
        if feedback:
            self._save_feedback(case_id, feedback)
            print(colored("\n✅ Detailed feedback generated!", "green"))
            print(colored(f"Saved to cases/{case_id}_feedback.md", "cyan"))
            
            # Print a sneak peek
            print(colored("\n--- FEEDBACK SNEAK PEEK ---", "yellow"))
            lines = feedback.split('\n')
            for line in lines[:20]:
                print(line)
            print(colored("...", "yellow"))
        else:
            print(colored("\n❌ Failed to generate feedback.", "red"))

    def _save_feedback(self, case_id: str, content: str):
        path = os.path.join(self.cfg.cases_dir, f"{case_id}_feedback.md")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
