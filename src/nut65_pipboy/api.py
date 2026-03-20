"""pywebview JS-Python bridge — PipboyAPI class.

All methods are called from JavaScript threads. Parameters are validated
on the Python side (never trust JS values).
"""

from __future__ import annotations

import logging
import re
import threading
from typing import TYPE_CHECKING

from nut65_pipboy.types import AppMode

if TYPE_CHECKING:
    import webview

    from nut65_pipboy.controller import GameController

log = logging.getLogger(__name__)

MAX_MARQUEE_LENGTH = 64
ALLOWED_CHARS = re.compile(r"^[A-Z0-9 !?.,:;\-/%()\[\]]+$")


class PipboyAPI:
    """Exposed to JS via pywebview's js_api parameter."""

    def __init__(
        self,
        controller: GameController,
        state_relay: StateRelay,
    ) -> None:
        self._controller = controller
        self._relay = state_relay
        self._window: webview.Window | None = None
        self._ready = threading.Event()

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def client_ready(self) -> dict:
        """JS signals that DOM is initialized and ready for data."""
        self._ready.set()
        log.info("Frontend client ready")
        return {"status": "ok"}

    def wait_for_client(self, timeout: float = 15.0) -> bool:
        return self._ready.wait(timeout)

    def get_state(self) -> dict | None:
        """Pull-based: returns latest state or None if no new data."""
        return self._relay.consume()

    def set_mode(self, mode: str) -> dict:
        if not isinstance(mode, str):
            return {"error": "mode must be a string"}
        valid = [m.value for m in AppMode]
        if mode not in valid:
            return {"error": f"mode must be one of {valid}"}
        self._controller.set_mode(mode)
        return {"status": "ok", "mode": mode}

    def set_speed(self, value: int | str | float) -> dict:
        try:
            v = int(value)
        except (TypeError, ValueError):
            return {"error": "speed must be an integer"}
        if not (1 <= v <= 10):
            return {"error": "speed must be 1-10"}
        self._controller.set_speed(v)
        return {"status": "ok", "speed": v}

    def set_marquee_text(self, text: str) -> dict:
        if not isinstance(text, str):
            return {"error": "text must be a string"}
        text = text.upper().strip()
        if len(text) > MAX_MARQUEE_LENGTH:
            return {"error": f"text exceeds {MAX_MARQUEE_LENGTH} characters"}
        if text and not ALLOWED_CHARS.match(text):
            return {"error": "text contains unsupported characters"}
        self._controller.set_marquee_text(text)
        return {"status": "ok"}

    def set_hue(self, hue: int | str | float) -> dict:
        try:
            h = int(hue)
        except (TypeError, ValueError):
            return {"error": "hue must be an integer"}
        self._controller.set_hue(h)
        return {"status": "ok"}

    def set_marquee_mode(self, mode: str) -> dict:
        if mode not in ("custom", "system"):
            return {"error": "mode must be 'custom' or 'system'"}
        self._controller.set_marquee_mode(mode)
        return {"status": "ok"}

    def toggle_fullscreen(self) -> dict:
        if self._window:
            self._window.toggle_fullscreen()
        return {"status": "ok"}


class StateRelay:
    """Thread-safe state relay between game loop and frontend.

    publish() overwrites, consume() returns latest without clearing.
    This way JS can poll at any rate without missing frames.
    """

    def __init__(self) -> None:
        self._state: dict | None = None
        self._lock = threading.Lock()

    def publish(self, state: dict) -> None:
        with self._lock:
            self._state = state

    def consume(self) -> dict | None:
        with self._lock:
            return self._state
