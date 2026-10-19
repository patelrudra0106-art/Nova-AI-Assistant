"""Network connectivity utilities for Nova AI Assistant."""

import socket
from typing import Optional
import config

DEFAULT_HOST = "8.8.8.8"
DEFAULT_PORT = 53

def is_online(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: int = config.SOCKET_TIMEOUT
) -> bool:
    """
    Check if the system has internet connectivity.

    Args:
        host: Hostname or IP address to ping
        port: Network port to connect to
        timeout: Connection timeout in seconds

    Returns:
        True if online, False otherwise
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, socket.timeout, OSError):
        return False
    except Exception:
        return False

__all__ = ["is_online"]