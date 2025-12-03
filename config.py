import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Centralized configuration with environment variable support"""
    # API Keys
    openrouter_key: str = os.getenv("OPENROUTER_KEY", "")
    assemblyai_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    
    # LLM Settings
    llm_model: str = "microsoft/wizardlm-2-8x22b:nitro"
    temperature: float = 0.22
    max_tokens: int = 260
    llm_timeout: float = 15.0
    enable_llm_streaming: bool = False
    enable_llm_cache: bool = True
    llm_cache_size: int = 100
    
    # Interview Settings
    max_turns: int = 9
    max_question_words: int = 15
    approval_threshold: int = 70
    
    # Style/Context Defaults
    default_style: str = "strict"
    default_embassy: str = "generic"
    
    # Paths
    cases_dir: str = "cases"
    
    # Voice / STT Settings
    voice_only: bool = True
    per_turn_timeout_sec: int = 35
    silence_ms: int = 1200
    beep_enabled: bool = True
    post_tts_cooldown_s: float = 0.15
    
    # TTS Settings
    preferred_voice: str = "alloy"
    debug_tts: bool = False
    tts_non_blocking: bool = True
    
    # STT Optimization
    reuse_stt_client: bool = True
    stt_sample_rate: int = 16000
    
    # History Management
    max_history_length: int = 20
    enable_history_compression: bool = True
    
    # Performance
    enable_prefetch: bool = True
    max_workers: int = 3
    
    def __post_init__(self):
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_KEY not set")
        if not self.assemblyai_key:
            raise ValueError("ASSEMBLYAI_API_KEY not set")
        os.makedirs(self.cases_dir, exist_ok=True)
