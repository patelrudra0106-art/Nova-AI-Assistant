"""Messaging automation for WhatsApp and web browser interactions."""

import time
import urllib.parse
import webbrowser
import pyautogui
import config
from typing import Optional
from utils.logger import console
from utils.network import is_online

class MessagingAutomation:
    """
    Handle messaging automation and web browser interactions.

    This class includes:
    - WhatsApp message sending via pywhatkit (for known contacts)
    - WhatsApp Web automation via keyboard controls (for unknown contacts)
    - Web search and URL launching
    """

    def __init__(self, speaker_update_freq: int = 15, whatsapp_search_wait: int = 20):
        """
        Initialize messaging automation.

        Args:
            speaker_update_freq: Seconds to wait before sending messages (pywhatkit)
            whatsapp_search_wait: Seconds to wait for WhatsApp Web page load
        """
        self.speaker_update_freq = speaker_update_freq
        self.whatsapp_search_wait = whatsapp_search_wait

    def send_whatsapp_message(
        self,
        contact: str,
        message: str,
        contacts_dict: dict = None,
        close_browser_after: bool = True
    ) -> Optional[str]:
        """
        Send a WhatsApp message to a contact.

        This function attempts pywhatkit first for known contacts,
        and falls back to automated WhatsApp Web UI navigation.

        Args:
            contact: Contact name or phone number
            message: Message text to send
            contacts_dict: Optional dict mapping contact names to phone numbers
            close_browser_after: Whether to close WhatsApp Web tab after message

        Returns:
            Success message, or error message/null on failure
        """
        if not is_online():
            return "I am currently offline and cannot send WhatsApp messages."

        pywhatkit = __import__("pywhatkit")
        # Use passed contacts_dict if provided, otherwise fall back to config.CONTACTS
        contacts = contacts_dict if contacts_dict is not None else config.CONTACTS
        contact_number = None

        # Try to find contact in provided dict
        if contact in contacts:
            contact_number = contacts[contact]

        # Or extract from contact text if it's a phone number
        if not contact_number:
            digits = ''.join(ch for ch in contact if ch.isdigit())
            if digits:
                # Normalize Indian number format
                if len(digits) == 10:
                    contact_number = f"91{digits}"
                elif len(digits) == 12 and digits.startswith("91"):
                    contact_number = digits

        # Use pywhatkit for known numbers (most reliable)
        if contact_number:
            try:
                console.print(
                    f"\n[yellow]Sending WhatsApp message to {contact} ({contact_number}) "
                    f"using pywhatkit...[/yellow]"
                )
                pywhatkit.sendwhatmsg_instantly(
                    phone_no=f"+{contact_number}",
                    message=message,
                    wait_time=self.speaker_update_freq,
                    tab_close=True,
                    close_time=3
                )

                if close_browser_after:
                    console.print("[dim]WhatsApp tab will close automatically[/dim]")

                return f"Initiating WhatsApp automation for {contact}."

            except Exception as e:
                console.print(f"[bold red]WhatsApp (pywhatkit) Error: {e}[/bold red]")
                # Fall through to WhatsApp Web for manual search

        # Use WhatsApp Web automation for unknown contacts
        console.print(
            f"[bold yellow]Contact '{contact}' not in list. "
            f"Switching to manual WhatsApp Web workflow...[/bold yellow]"
        )

        try:
            # Open WhatsApp Web
            webbrowser.open("https://web.whatsapp.com")
            time.sleep(self.speaker_update_freq)

            # Maximize window
            pyautogui.hotkey("win", "up")
            time.sleep(5)  # Wait for page load

            # Focus search bar and enter contact name
            for _ in range(2):  # Retry search shortcut pattern if needed
                pyautogui.hotkey("ctrl", "alt", "/")
                time.sleep(1)
                pyautogui.press("esc")
                time.sleep(0.5)

            pyautogui.write(contact, interval=0.1)
            time.sleep(3)

            # Focus message field and send
            pyautogui.press("enter")
            time.sleep(2)

            for _ in range(3):  # Try different patterns for message line
                pyautogui.write(message, interval=0.1)
                pyautogui.press("enter")
                time.sleep(1)

            console.print(f"[bold green]WhatsApp automation for {contact} finished successfully![/bold green]")
            return f"Initiated WhatsApp Web automation for {contact}."

        except Exception as e:
            console.print(f"[bold red]WhatsApp Web automation failed: {e}[/bold red]")
            return f"Sorry, I couldn't send the WhatsApp message to {contact}."

    def search_web(self, query: str, engine: str = "google") -> Optional[str]:
        """
        Perform a web search and open results.

        Args:
            query: Search query string
            engine: Search engine to use (google, youtube, etc.)

        Returns:
            Success message, or error message on failure
        """
        if not query:
            return "What would you like me to search for?"

        if engine == "google":
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}"
            webbrowser.open(url)
            return f"Searching Google for {query}"

        elif engine == "youtube":
            encoded = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}"

        else:
            # Default: open in default browser
            webbrowser.open(query)
            return f"Opening {query}"

    def launch_url(self, url: str) -> Optional[str]:
        """
        Open a URL in the default browser.

        Args:
            url: Website URL to open

        Returns:
            Success message, or error message on failure
        """
        if not url:
            return "Which URL should I open?"

        if not "http" in url.lower() and not "www" in url.lower():
            url = "https://" + url

        try:
            webbrowser.open(url)
            return f"Opening {url}"
        except Exception as e:
            return f"I couldn't open {url}"

    def open_youtube(self) -> str:
        """Open YouTube in the default browser."""
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    def open_google(self) -> str:
        """Open Google in the default browser."""
        webbrowser.open("https://google.com")
        return "Opening Google"

    def open_chatgpt(self) -> str:
        """Open ChatGPT in the default browser."""
        webbrowser.open("https://chatgpt.com")
        return "Opening ChatGPT"

__all__ = ["MessagingAutomation"]