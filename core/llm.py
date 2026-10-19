"""Groq LLM integration with thread-safe chat history management."""

from groq import Groq
from typing import List, Dict, Optional
from utils.network import is_online
from utils.logger import console, speak
import threading

class GroqLLM:
    """
    Thread-safe LLM integration with Groq Cloud API.

    This class manages chat history with thread locking to prevent race conditions.
    """

    def __init__(self, api_key: str, chat_model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq LLM client.

        Args:
            api_key: Groq API authentication key
            chat_model: Model ID for chat completions
        """
        self.client = Groq(api_key=api_key)
        self.chat_model = chat_model
        self.chat_history_lock = threading.Lock()
        self._initialize_history()

    def _initialize_history(self) -> None:
        """Initialize chat history with system prompt."""
        self.chat_history = [
            {
                "role": "system",
                "content": (
                    "You are Nova, a clever, helpful assistant. "
                    "You were created by Rudra Patel. Never refer to yourself as an AI, "
                    "a robot, or a language model. Keep your personality warm and conversational."
                )
            }
        ]

    def ask(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        vision_mode: bool = False
    ) -> Optional[str]:
        """
        Send a prompt to Groq API and get a response.

        Args:
            prompt: User prompt text
            max_tokens: Maximum tokens in response
            temperature: Creativity factor (0-2)
            vision_mode: Whether this is a vision/image analysis request

        Returns:
            AI response text, or None if offline or error occurs
        """
        # Check connectivity first
        if not is_online():
            speak(
                "I am currently in offline mode. "
                "I can run local applications and system commands, "
                "but I cannot connect to the neural net for complex queries right now."
            )
            return None

        try:
            # Use vision model if enabled
            model = self.chat_model
            if vision_mode:
                model = "llama-3.2-90b-vision-preview"  # Verified working vision model

            # Thread-safe request to update Chat history
            with self.chat_history_lock:
                self.chat_history.append({"role": "user", "content": prompt})

                # Maintain sliding window
                if len(self.chat_history) > 11:
                    self.chat_history = [self.chat_history[0]] + self.chat_history[-10:]

                completion = self.client.chat.completions.create(
                    model=model,
                    messages=self.chat_history,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                reply = completion.choices[0].message.content
                self.chat_history.append({"role": "assistant", "content": reply})
                return reply

        except Exception as e:
            console.print(f"[bold red]Neural Link Error: {e}[/bold red]")
            speak("I'm having a bit of trouble connecting to my thoughts right now.")
            return None

    def ask_vision(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        top_p: float = 1.0
    ) -> Optional[str]:
        """
        Send a vision/image prompt to Groq API.

        Args:
            prompt: Text description or analysis request
            max_tokens: Maximum tokens in response
            temperature: Creativity factor
            top_p: Nucleus sampling parameter

        Returns:
            AI response text, or None if offline or error occurs
        """
        if not is_online():
            speak(
                "I am currently in offline mode and cannot process "
                "visual data right now."
            )
            return None

        try:
            # Note: Groq vision requires image_url in content, not just text
            # This is a text-only vision query (for screen analysis with base64 image)
            completion = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content

        except Exception as e:
            console.print(f"[bold red]Vision Link Error: {e}[/bold red]")
            speak("I'm having a bit of trouble analyzing the visual data right now.")
            return None

__all__ = ["GroqLLM"]