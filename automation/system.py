"""System control and automation for Nova AI Assistant."""

import config
import os
import subprocess
import re
import time
import webbrowser
import pyautogui
import urllib.parse
from typing import Optional
from utils.logger import console
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
import psutil

# Enable PyAutoGUI fail-safe explicitly
pyautogui.FAILSAFE = True

class SystemAutomation:
    """
    Handle system-level operations including app management,
    volume controls, system stats, and window actions.
    """

    def open_app(self, app_name: str) -> str:
        """
        Open a supported application.

        Args:
            app_name: Name of the application

        Returns:
            Success message
        """
        app_key = app_name.lower()

        if app_key in config.COMMAND_APPS:
            try:
                config.COMMAND_APPS[app_key]["open"]()
                return f"Opening {app_name}"
            except Exception as e:
                return f"I couldn't open {app_name}."

        # Fallback: try standard Windows applications
        if "calculator" in app_name or "calc" in app_name:
            try:
                subprocess.run(["calc.exe"], shell=True, check=False)
                return "Opening Calculator"
            except Exception:
                return "I couldn't open the Calculator."

        if "notepad" in app_name:
            try:
                subprocess.run(["notepad.exe"], check=False)
                return "Opening Notepad"
            except Exception:
                return "I couldn't open Notepad."

        if "chrome" in app_name or "google chrome" in app_name or "browser" in app_name:
            try:
                subprocess.run(["start", "chrome"], shell=True, check=False)
                return "Opening Chrome"
            except Exception:
                return "I couldn't open Chrome."

        if "cmd" in app_name or "terminal" in app_name or "command prompt" in app_name:
            try:
                subprocess.run(["start", "cmd"], shell=True, check=False)
                return "Opening Command Prompt"
            except Exception:
                return "I couldn't open Command Prompt."

        return f"I don't recognize the application '{app_name}'."

    def close_app(self, app_name: str) -> str:
        """
        Close an open application.

        Args:
            app_name: Name of the application

        Returns:
            Success message
        """
        app_key = app_name.lower()

        if app_key in config.COMMAND_APPS:
            try:
                config.COMMAND_APPS[app_key]["close"]()
                return f"Closing {app_name}"
            except Exception:
                return f"I couldn't close {app_name}."

        # Fallback: try to close common applications
        if "calculator" in app_name:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "Calculator.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "Closing Calculator"
            except Exception:
                return "I couldn't close the Calculator."

        if "notepad" in app_name:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "notepad.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "Closing Notepad"
            except Exception:
                return "I couldn't close Notepad."

        if "chrome" in app_name:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "chrome.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "Closing Chrome"
            except Exception:
                return "I couldn't close Chrome."

        if "cmd" in app_name or "terminal" in app_name:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "cmd.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return "Closing Command Prompt"
            except Exception:
                return "I couldn't close Command Prompt."

        return f"I couldn't find '{app_name}' to close."

    def set_volume(self, level: int) -> str:
        """
        Set system volume level (0-100).

        Args:
            level: Volume level in percentage (0-100)

        Returns:
            Success message
        """
        if level < 0 or level > 100:
            return "Volume level must be between 0 and 100."

        try:
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return f"System volume set to {level} percent."
        except Exception as e:
            console.print(f"[bold red]Volume Error: {e}[/bold red]")
            return "I couldn't change the system volume."

    def toggle_mute(self) -> str:
        """
        Toggle system mute state.

        Returns:
            New mute state message
        """
        try:
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            current_mute = volume.GetMute()
            volume.SetMute(not current_mute, None)
            return "Muted" if not current_mute else "Unmuted"
        except Exception as e:
            console.print(f"[bold red]Volume Error: {e}[/bold red]")
            return "I couldn't toggle mute."

    def take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot of the screen.

        Returns:
            Screenshot file path, or error message/null on failure
        """
        try:
            screenshot_path = "screenshot.png"
            pyautogui.screenshot(screenshot_path)
            return screenshot_path
        except Exception as e:
            console.print(f"[bold red]Screenshot Error: {e}[/bold red]")
            return None

    def display_system_stats(self) -> str:
        """
        Display system health statistics (CPU, RAM, Battery).

        Returns:
            Verbal system status summary
        """
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()

        cpu_status = "STABLE" if cpu_usage < 70 else "HEAVY LOAD"
        ram_usage = memory.percent
        ram_status = "OPTIMAL" if ram_usage < 80 else "CRITICAL"

        # Generate and speak verbal summary
        summary = f"System report initialized. CPU is at {cpu_usage} percent, "
        summary += f"and RAM usage is at {ram_usage} percent. "
        if battery is not None:
            bat_percent = battery.percent
            bat_status = "CHARGING" if battery.power_plugged else "DISCHARGING"
            summary += f" Battery is currently at {bat_percent} percent [{bat_status}]."

        return summary

    def search_and_launch(self, query: str) -> str:
        """
        Open Windows Search and type query to launch application.

        Args:
            query: Search query string

        Returns:
            Message confirming launch attempt
        """
        console.print(
            f"\n[yellow]Windows Search: {query}[/yellow]"
        )
        if not query:
            return "What would you like to search for?"
        pyautogui.press("win")
        time.sleep(0.5)
        pyautogui.write(query, interval=0.1)
        time.sleep(0.7)
        pyautogui.press("enter")
        return f"Attempting to launch {query} from Windows Search."

    def maximize_current_window(self) -> None:
        """Maximize the currently active window."""
        try:
            pyautogui.hotkey("win", "up")
        except Exception:
            pass

__all__ = ["SystemAutomation"]