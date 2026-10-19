"""Thread-safe task and reminder management with background worker."""

import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional
from utils.logger import console, speak
from utils.network import is_online

TASKS_FILE = "tasks.json"
REMINDER_CHECK_INTERVAL = 20

class TaskManager:
    """
    Thread-safe task manager with persistent storage and background reminders.

    This class ensures safe concurrent access to tasks.json through threading locks,
    provides LLM-based natural language parsing for task commands, and runs a
    background worker that checks for reminders at regular intervals.
    """

    def __init__(self, speak_func=None):
        """Initialize task manager and create directories if needed."""
        self.tasks_lock = threading.Lock()
        self.reminder_exit_event = threading.Event()
        self.reminder_thread = None
        self.speak_func = speak_func

    def load_tasks(self) -> Dict[str, List[Dict]]:
        """
        Load tasks from tasks.json file.

        Returns:
            Dictionary mapping list names to task lists
        """
        if not os.path.exists(TASKS_FILE):
            return {}

        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[bold yellow]Warning: Could not load tasks.json: {e}[/bold yellow]")
            return {}

    @staticmethod
    def save_tasks(tasks: Dict[str, List[Dict]]) -> bool:
        """
        Save tasks to tasks.json file.

        Args:
            tasks: Dictionary of task lists to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4)
            return True
        except Exception as e:
            console.print(f"[bold red]Error saving tasks: {e}[/bold red]")
            return False

    @staticmethod
    def parse_task_command(command: str, llm_client) -> Optional[Dict]:
        """
        Parse a natural language task command using Groq LLM.

        Args:
            command: User's natural language task command
            llm_client: GroqLLM instance for JSON extraction

        Returns:
            Dictionary with action, list_name, item, and time, or None if no task commands
        """
        prompt = f"""
Extract task, list, or reminder information from the user's command.
Respond ONLY with a valid JSON object. Do not include markdown blocks like ```json.
Format:
{
    "action": "add" or "read" or "none",
    "list_name": "name of the list (e.g., 'shopping list', 'reminders', 'tasks') - default to 'tasks' if unspecified",
    "item": "description of the task or reminder (null if action is read)",
    "time": "If a time is specified, convert it to 24-hour HH:MM format (e.g. '5 PM' -> '17:00'). If no time, use null."
}
User command: "{command}"
"""

        try:
            completion = llm_client.ask(prompt, max_tokens=200, vision_mode=False)
            if not completion:
                return None

            # Strip markdown if present
            reply = completion.strip()
            if reply.startswith("```json"):
                reply = reply[7:]
            if reply.startswith("```"):
                reply = reply[3:]
            if reply.endswith("```"):
                reply = reply[:-3]

            data = json.loads(reply.strip())
            return data

        except json.JSONDecodeError:
            console.print("[bold yellow]Warning: Could not parse task command response as JSON[/bold yellow]")
            return None
        except Exception as e:
            console.print(f"[bold red]Task Parser Error: {e}[/bold red]")
            return None

    def handle_tasks(self, command: str, llm_client) -> Optional[str]:
        """
        Handle task-related commands (add, read, list).

        Args:
            command: User's natural language task command
            llm_client: GroqLLM instance for parsing

        Returns:
            Notification response or None if no task command
        """
        # Parse command using LLM
        data = self.parse_task_command(command, llm_client)
        if not data:
            return None

        action = data.get("action")
        if action == "none":
            return None

        list_name = data.get("list_name", "tasks").lower()
        item = data.get("item")
        time_str = data.get("time")

        # Thread-safe task database operations
        with self.tasks_lock:
            tasks_db = self.load_tasks()

            if action == "add" and item:
                if list_name not in tasks_db:
                    tasks_db[list_name] = []
                task_entry = {"item": item, "time": time_str, "notified": False}
                tasks_db[list_name].append(task_entry)

                if self.save_tasks(tasks_db):
                    if time_str:
                        return f"I've set a reminder to '{item}' at {time_str}."
                    else:
                        return f"Added '{item}' to your {list_name}."
                else:
                    return f"Sorry, I couldn't save the task."

            elif action == "read":
                if list_name in tasks_db and tasks_db[list_name]:
                    items = []
                    for t in tasks_db[list_name]:
                        if t.get("time"):
                            items.append(f"{t['item']} at {t['time']}")
                        else:
                            items.append(t['item'])

                    task_list_str = ", ".join(items)
                    return f"You have {len(items)} items in your {list_name}: {task_list_str}."
                else:
                    return f"Your {list_name} is currently empty."

        return None

    def start_reminder_worker(self) -> None:
        """Start background reminder worker thread."""
        if self.reminder_thread:
            return

        self.reminder_exit_event.clear()
        self.reminder_thread = threading.Thread(
            target=self._reminder_worker,
            daemon=True,
            name="ReminderWorker"
        )
        self.reminder_thread.start()
        console.print("[dim]Reminder worker started[/dim]")

    def stop_reminder_worker(self) -> None:
        """Stop background reminder worker thread."""
        if self.reminder_thread:
            self.reminder_exit_event.set()
            self.reminder_thread.join(timeout=5)
            self.reminder_thread = None
            console.print("[dim]Reminder worker stopped[/dim]")

    def _reminder_worker(self) -> None:
        """Background worker that checks for due reminders."""
        while not self.reminder_exit_event.is_set():
            try:
                now = datetime.now().strftime("%H:%M")

                # Load tasks under lock
                with self.tasks_lock:
                    tasks_db = self.load_tasks()
                    changed = False

                    for list_name, tasks in tasks_db.items():
                        for t in tasks:
                            if t.get("time") == now and not t.get("notified"):
                                # Speak reminder - do NOT hold tasks_lock during speak()
                                # to avoid deadlock with SpeechManager.speak_lock
                                t["notified"] = True
                                changed = True
                                reminder_text = t['item']

                    if changed and self.save_tasks(tasks_db):
                        console.print("[dim]Reminder saved to tasks.json[/dim]")

                # Speak reminders OUTSIDE the lock
                if changed:
                    try:
                        if self.speak_func:
                            self.speak_func(f"Reminder: {reminder_text}")
                        else:
                            speak(f"Reminder: {reminder_text}")
                    except Exception as e:
                        console.print(f"[dim yellow]Failed to speak reminder: {e}[/dim yellow]")

            except Exception as e:
                # Log error and continue without crashing
                console.print(
                    f"[dim yellow]Reminder worker error: {e}[/dim yellow]"
                )

            # Wait for next check cycle
            self.reminder_exit_event.wait(REMINDER_CHECK_INTERVAL)

__all__ = ["TaskManager"]