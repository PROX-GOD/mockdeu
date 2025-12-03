import io
import re
import queue
import wave
import threading
import asyncio
import logging
import pyttsx3
import pyaudio

# Optional: A4F local TTS
try:
    from a4f_local import A4F
    HAS_A4F = True
except Exception:
    HAS_A4F = False

logger = logging.getLogger(__name__)

class NonBlockingTTS:
    """TTS with async playback using PyAudio callbacks"""
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.a4f = None
        self.fallback = None
        self._pa = None
        self._playback_queue = queue.Queue()
        self._is_playing = threading.Event()
        self._playback_thread = None
        self._init_engines()
        
    def _init_engines(self):
        """Initialize TTS engines"""
        if HAS_A4F:
            try:
                self.a4f = A4F()
            except Exception as e:
                logger.warning(f"A4F init failed: {e}")
        
        try:
            self.fallback = pyttsx3.init()
            voices = self.fallback.getProperty("voices")
            for v in voices:
                name = (v.name or "").lower()
                if any(x in name for x in ["zira", "hazel", "samantha", "female"]):
                    self.fallback.setProperty("voice", v.id)
                    break
            self.fallback.setProperty("rate", 165)
            self.fallback.setProperty("volume", 1.0)
        except Exception as e:
            logger.error(f"Fallback TTS init failed: {e}")
        
        if self.cfg.tts_non_blocking:
            self._pa = pyaudio.PyAudio()
            self._playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self._playback_thread.start()
    
    def _playback_worker(self):
        """Background thread for audio playback"""
        while True:
            try:
                wav_bytes = self._playback_queue.get(timeout=1.0)
                if wav_bytes is None:
                    break
                self._play_wav_sync(wav_bytes)
                self._playback_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Playback error: {e}")
    
    def _play_wav_sync(self, wav_bytes: bytes):
        """Synchronous WAV playback"""
        try:
            wf = wave.open(io.BytesIO(wav_bytes), 'rb')
            stream = self._pa.open(
                format=self._pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )
            chunk = 1024
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            stream.stop_stream()
            stream.close()
            wf.close()
        except Exception as e:
            logger.error(f"WAV playback error: {e}")
    
    async def speak_async(self, text: str, stream: bool = False) -> bool:
        """Async TTS with optional streaming"""
        if not text:
            return False
        
        if stream and len(text) > 50:
            sentences = re.split(r'([.!?]\s+)', text)
            chunks = []
            for i in range(0, len(sentences), 2):
                if i + 1 < len(sentences):
                    chunks.append(sentences[i] + sentences[i+1])
                else:
                    chunks.append(sentences[i])
            
            for chunk in chunks:
                if chunk.strip():
                    await self._speak_chunk(chunk.strip())
                    await asyncio.sleep(0.1)
            return True
        else:
            return await self._speak_chunk(text)
    
    async def _speak_chunk(self, text: str) -> bool:
        """Speak a single chunk of text"""
        if self.a4f:
            try:
                wav_bytes = None
                for key in ("format", "audio_format", "response_format", "container"):
                    try:
                        wav_bytes = self.a4f.audio.speech.create(
                            model="tts-2", input=text, voice=self.cfg.preferred_voice, **{key: "wav"}
                        )
                        if isinstance(wav_bytes, (bytes, bytearray)) and len(wav_bytes) > 44:
                            break
                        wav_bytes = None
                    except Exception:
                        continue
                
                if wav_bytes:
                    if self.cfg.tts_non_blocking:
                        self._playback_queue.put(wav_bytes)
                        await asyncio.sleep(self.cfg.post_tts_cooldown_s)
                        return True
                    else:
                        self._play_wav_sync(wav_bytes)
                        await asyncio.sleep(self.cfg.post_tts_cooldown_s)
                        return True
            except Exception as e:
                logger.debug(f"A4F error: {e}")
        
        if self.fallback:
            def _speak_sync():
                try:
                    cleaned = self._clean_text(text)
                    self.fallback.say(cleaned)
                    self.fallback.runAndWait()
                except Exception as e:
                    logger.error(f"Fallback TTS error: {e}")
            
            if self.cfg.tts_non_blocking:
                threading.Thread(target=_speak_sync, daemon=True).start()
                await asyncio.sleep(self.cfg.post_tts_cooldown_s)
            else:
                _speak_sync()
                await asyncio.sleep(self.cfg.post_tts_cooldown_s)
            return True
        
        return False
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for TTS"""
        repl = {"U.S.": "United States", "F-1": "F one", "I-20": "I twenty", "GPA": "G P A"}
        for k, v in repl.items():
            text = text.replace(k, v)
        return re.sub(r"\s+", " ", text).strip()
    
    def close(self):
        """Cleanup resources"""
        if self._playback_queue:
            self._playback_queue.put(None)
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
