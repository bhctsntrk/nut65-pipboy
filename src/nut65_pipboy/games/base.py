"""Base class for all game engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

from nut65_pipboy.keyboard import COLS, ROWS
from nut65_pipboy.types import HueSat

type FrameGrid = list[list[HueSat | None]]

COLOR_OFF = HueSat(hue=0, sat=0)


def empty_frame() -> FrameGrid:
    """Create an empty 6x15 frame (all None)."""
    return [[None for _ in range(COLS)] for _ in range(ROWS)]


class GameEngine(ABC):
    """Abstract base for autonomous game engines.

    Each engine produces 6x15 HSV frames at a configurable tick rate.
    Games are AI-controlled — no user input for gameplay.
    """

    def __init__(self) -> None:
        self.hue: int = 85  # active color hue, set by controller each tick

    @property
    def score(self) -> int:
        """Current game score. Override in subclasses that track score."""
        return 0

    @abstractmethod
    def tick(self) -> None:
        """Advance the game by one step."""

    @abstractmethod
    def render(self) -> FrameGrid:
        """Return the current 6x15 HSV grid for display."""

    @abstractmethod
    def reset(self) -> None:
        """Restart the game from scratch."""

    @property
    @abstractmethod
    def game_over(self) -> bool:
        """Whether the game has ended (waiting for restart)."""
