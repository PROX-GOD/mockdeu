import re
import json
from collections import deque
from functools import lru_cache
from typing import Dict, List, Optional

class InterviewState:
    """Enhanced interview state with adaptive questioning"""
    def __init__(self):
        self.turn = 0
        self.asked_categories = []
        self.category_set = set()
        self.questions_history = deque(maxlen=25)
        self.darwin_check_used = False

    def record(self, q: str, cat_hint: str | None):
        if q:
            self.questions_history.append(self._norm(q))
        if cat_hint:
            self.asked_categories.append(cat_hint)
            self.category_set.add(cat_hint)

    def next_target_category(self):
        order = ["funds", "intent", "ties", "academics"]
        if self.turn < 5 and len(self.category_set) < 3:
            for c in order:
                if c not in self.category_set:
                    return c
        counts = {c: self.asked_categories.count(c) for c in order}
        return min(counts, key=counts.get)

    def too_similar(self, new_q: str, threshold=0.8) -> bool:
        n = self._norm(new_q)
        for prev in self.questions_history:
            if self._jaccard(prev, n) >= threshold:
                return True
        return False

    @staticmethod
    def _norm(s: str):
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        return " ".join(s.split())

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa, sb = set(a.split()), set(b.split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

# ------------------ Realistic Visa Officer Prompt (F1 & B1/B2) ------------------
@lru_cache(maxsize=20)
def build_realistic_officer_prompt(data_str: str, style: str, embassy: str, max_words: int, seed_qa_str: str, visa_type: str = "F1") -> str:
    """Realistic visa officer prompt based on actual interview experiences"""
    data = json.loads(data_str)
    seed_qa = json.loads(seed_qa_str)
    
    # Common Styles
    styles = {
        "strict": "Strict, concise, pressing for specifics; brief acknowledgments; pivot if vague.",
        "medium": "Professional, neutral; steady pacing; thorough but fair.",
        "easy": "Patient, clear, but still formal; helpful but maintains standards.",
        "friendly": "Warm yet professional; conversational but serious about criteria.",
        "skeptical": "Probing, doubtful, hunting for inconsistencies; challenges answers."
    }
    st = styles.get(style, styles["strict"])
    
    if visa_type == "B1/B2":
        return _build_b1b2_prompt(data, st, embassy, max_words)
    else:
        return _build_f1_prompt(data, st, embassy, max_words, seed_qa)

def _build_b1b2_prompt(data: Dict, style: str, embassy: str, max_words: int) -> str:
    return f"""You are a REAL U.S. Consular Officer conducting B1/B2 (Business/Tourism) visa interviews at {embassy.capitalize()} embassy.
    
CRITICAL LEGAL CONTEXT (INA 214(b)):
- Every applicant is PRESUMED to be an immigrant.
- They MUST prove:
  1. Strong ties to home country (Job, Family, Property).
  2. Legitimate purpose of trip (Tourism, Business, Medical).
  3. Ability to pay without working in the US.
  4. Intent to return.

APPLICANT PROFILE:
- Purpose: {data.get('purpose', 'Tourism')}
- Job: {data.get('job_title', 'Unemployed')} at {data.get('company', 'N/A')}
- Income: {data.get('income', '0')}
- Travel History: {data.get('travel_history', 'None')}
- Family in US: {data.get('us_family', 'None')}

INTERVIEW STRATEGY:
1. **The "Job" Check**: Employment is the #1 tie. Ask "What do you do?" immediately.
   - If unemployed/freelancer: HIGH RISK. Drill down on income source.
   - If employed: Ask "How long have you been there?" "What is your salary?"

2. **The "Purpose" Check**:
   - Tourism: "Where are you going?" "Why now?" "How long?" (2 weeks is normal; 6 months is suspicious).
   - Business: "What is the meeting about?" "Who are you meeting?"
   - Family Visit: "What does your relative do?" "Why can't they come here?"

3. **The "Travel" Check**:
   - "Have you traveled to other countries?" (Europe/UK/Aus/Can = Good; No travel = Neutral/Weak).

4. **The "Finance" Check**:
   - "Who is paying?"
   - "How much will this trip cost?"

DECISION LOGIC:
- **APPROVE**: Good job (2+ years), previous travel, clear short trip plan, strong family ties at home.
- **DENY (214b)**: Unemployed, vague plans, long proposed stay, young/single with no ties, or recent refusal.

STYLE: {style}

OUTPUT FORMAT:
QUESTION: <next question>
SCORE: <category>:<1-3> (Categories: ties, purpose, funds)

FINAL DECISION FORMAT:
If APPROVING:
DECISION: APPROVED:<reason>
Then ask: "Do you use social media?" (Mandatory)

If DENYING:
DECISION: DENIED:<concrete 214(b) reason>
"""

def _build_f1_prompt(data: Dict, style: str, embassy: str, max_words: int, seed_qa: List) -> str:
    # Build few-shot examples
    seed_lines = []
    for i, s in enumerate(seed_qa[:5], start=1):
        seed_lines.append(f"EX{i} OFFICER: {s['q']}")
        seed_lines.append(f"EX{i} APPLICANT: {s['a']}")
    seed_block = "\n".join(seed_lines)
    
    emb = {
        "generic": "Standard F-1 adjudication.",
        "kathmandu": "Emphasize verifiable funding sources and home-family ties.",
        "mumbai": "Emphasize academic fit and English proficiency.",
    }
    em = emb.get(embassy, emb["generic"])
    
    return f"""You are a REAL U.S. Consular Officer conducting F-1 visa interviews at {embassy.capitalize()} embassy.
    
CRITICAL PROCEDURES:
1. **SOCIAL MEDIA SCREENING**: Mandatory for approvals.
2. **DS-160 VERIFICATION**: Reference details naturally.
3. **KNOWLEDGE CHECKS**: For biology/science majors, ask one technical question (e.g., Darwin).
4. **FINANCIALS**: Verify sponsor's ability to pay.

APPLICANT PROFILE:
- University: {data.get('university', '')}
- Major: {data.get('major', '')}
- Sponsor: {data.get('sponsor', '')}

STYLE: {style}
EMBASSY CONTEXT: {em}

INTERVIEW FLOW:
1. Purpose/University
2. Academics (GRE/SAT/GPA)
3. Financials (Sponsor income)
4. Ties/Intent

DECISION LOGIC:
- APPROVED: Consistent, credible, clear return intent.
- DENIED: Potential immigrant, weak finances, academic unpreparedness.

OUTPUT FORMAT:
QUESTION: <next question>
SCORE: <category>:<1-3> (Categories: academics, funds, ties, intent)

FINAL DECISION FORMAT:
If APPROVING:
DECISION: APPROVED:<reason>
Then ask: "Do you use social media?"

If DENYING:
DECISION: DENIED:<reason>

EXAMPLES:
{seed_block}
""".strip()



def parse_ai_with_ap(ai_text: str, user_text: str, scorer) -> tuple:
    """Parse AI response with administrative processing support"""
    if not ai_text:
        return None, None, False, None, None
        
    q = None
    decision = None
    cat = "intent"
    pts = 1
    score_line = None
    dec_line = None

    for line in ai_text.splitlines():
        t = line.strip()
        if not t:
            continue
        u = t.upper()
        if u.startswith("QUESTION:"):
            q = t[9:].strip()
        elif u.startswith("SCORE:"):
            score_line = t
            try:
                body = t[6:].strip()
                c, p = body.split(":", 1)
                c = c.strip().lower()
                m = {"education": "academics", "financial": "funds", "finance": "funds", "family": "ties", "purpose": "intent"}
                cat = m.get(c, c)
                pts = int(p.strip())
            except Exception:
                pass
        elif u.startswith("DECISION:"):
            dec_line = t
            try:
                body = t[9:].strip()
                if ":" in body:
                    typ, reason = body.split(":", 1)
                    decision = (typ.strip(), reason.strip())
                else:
                    decision = (body.strip(), "Based on interview responses")
            except Exception:
                pass

    if cat in {"academics", "funds", "ties", "intent", "purpose"}:
        scorer.update(cat, pts, user_text)

    if q:
        # Basic sanitization
        if "ds-160" in q.lower():
            pass
        elif any(x in q.lower() for x in ["show me", "provide document"]):
             q = "Can you explain that in more detail?"

    return q, decision, decision is not None, score_line, dec_line
