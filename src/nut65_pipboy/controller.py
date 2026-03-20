"""Game controller — manages game engines, state, and configuration."""

from __future__ import annotations

import logging
import threading
import time

from nut65_pipboy.games.base import FrameGrid, GameEngine, empty_frame
from nut65_pipboy.games.marquee import MarqueeGame
from nut65_pipboy.games.pong import PongGame
from nut65_pipboy.games.snake import SnakeGame
from nut65_pipboy.keyboard import COLS, LED_MATRIX, ROWS
from nut65_pipboy.types import AppMode

log = logging.getLogger(__name__)

# Speed 1 = 500ms, speed 10 = 50ms (logarithmic-ish)
SPEED_TABLE = {
    1: 0.500, 2: 0.350, 3: 0.250, 4: 0.180, 5: 0.130,
    6: 0.100, 7: 0.083, 8: 0.070, 9: 0.060, 10: 0.050,
}


class GameController:
    """Manages game engines and provides state for the frontend."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mode = AppMode.SNAKE
        self._speed = 5
        self._engines: dict[AppMode, GameEngine] = {
            AppMode.SNAKE: SnakeGame(),
            AppMode.PONG: PongGame(),
            AppMode.MARQUEE: MarqueeGame(),
        }
        self._frame_count = 0
        self._fps_time = time.perf_counter()
        self._fps = 0.0
        self._hue = 85  # active color hue (green default)
        self._connected = False
        self._last_frame: FrameGrid | None = None
        self._seq = 0

    @property
    def tick_interval(self) -> float:
        return SPEED_TABLE.get(self._speed, 0.130)

    @property
    def current_engine(self) -> GameEngine:
        return self._engines[self._mode]

    def set_mode(self, mode: str) -> None:
        with self._lock:
            try:
                new_mode = AppMode(mode)
            except ValueError:
                return
            if new_mode != self._mode:
                self._mode = new_mode
                self._engines[new_mode].reset()
                log.info("Mode switched to %s", new_mode)

    def set_speed(self, value: int) -> None:
        with self._lock:
            self._speed = max(1, min(10, value))

    def set_marquee_text(self, text: str) -> None:
        with self._lock:
            engine = self._engines[AppMode.MARQUEE]
            if isinstance(engine, MarqueeGame):
                engine.custom_text = text

    def set_hue(self, hue: int) -> None:
        with self._lock:
            self._hue = max(0, min(255, hue))

    def set_marquee_mode(self, mode: str) -> None:
        with self._lock:
            engine = self._engines[AppMode.MARQUEE]
            if isinstance(engine, MarqueeGame):
                engine.system_mode = mode == "system"

    def set_connected(self, connected: bool) -> None:
        self._connected = connected

    def step(self) -> tuple[FrameGrid, dict]:
        """Tick, render, and return frame + state dict. Thread-safe."""
        with self._lock:
            self._tick()
            frame = self._render()
            state = self._build_state()
        return frame, state

    def _tick(self) -> None:
        """Advance the current game by one step. Call with lock held."""
        engine = self.current_engine
        engine.hue = self._hue
        engine.tick()

        # FPS tracking
        self._frame_count += 1
        now = time.perf_counter()
        elapsed = now - self._fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = now

    def _render(self) -> FrameGrid:
        """Get the current frame and cache it. Call with lock held."""
        self._last_frame = self.current_engine.render()
        return self._last_frame

    def _build_state(self) -> dict:
        """Build state dict for the frontend. Call with lock held."""
        frame = self._last_frame or empty_frame()

        colors = []
        for row, col in LED_MATRIX:
            cell = frame[row][col]
            if cell is not None:
                colors.append({"row": row, "col": col, "hue": cell.hue, "sat": cell.sat})
            else:
                colors.append({"row": row, "col": col, "hue": 0, "sat": 0})

        self._seq += 1
        return {
            "seq": self._seq,
            "connected": self._connected,
            "mode": self._mode.value,
            "score": self.current_engine.score,
            "fps": round(self._fps, 1),
            "gameOver": self.current_engine.game_over,
            "speed": self._speed,
            "colors": colors,
        }
