"""Configuration management and environment validation for Nova AI Assistant."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-90b-vision-preview"  # Verified working vision model on Groq

# API Key Validation (runtime, not import-time)
def validate_api_key() -> None:
    """Validate Groq API key is present."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found in environment variables. "
            "Please set it in the .env file."
        )

# Personal & System Configuration
DEFAULT_CITY = "surat"
CREATOR_NAME = "Rudra Patel"

# Contact Numbers - Load from environment with fallback
def _load_contacts() -> dict:
    """Load contacts from environment variable or use defaults."""
    contacts_env = os.getenv("NOVA_CONTACTS")
    if contacts_env:
        try:
            import json
            return json.loads(contacts_env)
        except json.JSONDecodeError:
            pass
    # Default contacts (can be overridden by NOVA_CONTACTS env var)
    return {
        "mummy": "9664794881",
        "papa": "9123456789",
        "bhai": "8735045208",
    }

CONTACTS = _load_contacts()

# App Commands Dictionary - using subprocess.run instead of os.system
import subprocess

COMMAND_APPS = {
    "notepad": {
        "open": lambda: subprocess.run(
            ["notepad.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        "close": lambda: subprocess.run(
            ["taskkill", "/F", "/IM", "notepad.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        "keywords": ["notepad", "notes"],
    },
    "calculator": {
        "open": lambda: subprocess.run(["calc.exe"], shell=True),
        "close": lambda: subprocess.run(
            ["taskkill", "/F", "/IM", "Calculator.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        "keywords": ["calculator", "calc"],
    },
    "chrome": {
        "open": lambda: subprocess.run(["start", "chrome"], shell=True),
        "close": lambda: subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        "keywords": ["chrome", "browser", "google chrome"],
    },
    "command prompt": {
        "open": lambda: subprocess.run(["start", "cmd"], shell=True),
        "close": lambda: subprocess.run(
            ["taskkill", "/F", "/IM", "cmd.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        "keywords": ["cmd", "terminal", "command prompt"],
    },
}

# System Commands Dictionary
SYSTEM_COMMANDS = {
    "restart system": lambda: subprocess.run(["shutdown", "/r", "/t", "0"]),
    "shutdown system": lambda: subprocess.run(["shutdown", "/s", "/t", "0"]),
    "mute": lambda: __import__("pyautogui").press("volumemute"),
    "screenshot": lambda: __import__("pyautogui").screenshot("screenshot.png"),
}

# WhatsApp Automation Settings
WHATSAPP_SHORTCUT = "ctrl+alt,/"
WHATSAPP_SEARCH_WAIT = 20
WHATSAPP_PAGE_LOAD_DELAY = 5

# Vision Settings
VISION_SCREENSHOT_PATH = "temp_vision.png"
VISION_SCANSHOT_DELETE = True

# Task / Reminder Settings
TASKS_FILE = "tasks.json"
REMINDER_CHECK_INTERVAL = 20

# Wake Words
WAKE_WORDS = [
    "hello nova",
    "wake up nova",
    "hey nova",
    "hi nova",
    "ok nova",
    "nova",
    "no va",
    "know va",
    "lenova",
]

# Listening Settings
LISTEN_PAUSE_THRESHOLD = 1.5
LISTEN_ENERGY_THRESHOLD = 300

# Offline Behavior
OFFLINE_TIMEOUT = 3

# Network timeouts
REQUEST_TIMEOUT = 10  # seconds for HTTP requests
SOCKET_TIMEOUT = 3    # seconds for connectivity check