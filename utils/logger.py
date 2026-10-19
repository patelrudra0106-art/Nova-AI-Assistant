"""Rich console logging setup for Nova AI Assistant."""

import pyttsx3
import threading
from rich.console import Console
from rich.panel import Panel

# Initialize Rich Console
console = Console()

# Single TTS engine instance - created once, reused
_tts_engine = None
_tts_engine_lock = threading.Lock()

def _get_tts_engine():
    """Get or create the singleton TTS engine."""
    global _tts_engine
    with _tts_engine_lock:
        if _tts_engine is None:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 150)
            voices = _tts_engine.getProperty("voices")
            if len(voices) > 1:
                _tts_engine.setProperty("voice", voices[1].id)
            else:
                _tts_engine.setProperty("voice", voices[0].id)
        return _tts_engine

def speak(text: str, console_obj: Console = None) -> None:
    """
    Speak text using text-to-speech engine.

    Args:
        text: Text to speak
        console_obj: Optional Rich console instance (defaults to global console)
    """
    c = console_obj or console

    # Display on console with panel
    c.print(
        Panel(
            f"[bold magenta]{text}[/bold magenta]",
            title="[bold cyan]Nova[/bold cyan]",
            title_align="left",
            border_style="cyan"
        )
    )

    # Use singleton TTS engine
    engine = _get_tts_engine()
    engine.say(text)
    engine.runAndWait()

__all__ = ["console", "speak"]