import json
import hashlib
import threading
import asyncio
import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OptimizedLLMClient:
    """LLM client with response caching"""
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=cfg.openrouter_key,
            timeout=cfg.llm_timeout
        )
        self._cache = {} if cfg.enable_llm_cache else None
        self._cache_lock = threading.Lock()
    
    def _make_cache_key(self, system_prompt: str, history: List[Dict]) -> str:
        """Create cache key from recent context"""
        recent = history[-3:] if len(history) > 3 else history
        content = (system_prompt + json.dumps(recent, default=str)).encode()
        return hashlib.md5(content).hexdigest()
    
    async def reply_async(self, system_prompt: str, history: List[Dict], stream_callback=None) -> Optional[str]:
        """Async LLM call with caching"""
        if len(history) > self.cfg.max_history_length:
            history = history[-self.cfg.max_history_length:]
        
        if self._cache is not None:
            cache_key = self._make_cache_key(system_prompt, history)
            with self._cache_lock:
                if cache_key in self._cache:
                    logger.debug("LLM cache hit")
                    return self._cache[cache_key]
        
        try:
            messages = [{"role": "system", "content": system_prompt}] + history
            
            if self.cfg.enable_llm_streaming and stream_callback:
                response_text = ""
                stream = await asyncio.to_thread(
                    lambda: self.client.chat.completions.create(
                        model=self.cfg.llm_model,
                        temperature=self.cfg.temperature,
                        max_tokens=self.cfg.max_tokens,
                        messages=messages,
                        stream=True
                    )
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        response_text += delta
                        if stream_callback:
                            await stream_callback(delta)
                result = response_text.strip()
            else:
                resp = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.cfg.llm_model,
                    temperature=self.cfg.temperature,
                    max_tokens=self.cfg.max_tokens,
                    messages=messages,
                )
                if resp.choices and resp.choices[0].message:
                    result = resp.choices[0].message.content.strip()
                else:
                    result = None
            
            if result and self._cache is not None:
                with self._cache_lock:
                    self._cache[cache_key] = result
                    if len(self._cache) > self.cfg.llm_cache_size:
                        oldest = next(iter(self._cache))
                        del self._cache[oldest]
            
            return result
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None
