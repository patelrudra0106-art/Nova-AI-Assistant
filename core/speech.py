"""Speech recognition and text-to-speech with thread-safe locking."""

import speech_recognition as sr
from typing import Optional
import threading
from utils.logger import console, speak
from utils.network import is_online

class SpeechManager:
    """
    Manage speech recognition and text-to-speech with thread safety.

    This class ensures that multiple threads can speak simultaneously
    without conflict, and provides robust error handling for audio input.
    """

    def __init__(
        self,
        pause_threshold: float = 1.5,
        energy_threshold: int = 300,
        dynamic_energy: bool = True
    ):
        """
        Initialize speech manager.

        Args:
            pause_threshold: Silence duration in seconds before recognizing phrase
            energy_threshold: Minimum audio energy required to consider voice input
            dynamic_energy: Whether to use dynamic energy thresholding
        """
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy
        self.recognizer.energy_threshold = energy_threshold
        self.speak_lock = threading.Lock()

    def listen(
        self,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None
    ) -> Optional[str]:
        """
        Listen for voice input from the microphone.

        Args:
            timeout: Maximum time to wait for speech in seconds (None = unlimited)
            phrase_time_limit: Maximum duration of speech in seconds (None = unlimited)

        Returns:
            Transcribed text, or empty string if no speech detected or error occurs
        """
        # Do NOT hold speak_lock during microphone access - avoids deadlock with speak()
        with sr.Microphone() as source:
            with console.status("[bold green]Nova is Listening...", spinner="earth"):
                try:
                    audio = self.recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_time_limit
                    )
                    command = self.recognizer.recognize_google(audio)
                    console.print(f"[bold green]➤ User:[/bold green] {command}")
                    return command.lower()
                except sr.WaitTimeoutError:
                    return ""
                except sr.UnknownValueError:
                    return ""  # Could not understand audio
                except sr.RequestError as e:
                    console.print("[bold yellow]➤ Offline Mode:[/bold yellow] "
                                 "Speech service unavailable.")
                    # Fallback to text input - only works in main thread
                    try:
                        cmd = console.input("[bold cyan]➤ Type your command: [/bold cyan]")
                        return cmd.lower()
                    except Exception:
                        return ""
                except Exception as e:
                    return ""  # All other errors result in silence

    def speak_from_text(
        self,
        text: str,
        console_obj = None
    ) -> None:
        """
        Speak text using text-to-speech engine.

        Args:
            text: Text to speak
            console_obj: Optional Rich console instance
        """
        # Use speak_lock to prevent overlapping speech
        with self.speak_lock:
            speak(text, console_obj)

__all__ = ["SpeechManager"]