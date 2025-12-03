import sys
import time
import queue
import threading
import asyncio
import logging
from typing import Optional
from termcolor import colored

import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

# Optional Windows beep
try:
    import winsound
    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False

logger = logging.getLogger(__name__)

class OptimizedSTTClient:
    """AssemblyAI STT with persistent connection and faster response"""
    
    def __init__(self, cfg):
        self.cfg = cfg
        aai.settings.api_key = cfg.assemblyai_key
        self.client = None
        self._mic_stream = None
        self._streaming_thread = None
        self._transcripts_queue = queue.Queue()
        self._state = {"connected": False, "partial": "", "stop": False}
        self._lock = threading.Lock()
    
    def _create_client(self):
        """Create and configure streaming client"""
        client = StreamingClient(
            StreamingClientOptions(
                api_key=self.cfg.assemblyai_key,
                api_host="streaming.assemblyai.com"
            )
        )
        
        def on_begin(c, ev: BeginEvent):
            with self._lock:
                self._state["connected"] = True
                self._state["partial"] = ""
            try:
                c.set_params(StreamingSessionParameters(format_turns=True))
            except Exception:
                pass
        
        def on_turn(c, ev: TurnEvent):
            if ev.transcript:
                with self._lock:
                    self._state["partial"] = ev.transcript
                if ev.end_of_turn:
                    self._transcripts_queue.put(ev.transcript)
                    with self._lock:
                        self._state["partial"] = ""
                    if not ev.turn_is_formatted:
                        try:
                            c.set_params(StreamingSessionParameters(format_turns=True))
                        except Exception:
                            pass
        
        def on_end(c, ev: TerminationEvent):
            with self._lock:
                self._state["connected"] = False
        
        def on_error(c, err: StreamingError):
            with self._lock:
                self._state["connected"] = False
            logger.error(f"Streaming error: {err}")
        
        client.on(StreamingEvents.Begin, on_begin)
        client.on(StreamingEvents.Turn, on_turn)
        client.on(StreamingEvents.Termination, on_end)
        client.on(StreamingEvents.Error, on_error)
        
        return client
    
    async def initialize_async(self) -> bool:
        """Initialize and connect STT client"""
        if self.cfg.reuse_stt_client and self.client is not None:
            return True
        
        try:
            self.client = self._create_client()
            await asyncio.to_thread(
                self.client.connect,
                StreamingParameters(
                    sample_rate=self.cfg.stt_sample_rate,
                    format_turns=True,
                    end_utterance_silence_threshold=self.cfg.silence_ms,
                )
            )
            return True
        except Exception as e:
            logger.error(f"STT connection error: {e}")
            return False
    
    async def listen_async(self, timeout_sec: int = None, beep: bool = False, show_partial: bool = True) -> Optional[str]:
        """Listen for speech asynchronously with real-time partial transcript display"""
        if timeout_sec is None:
            timeout_sec = self.cfg.per_turn_timeout_sec
        
        # Clear any old transcripts
        while not self._transcripts_queue.empty():
            try:
                self._transcripts_queue.get_nowait()
            except queue.Empty:
                break
        
        with self._lock:
            self._state["partial"] = ""
        
        await asyncio.sleep(0.1)
        
        if not self._state["connected"]:
            if not await self.initialize_async():
                return None
        
        if self._streaming_thread is None or not self._streaming_thread.is_alive():
            self._state["stop"] = False
            self._mic_stream = aai.extras.MicrophoneStream(sample_rate=self.cfg.stt_sample_rate)
            
            def _stream():
                try:
                    self.client.stream(self._mic_stream)
                except Exception as e:
                    if not self._state["stop"]:
                        logger.error(f"Stream error: {e}")
            
            self._streaming_thread = threading.Thread(target=_stream, daemon=True)
            self._streaming_thread.start()
        
        if beep and HAS_WINSOUND:
            try:
                winsound.Beep(1200, 150)
            except Exception:
                pass
        
        print(colored("\n🎤 Listening... Speak, then pause.", "cyan", attrs=["bold"]))
        start_time = time.time()
        last_partial = ""
        sys.stdout.flush()
        
        while time.time() - start_time < timeout_sec:
            try:
                text = self._transcripts_queue.get(timeout=0.1)
                if text and text.strip():
                    self._print_status(f"{colored('📝 You said:', 'green', attrs=['bold'])} {colored(text.strip(), 'white')}")
                    print() # Newline after final transcript
                    sys.stdout.flush()
                    return text.strip()
            except queue.Empty:
                with self._lock:
                    partial = self._state["partial"].strip()
                    if show_partial and partial and partial != last_partial:
                        self._print_status(f"{colored('🎤 You:', 'cyan')} {colored(partial, 'yellow')}")
                        last_partial = partial
                    elif not partial and last_partial:
                        self._print_status("")
                        last_partial = ""
                    if not self._state["connected"]:
                        break
                await asyncio.sleep(0.05)
                continue
        
        with self._lock:
            partial = self._state["partial"].strip()
            if partial:
                self._print_status(f"{colored('📝 You said:', 'green', attrs=['bold'])} {colored(partial, 'white')}")
                print()
                sys.stdout.flush()
                return partial
        
        if last_partial:
            print("\r" + " " * (len(last_partial) + 20), end="", flush=True)
        print(colored("\r❌ No speech captured", "red, attrs=['bold']"))
        sys.stdout.flush()
        return None
    
    def _print_status(self, text: str):
        """Print status with line clearing to prevent artifacts"""
        # Truncate text if it's too long for a single line (assuming 100 chars width)
        max_len = 90
        if len(text) > max_len:
            text = "..." + text[-(max_len-3):]
            
        # ANSI escape code to clear the entire line: \033[2K
        # Move cursor to beginning of line: \r
        sys.stdout.write("\033[2K\r" + text)
        sys.stdout.flush()
    
    def disconnect(self):
        """Disconnect STT client"""
        with self._lock:
            self._state["stop"] = True
            self._state["connected"] = False
        
        if self.client:
            try:
                self.client.disconnect(terminate=True)
            except Exception:
                pass
        
        if self._mic_stream:
            try:
                self._mic_stream.close()
            except Exception:
                pass
