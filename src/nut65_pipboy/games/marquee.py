"""Marquee engine — scrolling text across the keyboard LEDs.

Text is rendered as a 4-pixel-tall bitmap font on rows 0-3, scrolling left
across the 15-column display. Row 4 is skipped (spacebar gaps).
"""

from __future__ import annotations

import datetime
from typing import override

import psutil

from nut65_pipboy.keyboard import COLS, VALID_POSITIONS
from nut65_pipboy.pixel_font import text_to_columns
from nut65_pipboy.types import HueSat

from .base import COLOR_OFF, FrameGrid, GameEngine, empty_frame

PLAY_ROWS = 5


class MarqueeGame(GameEngine):
    def __init__(self) -> None:
        super().__init__()
        self._custom_text = "NUT65 PIPBOY"
        self._system_mode = False
        self._scroll_offset = 0
        self._columns: list[list[bool]] = []
        self._info_refresh_counter = 0
        psutil.cpu_percent()  # prime the counter (first call returns 0)
        self._rebuild_canvas()

    @property
    @override
    def game_over(self) -> bool:
        return False  # marquee never ends

    @property
    def custom_text(self) -> str:
        return self._custom_text

    @custom_text.setter
    def custom_text(self, text: str) -> None:
        self._custom_text = text.upper().strip() or "NUT65 PIPBOY"
        if not self._system_mode:
            self._rebuild_canvas()

    @property
    def system_mode(self) -> bool:
        return self._system_mode

    @system_mode.setter
    def system_mode(self, value: bool) -> None:
        self._system_mode = value
        self._rebuild_canvas()

    def _rebuild_canvas(self) -> None:
        if self._system_mode:
            text = self._get_system_info()
        else:
            text = self._custom_text
        self._columns = text_to_columns(text)
        # Add trailing blank space for smooth wrap
        self._columns.extend([[False] * 5] * COLS)
        self._scroll_offset = 0

    def _get_system_info(self) -> str:
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")
        cpu = int(psutil.cpu_percent(interval=0))
        mem = int(psutil.virtual_memory().percent)
        return f"  {time_str}  CPU {cpu}%  RAM {mem}%  "

    @override
    def tick(self) -> None:
        self._scroll_offset += 1
        if self._scroll_offset >= len(self._columns):
            self._scroll_offset = 0

        # Refresh system info periodically (every ~5 seconds at 12fps)
        if self._system_mode:
            self._info_refresh_counter += 1
            if self._info_refresh_counter >= 60:
                self._info_refresh_counter = 0
                old_offset = self._scroll_offset
                self._rebuild_canvas()
                self._scroll_offset = old_offset % max(1, len(self._columns))

    @override
    def reset(self) -> None:
        self._scroll_offset = 0
        self._rebuild_canvas()

    @override
    def render(self) -> FrameGrid:
        frame = empty_frame()

        # Render visible window of the virtual canvas
        for display_col in range(COLS):
            canvas_col = (self._scroll_offset + display_col) % len(self._columns)
            column_data = self._columns[canvas_col]
            for row in range(PLAY_ROWS):
                if (row, display_col) in VALID_POSITIONS:
                    if row < len(column_data) and column_data[row]:
                        frame[row][display_col] = HueSat(self.hue, 255)
                    else:
                        frame[row][display_col] = COLOR_OFF

        # Light bar (row 5): gentle pulse
        bar_brightness = 120 + int(60 * (0.5 + 0.5 * ((self._scroll_offset % 30) / 30)))
        bar_color = HueSat(self.hue, bar_brightness)
        for c in range(COLS):
            if (5, c) in VALID_POSITIONS:
                frame[5][c] = bar_color

        return frame
