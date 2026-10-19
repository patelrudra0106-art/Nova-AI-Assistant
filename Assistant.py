#!/usr/bin/env python
"""
Nova AI Assistant - A voice-controlled personal assistant for Windows

Main program that integrates speech recognition, LLM capabilities, system controls,
tasks management, and automation features.

Author: Rudra Patel
"""

import datetime
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import base64
import pyautogui
import pyjokes

# Import default configuration and modules
from config import (
    GROQ_API_KEY,
    CHAT_MODEL,
    VISION_MODEL,
    DEFAULT_CITY,
    CREATOR_NAME,
    CONTACTS,
    COMMAND_APPS,
    SYSTEM_COMMANDS,
    WHATSAPP_SHORTCUT,
    WHATSAPP_SEARCH_WAIT,
    VISION_SCREENSHOT_PATH,
    VISION_SCANSHOT_DELETE,
    TASKS_FILE,
    REMINDER_CHECK_INTERVAL,
    WAKE_WORDS,
    LISTEN_PAUSE_THRESHOLD,
    LISTEN_ENERGY_THRESHOLD,
    OFFLINE_TIMEOUT,
    validate_api_key,
    REQUEST_TIMEOUT,
)

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import box

from utils.logger import console, speak
from utils.network import is_online
import speech_recognition as sr

from core.speech import SpeechManager
from core.llm import GroqLLM
from core.tasks import TaskManager

from automation.system import SystemAutomation
from automation.messaging import MessagingAutomation


def handle_command(command: str, llm_client: GroqLLM, voice_manager: SpeechManager,
                   task_manager: TaskManager, system_automation: SystemAutomation,
                   messaging_automation: MessagingAutomation) -> str:
    """
    Handle a single voice command using all available modules.

    Args:
        command: The user's command string
        llm_client: GroqLLM instance for AI responses
        voice_manager: SpeechManager for audio input/output
        task_manager: TaskManager for persistent tasks/reminders
        system_automation: SystemAutomation instance for system controls
        messaging_automation: MessagingAutomation instance for MBT

    Returns:
        Response text to speak back to user
    """
    command_lower = command.lower()

    # Exit commands
    if "exit" in command_lower or "quit" in command_lower:
        speak("Goodbye!")
        sys.exit(0)

    # PyJokes Integration
    if "joke" in command_lower:
        try:
            return pyjokes.get_joke()
        except Exception as e:
            console.print(f"[dim yellow]Local joke API warning: {e}[/dim yellow]")
            return "Why don't scientists trust atoms? Because they make up everything!"

    # Greeting/introduction commands
    intro_triggers = [
        "who are you",
        "what's your name",
        "introduce yourself",
        "about yourself",
        "tell me about you"
    ]
    if any(trigger in command_lower for trigger in intro_triggers):
        return llm_client.ask(
            f"Give a fresh, creative, and unique introduction of yourself as Nova. "
            f"Ensure you mention your creators ({CREATOR_NAME}) and your role as a helpful assistant. "
            f"Be concise but different every time!"
        )

    # Vision commands
    vision_keywords = [
        "on my screen",
        "look at my screen",
        "what do you see",
        "read my screen",
        "summarize my screen",
        "describe my screen"
    ]
    if any(vk in command_lower for vk in vision_keywords):
        speak("Analyzing your screen. Please wait.")
        screenshot_path = VISION_SCREENSHOT_PATH
        try:
            pyautogui.screenshot(screenshot_path)

            # Strip vision keywords from prompt
            vision_prompt = command_lower
            for vk in vision_keywords:
                vision_prompt = vision_prompt.replace(vk, "")
            vision_prompt = vision_prompt.strip()

            # Provide minimal prompt if none given
            if not vision_prompt or any(w in vision_prompt for w in ["what is", "can you", "please", "tell me"]):
                vision_prompt = "Briefly describe the main contents of this screen."

            response = llm_client.ask_vision(vision_prompt)
            return response

        except Exception as e:
            return f"I couldn't process the screen analysis due to an error: {e}"
        finally:
            # Clean up temporary screenshot reliably
            if VISION_SCANSHOT_DELETE and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                except Exception as cleanup_err:
                    console.print(f"[dim red]Failed to delete temp vision file: {cleanup_err}[/dim red]")

    # App commands - open/close via SystemAutomation
    for app_name, actions in COMMAND_APPS.items():
        if any(kw in command_lower for kw in actions["keywords"]):
            # Check for close intent
            if any(close_kw in command_lower for close_kw in ["close", "stop", "exit", "kill", "terminate", "quit"]):
                return system_automation.close_app(app_name)
            # Default open application
            else:
                return system_automation.open_app(app_name)

    # Standalone system commands
    for cmd_key in SYSTEM_COMMANDS.keys():
        if cmd_key in command_lower:
            try:
                SYSTEM_COMMANDS[cmd_key]()
                return f"Executing {cmd_key}"
            except Exception as e:
                return f"Sorry, I couldn't execute {cmd_key}."

    # Volume control
    if "volume" in command_lower or "sound" in command_lower or "mute" in command_lower:
        # Extract numbers from command
        numbers = re.findall(r'\d+', command_lower)
        if numbers:
            level = int(numbers[0])
            if 0 <= level <= 100:
                return system_automation.set_volume(level)

        # Mute checks (without numbers)
        if "mute" in command_lower:
            return system_automation.toggle_mute()

        if "max" in command_lower or "full" in command_lower or "highest" in command_lower:
            return system_automation.set_volume(100)

    # System health
    if any(k in command_lower for k in ["status", "health", "report", "performance", "system report"]):
        return system_automation.display_system_stats()

    # Tasks and reminders
    task_keywords = ["remind", "task", "list", "todo", "to do", "shopping", "agenda"]
    if any(k in command_lower for k in task_keywords):
        task_response = task_manager.handle_tasks(command_lower, llm_client)
        if task_response:
            return task_response

    # Universal search and launch
    launch_keywords = ["open", "launch", "start", "run", "search for", "open in"]
    if any(lk in command_lower for lk in launch_keywords):
        target = command_lower
        for lk in launch_keywords:
            target = target.replace(lk, "")
        target = target.strip()

        if target:
            result = system_automation.search_and_launch(target)
            if "Windows Search" in result:
                speak(result)
            return result

    # WhatsApp messaging
    if (
        "whatsapp" in command_lower
        or command_lower.startswith("message ")
        or command_lower.startswith("send message ")
        or command_lower.startswith("send a message ")
    ):
        contact = ""
        msg = ""

        # Parse contact and message
        prefixes = [
            "send a whatsapp message to",
            "send whatsapp message to",
            "send whatsapp to",
            "send a whatsapp message",
            "send whatsapp message",
            "send message to",
            "send a message to",
            "send message",
            "message",
            "whatsapp",
            "to",
        ]

        text = command_lower.strip()
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        separators = [" saying ", " that ", " text ", " msg "]
        for sep in separators:
            if sep in text:
                left, right = text.split(sep, 1)
                contact = left.strip()
                msg = right.strip()
                break

        # Fallback: first token is contact, rest is message
        if not msg and text:
            parts = text.split(maxsplit=1)
            if len(parts) == 2:
                contact, msg = parts[0].strip(), parts[1].strip()
            else:
                contact = parts[0].strip()

        # Collect contact numbers
        contacts_dict = {**CONTACTS}

        # If contact not in saved contacts and message empty, ask for both
        if not contact or not msg:
            speak("Who would you like to message?")
            contact = voice_manager.listen().lower()
            if not contact:
                return "Cancelled."

        # If message still empty, ask for message
        if not msg:
            speak("What is the message?")
            msg = voice_manager.listen()
            if not msg:
                return "Cancelled."

        # Send message
        try:
            result = messaging_automation.send_whatsapp_message(
                contact=contact,
                message=msg,
                contacts_dict=contacts_dict
            )
            speak(result) if result else None
            return result
        except Exception as e:
            speak(f"I couldn't send the WhatsApp message: {e}")
            return f"Sorry, I couldn't send the WhatsApp message to {contact}."

    # News
    if "news" in command_lower:
        try:
            import requests
            from xml.etree import ElementTree as ET

            res = requests.get("http://feeds.bbci.co.uk/news/rss.xml", timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                headlines = [
                    item.find('title').text
                    for item in root.findall('./channel/item')
                ][:4]
                news_text = "Headlines: " + ". ".join(headlines)
                return llm_client.ask(
                    f"Summarize these news headlines playfully in 2 sentences. "
                    f"Give a direct response without any conversational filler: {news_text}",
                    max_tokens=256
                )
            else:
                return "I couldn't fetch the latest news at the moment."
        except Exception as e:
            console.print(f"[dim yellow]News fetch warning: {e}[/dim yellow]")
            return "I couldn't fetch the latest news."

    # YouTube
    if "youtube" in command_lower:
        query = command_lower.replace("youtube", "").replace("search", "").strip()
        if query:
            result = messaging_automation.search_web(query, engine="youtube")
            if result:
                speak(result)
            return result
        else:
            return messaging_automation.open_youtube()

    # Google
    if "google" in command_lower:
        query = command_lower.replace("google", "").replace("search", "").strip()
        if query:
            result = messaging_automation.search_web(query, engine="google")
            if result:
                speak(result)
            return result
        else:
            return messaging_automation.open_google()

    # Open specific services
    if "open youtube" in command_lower:
        return messaging_automation.open_youtube()

    elif "open google" in command_lower:
        return messaging_automation.open_google()

    elif "open ai" in command_lower or "open chatgpt" in command_lower:
        return messaging_automation.open_chatgpt()

    # Clock
    if "clock" in command_lower:
        # Windows Clock app
        for win_exe in ["ms-clock:", "clock.exe", "clock-w64.exe"]:
            try:
                subprocess.Popen(win_exe, shell=True)
                return "Opening Clock"
            except:
                continue
        return "I couldn't open the Clock app."

    # Time
    if "time" in command_lower:
        now = datetime.datetime.now()
        return now.strftime("%I:%M %p")

    # Date
    if "date" in command_lower:
        now = datetime.datetime.now()
        return now.strftime("%A, %d %B %Y")

    # Weather
    if "weather" in command_lower:
        city = command_lower.replace("weather", "").replace("in", "").strip()
        if not city:
            city = DEFAULT_CITY

        try:
            import requests

            # Get weather via wttr.in
            res = requests.get(f"https://wttr.in/{city}?format=3", timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                weather_text = res.text.strip()
                return f"The current weather in {city} is: {weather_text}"
            else:
                return f"I couldn't fetch weather for {city} right now."
        except Exception as e:
            console.print(f"[dim yellow]Weather fetch warning: {e}[/dim yellow]")
            return "I couldn't fetch the weather at the moment."

    # Timer
    if "timer" in command_lower:
        words = command_lower.split()
        duration = 0
        for word in words:
            if word.isdigit():
                duration = int(word)
                if "minute" in command_lower or "minutes" in command_lower:
                    duration *= 60
                elif "hour" in command_lower or "hours" in command_lower:
                    duration *= 3600
                break

        if duration > 0:
            def timer_done():
                voice_manager.speak_from_text("Your timer is up!")

            t = threading.Timer(duration, timer_done)
            t.daemon = True
            t.start()
            return f"Timer started for {duration} seconds."
        else:
            return "I didn't catch the duration for the timer."

    # Media controls
    if "play music" in command_lower or "pause music" in command_lower:
        try:
            pyautogui.press("playpause")
            return "Toggling playback."
        except Exception:
            return "I couldn't toggle media playback."

    if "next track" in command_lower or "skip song" in command_lower:
        try:
            pyautogui.press("nexttrack")
            return "Skipping to the next track."
        except Exception:
            return "I couldn't skip the track."

    if "previous track" in command_lower or "back" in command_lower:
        try:
            pyautogui.press("prevtrack")
            return "Going back."
        except Exception:
            return "I couldn't go back."

    # Groq fallback for any other command
    return llm_client.ask(command_lower)


def main():
    """
    Main program execution flow.
    """
    # Start up: Validate API Key
    try:
        validate_api_key()
    except ValueError as val_err:
        console.print(f"[bold red]Configuration Error: {val_err}[/bold red]")
        sys.exit(1)

    # Initialize system components
    voice_manager = SpeechManager(
        pause_threshold=LISTEN_PAUSE_THRESHOLD,
        energy_threshold=LISTEN_ENERGY_THRESHOLD
    )

    llm_client = GroqLLM(
        api_key=GROQ_API_KEY,
        chat_model=CHAT_MODEL
    )

    task_manager = TaskManager(speak_func=voice_manager.speak_from_text)
    system_automation = SystemAutomation()
    messaging_automation = MessagingAutomation()

    # Start reminder worker thread
    task_manager.start_reminder_worker()

    # --- BOOT SEQUENCE ---
    console.print(Rule(style="bold blue"))
    console.print(
        Panel(
            Text("N O V A   A I   C O R E", justify="center", style="bold cyan"),
            border_style="blue"
        )
    )

    with console.status("[bold blue]Initialising Core Modules...", spinner="earth") as status:
        time.sleep(0.5)
        status.update("[bold blue]Neural Link Establishing...", spinner="earth")
        time.sleep(0.5)
        status.update("[bold blue]Calibrating Ambient Noise... (Please be quiet)", spinner="earth")
        with sr.Microphone() as source:
            recognizer = sr.Recognizer()
            recognizer.adjust_for_ambient_noise(source, duration=1)
        status.update("[bold green]System Ready. Calibration Complete.", spinner="earth")
        time.sleep(0.5)

    console.print(Rule(style="bold green"))
    console.print("[bold cyan]NOVA IS ONLINE[/bold cyan]")
    console.print()

    # Welcome message
    wake_greeting = "Hello! I'm Nova. How can I assist you today?"
    console.print(Panel(wake_greeting, title="[bold cyan]Nova[/bold cyan]", box=box.DOUBLE))
    speak(wake_greeting)

    # Main listening loop
    active_mode = False

    try:
        while True:
            # Primary listening for wake words or commands
            text = voice_manager.listen(timeout=None, phrase_time_limit=None)

            if not text:
                continue

            # Handle wake words
            if any(wake in text for wake in WAKE_WORDS):
                if not active_mode:
                    active_mode = True
                    speak("How can I help?")
                    continue
                else:
                    # Already active, just extract command
                    command = text
                    for wake in WAKE_WORDS:
                        command = command.replace(wake, "")
                    command = command.strip()
                    if not command:
                        continue

            if active_mode:
                command = text
                # Strip wake words
                for wake in WAKE_WORDS:
                    command = command.replace(wake, "")
                command = command.strip()

                if not command:
                    continue

                # Sleep/exit command
                if any(sleep in command for sleep in ["stop", "go to sleep", "goodbye", "sleep", "shut down"]):
                    active_mode = False
                    speak("Going to sleep. Just say my name if you need me.")
                    continue

                # Process command through all modules
                result = handle_command(
                    command,
                    llm_client,
                    voice_manager,
                    task_manager,
                    system_automation,
                    messaging_automation
                )

                if result:
                    speak(result)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping Nova...[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error: {e}[/bold red]")
    finally:
        # Cleanup on exit
        task_manager.stop_reminder_worker()
        console.print("[bold cyan]Nova has stopped.[/bold cyan]")


if __name__ == "__main__":
    main()