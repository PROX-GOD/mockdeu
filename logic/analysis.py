import re
from typing import Dict, List, Tuple

class AdministrativeProcessingTracker:
    """Track triggers for administrative processing"""
    
    def __init__(self):
        self.financial_triggers = 0
        self.academic_triggers = 0
        self.consistency_triggers = 0
        self.credibility_triggers = 0
        self.ap_threshold = 2
        
    def analyze_response(self, user_text: str, analysis: Dict, turn: int) -> Dict:
        """Analyze if response triggers administrative processing"""
        triggers = []
        
        if self._financial_uncertainty(user_text):
            self.financial_triggers += 1
            triggers.append("financial verification needed")
            
        if self._academic_issues(user_text, analysis):
            self.academic_triggers += 1
            triggers.append("academic background verification")
            
        if analysis.get('consistency_flags'):
            self.consistency_triggers += 1
            triggers.append("inconsistent information")
            
        if self._credibility_concerns(user_text, analysis):
            self.credibility_triggers += 1
            triggers.append("credibility concerns")
            
        return {
            "triggers": triggers,
            "total_triggers": (self.financial_triggers + self.academic_triggers + 
                              self.consistency_triggers + self.credibility_triggers),
            "should_escalate_ap": self._should_escalate_to_ap(),
            "ap_reason": " & ".join(triggers) if triggers else None
        }
    
    def _financial_uncertainty(self, text: str) -> bool:
        """Detect financial uncertainty that needs verification"""
        uncertainty_phrases = [
            "not sure", "don't know", "maybe", "probably", "i think",
            "my father will arrange", "we have enough", "sufficient funds"
        ]
        
        vague_financial = any(phrase in text.lower() for phrase in uncertainty_phrases)
        no_specifics = not any(word in text.lower() for word in ["salary", "savings", "bank", "amount", "figure"])
        
        return vague_financial or no_specifics
    
    def _academic_issues(self, text: str, analysis: Dict) -> bool:
        """Detect academic issues needing verification"""
        weak_preparation = analysis.get('specificity_score', 0) < 0.3
        vague_motivation = len(text.split()) < 8
        return weak_preparation or vague_motivation
    
    def _credibility_concerns(self, text: str, analysis: Dict) -> bool:
        """Detect general credibility concerns"""
        high_stress = analysis.get('stress_level', 0) > 0.7
        multiple_fillers = text.lower().count('um') + text.lower().count('uh') > 3
        return high_stress or multiple_fillers
    
    def _should_escalate_to_ap(self) -> bool:
        """Determine if case should go to administrative processing"""
        total = (self.financial_triggers + self.academic_triggers + 
                self.consistency_triggers + self.credibility_triggers)
        return total >= self.ap_threshold
    
    def get_ap_reason(self) -> str:
        """Get formatted reason for administrative processing"""
        reasons = []
        if self.financial_triggers >= 2:
            reasons.append("financial verification")
        if self.academic_triggers >= 2:
            reasons.append("academic background review") 
        if self.consistency_triggers >= 2:
            reasons.append("information consistency check")
        if self.credibility_triggers >= 2:
            reasons.append("applicant credibility assessment")
        return " & ".join(reasons) if reasons else "standard administrative review"

class AnswerAnalysis:
    """Enhanced answer analysis with emotion detection hints"""
    PROFAN = {"fuck", "fucked", "shit", "damn", "bitch"}
    HINTS = {
        "academics": ["gpa", "project", "course", "professor", "lab", "semester", "research", "thesis"],
        "funds": ["bank", "loan", "sponsor", "father", "mother", "tuition", "living", "scholarship", "rs", "usd"],
        "ties": ["family", "parents", "home", "property", "house", "land", "return", "community"],
        "intent": ["after graduation", "plan", "career", "job", "company", "return", "goal", "role"],
    }
    
    UNCERTAINTY = ["maybe", "not sure", "i think", "probably", "perhaps", "i guess", "don't know"]
    CONFIDENCE = ["definitely", "certainly", "absolutely", "for sure", "i know"]
    STRESS = ["um", "uh", "er", "well", "actually", "like", "you know"]

    def __init__(self, text: str):
        self.raw = text
        self.lower = text.lower()
        self.tokens = re.findall(r"[a-z0-9]+", self.lower)
        self.token_set = set(self.tokens)
        self.length = len(self.tokens)
        self.profanity = bool(self.token_set & self.PROFAN)
        self.numbers = re.findall(r"\b\d+(?:\.\d+)?\b", self.lower)
        self.primary = self._primary_cat()
        self.vague = self.length < 4 or any(w in self.token_set for w in self.UNCERTAINTY)
        self.bio_hint = any(w in self.token_set for w in ["biology", "biological", "life", "zoology"])
        self.cs_hint = any(w in self.token_set for w in ["computer", "cs", "programming", "software"])
        self.uni_hint = any(w in self.token_set for w in ["wisconsin", "uwgb", "green", "bay", "university"])
        self.uncertainty_detected = any(w in self.lower for w in self.UNCERTAINTY)
        self.confidence_detected = any(w in self.lower for w in self.CONFIDENCE)
        self.stress_indicators = sum(1 for w in self.STRESS if w in self.lower)
        self.specificity_score = self._calculate_specificity()

    def _primary_cat(self):
        counts = {}
        for k, hints in self.HINTS.items():
            counts[k] = sum(1 for h in hints if h in self.token_set)
        cat = max(counts, key=lambda k: counts[k]) if counts else None
        return cat if cat and counts[cat] > 0 else None

    def _calculate_specificity(self) -> float:
        """Calculate how specific the answer is (0-1)"""
        specific_indicators = [
            r'\$\d+', r'\b\d+\b', r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b(salary|tuition|fee|cost|amount|price)\s+\$?\d+',
            r'\b(company|corporation|organization|university|college)\s+[A-Z]',
            r'\b(position|role|job|career)\s+as\s+[a-z]+',
        ]
        
        matches = 0
        for pattern in specific_indicators:
            if re.search(pattern, self.raw, re.IGNORECASE):
                matches += 1
                
        return min(1.0, matches / 3.0)

    def compact(self):
        return {
            "primary_category": self.primary,
            "numbers": self.numbers[:5],
            "vague": self.vague,
            "profanity": self.profanity,
            "bio_hint": self.bio_hint,
            "cs_hint": self.cs_hint,
            "uni_hint": self.uni_hint,
            "length": self.length,
            "uncertainty": self.uncertainty_detected,
            "confidence": self.confidence_detected,
            "stress_indicators": self.stress_indicators,
            "specificity_score": self.specificity_score,
            "consistency_flags": []
        }

class VisaScorer:
    """Visa scoring system"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.points = 0.0
        self.max_possible = 0.0
        self.evidence = {"ties": [], "funds": [], "academics": [], "intent": []}
        self.categories_scored = set()
        self.response_quality = []
        self.evasiveness = 0
        self.contradictions = []
        self.claims = {}
        self.fraud_flags = []
        self.weights = {"ties": 1.5, "funds": 1.2, "academics": 1.0, "intent": 1.3, "purpose": 1.4}

    def update(self, cat, base_points, text):
        if not text:
            return
        w = self.weights.get(cat, 1.0)
        pts = max(0, min(3, base_points)) * w
        self.max_possible += 3 * w
        t = text.lower()

        kw = {
            "ties": ["family", "parents", "spouse", "children", "property", "house", "land", "job", "return", "home"],
            "funds": ["sponsor", "father", "mother", "bank", "loan", "savings", "salary", "tuition", "fees", "rs", "usd"],
            "academics": ["gpa", "grade", "research", "project", "course", "professor", "university", "computer science", "biology"],
            "intent": ["return", "temporary", "after graduation", "career", "plan", "goal", "role"],
            "purpose": ["tourism", "visit", "conference", "meeting", "business", "medical", "sightseeing", "grand canyon", "disney"],
        }
        matched = any(k in t for k in kw.get(cat, []))
        if cat == "funds" and any(c.isdigit() for c in t):
            matched = True
        if matched:
            self.points += pts
            self.evidence[cat].append(text)
            self.categories_scored.add(cat)
            self.response_quality.append(min(10, len(t.split()) / 4))
        else:
            self.response_quality.append(4)

        if any(p in t for p in ["don't know", "not sure", "maybe", "can't say"]):
            self.evasiveness += 1

        self._track_claims(t)
        if "fake" in t or "arranged" in t:
            self.fraud_flags.append("Possible misrepresentation language")

    def _track_claims(self, t):
        def set_claim(key, val):
            prev = self.claims.get(key)
            if prev and prev != val:
                self.contradictions.append((key, prev, val))
            self.claims[key] = val

        if any(w in t for w in ["father", "mother", "parents", "self", "scholarship", "loan"]):
            set_claim("sponsor", "mentioned")
        if any(w in t for w in ["wisconsin", "green bay", "uwgb", "university", "college"]):
            set_claim("university", "mentioned")
        if any(w in t for w in ["computer science", "cs", "biology", "engineering", "business", "it"]):
            set_claim("major", "mentioned")

    def score(self):
        if self.max_possible == 0:
            return 0
        base = 100.0 * (self.points / self.max_possible)
        penalty = (self.evasiveness * 3) + (len(self.contradictions) * 8) + (len(set(self.evidence.keys()) - self.categories_scored) * 8)
        quality = (sum(self.response_quality) / max(1, len(self.response_quality))) - 5.0
        final = base - penalty + (quality * 2.0)
        return max(0, min(100, round(final)))

    def summary(self):
        return {
            "score": self.score(),
            "evidence_count": {k: len(v) for k, v in self.evidence.items()},
            "categories_covered": list(self.categories_scored),
            "evasiveness": self.evasiveness,
            "contradictions": self.contradictions,
            "fraud_flags": self.fraud_flags,
        }
