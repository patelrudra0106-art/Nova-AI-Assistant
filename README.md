# Nova AI Assistant

A voice-controlled personal assistant for **Windows**. Nova listens for a wake word, understands what you say, and either runs a local action (open apps, control volume, send WhatsApp messages, manage reminders) or hands the request to a large language model on the [Groq](https://groq.com) cloud API.

Created by **Rudra Patel**.

---

## Features

- **Wake-word activation.** Say "Hey Nova", "OK Nova", or just "Nova" to start a session. Say "stop", "sleep", or "goodbye" to put it back to sleep.
- **Conversational AI.** Anything Nova doesn't handle locally goes to `llama-3.3-70b-versatile` on Groq. It keeps a short sliding window of chat history.
- **Screen understanding.** Ask "what do you see" or "describe my screen" and Nova takes a screenshot and sends it to a vision model.
- **App control.** Open and close Notepad, Calculator, Chrome, and Command Prompt, or launch any app through Windows Search.
- **System control.** Set the volume to a level, mute or unmute, shut down or restart, and read a CPU, RAM, and battery report.
- **Media keys.** Play or pause, skip, and go back to the previous track.
- **WhatsApp messaging.** Send a message to a saved contact or to a raw phone number, with a WhatsApp Web fallback for unknown contacts.
- **Tasks and reminders.** Keep lists such as "shopping" or "tasks", add items, read them back, and set time-based reminders that Nova speaks aloud. A background thread checks for due reminders.
- **Information.** Get the time, date, weather (via wttr.in), BBC news headlines (summarised by the LLM), and jokes (via pyjokes).
- **Web search.** Search Google or YouTube by voice.
- **Timers.** "Set a timer for 5 minutes" starts a background timer that speaks when it finishes.

---

## Requirements

- Windows 10 or 11. Several features depend on Windows-only tools: `taskkill`, `calc.exe`, `ms-clock:`, `shutdown`, `pycaw` for volume control, and the Windows key for search.
- Python 3.11 (the bundled bytecode was built with 3.11).
- A working microphone and speakers.
- An internet connection for speech recognition (Google's free speech API), the LLM, and weather/news.
- A free Groq API key from [console.groq.com](https://console.groq.com).

---

## Installation

1. **Clone or extract the project.**

   ```bash
   cd "Ai assistant"
   ```

2. **Create and activate a virtual environment (recommended).**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install the dependencies.**

   ```bash
   pip install groq python-dotenv SpeechRecognition pyaudio pyttsx3 pyautogui pyjokes rich pycaw psutil pywhatkit requests
   ```

   > **Note:** `pyaudio` is needed by `SpeechRecognition` to access the microphone. If `pip install pyaudio` fails on Windows, install a prebuilt wheel that matches your Python version, or run `pip install pipwin` followed by `pipwin install pyaudio`.

4. **Create a `.env` file** in the project root:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

   Optionally, set your own contacts for WhatsApp (see [Configuration](#configuration)).

5. **Run Nova.**

   ```bash
   python Assistant.py
   ```

   On start-up, Nova calibrates for ambient noise. Stay quiet for about a second while it does this.

---

## Usage

Once Nova says it is online, use the wake word and then speak your command.

| What you say | What happens |
|---|---|
| "Hey Nova" | Activates Nova. It replies "How can I help?" |
| "Open notepad" / "Close chrome" | Opens or closes a supported app |
| "Open spotify" | Searches Windows for the app and launches it |
| "Set volume to 40" / "Mute" / "Max volume" | Controls system audio |
| "System report" / "Status" | Reads CPU, RAM, and battery levels |
| "Play music" / "Next track" / "Previous track" | Sends media key presses |
| "Remind me to call mom at 6 PM" | Saves a timed reminder |
| "Add eggs to my shopping list" | Adds an item to a list |
| "Read my shopping list" | Reads a list aloud |
| "Message mummy saying I'll be late" | Sends a WhatsApp message |
| "Search Google for python dataclasses" | Opens a Google search |
| "Search YouTube for lo-fi beats" | Opens a YouTube search |
| "Weather in Mumbai" | Reads the current weather |
| "What's the news" | Summarises BBC headlines |
| "Set a timer for 10 minutes" | Starts a timer |
| "What do you see on my screen" | Analyses a screenshot |
| "Tell me a joke" | Tells a joke |
| "Who are you" | Nova introduces itself |
| "Stop" / "Go to sleep" | Puts Nova back into standby |
| "Exit" / "Quit" | Shuts Nova down |

Anything not matched by a rule is sent to the LLM as a free-form question.

---

## Configuration

Settings live in `config.py`.

| Setting | Purpose |
|---|---|
| `CHAT_MODEL` | Groq model used for chat (default `llama-3.3-70b-versatile`) |
| `VISION_MODEL` | Groq model used for screen analysis |
| `DEFAULT_CITY` | City used when a weather request doesn't name one |
| `CONTACTS` | Name-to-number map for WhatsApp |
| `COMMAND_APPS` | Apps that can be opened and closed, with their trigger keywords |
| `SYSTEM_COMMANDS` | Standalone commands such as shutdown or restart |
| `WAKE_WORDS` | Phrases that activate Nova |
| `LISTEN_PAUSE_THRESHOLD` / `LISTEN_ENERGY_THRESHOLD` | Microphone sensitivity |
| `REMINDER_CHECK_INTERVAL` | How often (in seconds) reminders are checked |
| `REQUEST_TIMEOUT` | HTTP timeout for weather and news |

### Setting your contacts without editing code

Set the `NOVA_CONTACTS` environment variable (or add it to `.env`) as a JSON object:

```env
NOVA_CONTACTS={"mummy": "9876543210", "bhai": "9123456789"}
```

If this variable is missing or invalid, Nova falls back to the defaults in `config.py`.

---

## Project Structure

```
Ai assistant/
├── Assistant.py          # Entry point: wake-word loop and command router
├── config.py             # All settings, contacts, app and system commands
├── core/
│   ├── llm.py            # GroqLLM: chat and vision calls, sliding-window history
│   ├── speech.py         # SpeechManager: microphone input and thread-safe TTS
│   └── tasks.py          # TaskManager: tasks, reminders, background worker
├── automation/
│   ├── system.py         # SystemAutomation: apps, volume, stats, Windows Search
│   └── messaging.py      # MessagingAutomation: WhatsApp, web search, URLs
└── utils/
    ├── logger.py         # Rich console output and pyttsx3 text-to-speech
    └── network.py        # Internet connectivity check
```

Tasks and reminders are stored in `tasks.json`, which is created automatically in the working directory.

---

## How It Works

1. **Listen.** `SpeechManager` records from the microphone and transcribes it with Google's speech recognition.
2. **Wake.** `Assistant.py` checks the text for a wake word. Once Nova is active, the next utterance is treated as a command.
3. **Route.** `handle_command()` checks the text against rules in this order: exit, jokes, introductions, vision, apps, system commands, volume, system stats, tasks, launch, WhatsApp, news, YouTube, Google, time and date, weather, timer, media keys. If nothing matches, the text goes to the LLM.
4. **Respond.** The reply is printed in a Rich panel and spoken with pyttsx3.

A background `ReminderWorker` thread wakes every `REMINDER_CHECK_INTERVAL` seconds, checks `tasks.json` for reminders that are due, and speaks them.

---

## Security Notes

- **Never commit your `.env` file.** `.gitignore` already excludes it, but if your API key has ever been shared or committed, **revoke it in the Groq console and create a new one.**
- `tasks.json`, `screenshot.png`, and `temp_vision.png` are excluded from Git.
- Nova can shut down or restart your computer and can send messages on your behalf. Be careful with the wake-word listener when others are nearby.
- Screen analysis sends a screenshot of your display to the Groq API. Don't use it while sensitive content is on screen.

---

## Known Limitations

- **Windows only.** Many commands rely on Windows executables and APIs.
- **Speech recognition needs internet access.** The offline fallback is a typed prompt, which only appears when the speech service is unreachable.
- **WhatsApp automation is fragile.** It depends on keyboard shortcuts and fixed delays, so it may fail on slow machines or when WhatsApp Web's layout changes.
- **Keyword matching is simple.** Some phrases may route to the wrong handler, for example a sentence that contains "time" but is really a question about something else.
- **No `requirements.txt` yet.** Use the install command in [Installation](#installation) until one is added.

---

## Roadmap Ideas

- Add a `requirements.txt` and a `.env.example` file.
- Replace keyword routing with LLM-based intent detection.
- Add a confirmation step before shutdown or restart.
- Support more apps through a config-driven registry.
- Add a wake-word engine that works offline.

---
## Author

**Rudra Patel**
