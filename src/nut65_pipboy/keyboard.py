"""Keyboard matrix abstraction and frame buffer for the NUT65.

6 rows x 15 cols, 82 LEDs (8 positions are empty).
Delta-optimized flush: only writes changed cells to HID.
"""

from __future__ import annotations

import logging

from nut65_pipboy.hid_device import HIDDevice
from nut65_pipboy.types import HueSat

log = logging.getLogger(__name__)

ROWS = 6
COLS = 15

# Matrix positions that have physical LEDs — ported from Weikav_NUT65.js vKeyMatrix.
# Each entry is (row, col). Index = LED number (0-81).
LED_MATRIX: list[tuple[int, int]] = [
    # Row 0: 15 keys
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),
    (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14),
    # Row 1: 15 keys
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
    (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14),
    # Row 2: 14 keys (col 12 missing)
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
    (2, 8), (2, 9), (2, 10), (2, 11), (2, 13), (2, 14),
    # Row 3: 14 keys (col 1 missing)
    (3, 0), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8),
    (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14),
    # Row 4: 9 keys (spacebar region gaps)
    (4, 0), (4, 1), (4, 2), (4, 5), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14),
    # Row 5: 15 light bar segments
    (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
    (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14),
]

# Set of valid (row, col) positions for fast lookup
VALID_POSITIONS: frozenset[tuple[int, int]] = frozenset(LED_MATRIX)

# Hysteresis threshold for delta optimization
HYSTERESIS = 3


class Keyboard:
    """Frame buffer and delta-optimized HID writer for the NUT65."""

    def __init__(self, device: HIDDevice) -> None:
        self._device = device
        self._current: list[HueSat | None] = [None] * (ROWS * COLS)
        self._previous: list[HueSat | None] = [None] * (ROWS * COLS)

    def _idx(self, row: int, col: int) -> int:
        return row * COLS + col

    def clear(self) -> None:
        """Reset frame buffer to all off (S=0, H=0)."""
        off = HueSat(0, 0)
        for row, col in LED_MATRIX:
            self._current[self._idx(row, col)] = off

    def set_pixel(self, row: int, col: int, color: HueSat) -> None:
        """Set a single pixel in the frame buffer."""
        if (row, col) in VALID_POSITIONS:
            self._current[self._idx(row, col)] = color

    def set_frame(self, frame: list[list[HueSat | None]]) -> None:
        """Set the entire frame buffer from a 6x15 grid."""
        for row in range(ROWS):
            for col in range(COLS):
                if (row, col) in VALID_POSITIONS:
                    self._current[self._idx(row, col)] = frame[row][col]

    def flush(self) -> int:
        """Write changed pixels to HID. Returns the number of HID writes sent."""
        writes = 0
        for row, col in LED_MATRIX:
            idx = self._idx(row, col)
            cur = self._current[idx]
            prev = self._previous[idx]

            if cur is None:
                continue

            if prev is not None:
                if abs(cur.hue - prev.hue) <= HYSTERESIS and abs(cur.sat - prev.sat) <= HYSTERESIS:
                    continue

            self._device.set_key_color(row, col, cur.hue, cur.sat)
            self._previous[idx] = cur
            writes += 1

        if writes > 0:
            self._device.apply()
            writes += 1

        return writes

    def force_full_refresh(self) -> None:
        """Force all pixels to be re-sent on next flush."""
        self._previous = [None] * (ROWS * COLS)

    def fill(self, color: HueSat) -> None:
        """Fill the entire keyboard with a single color."""
        for row, col in LED_MATRIX:
            self._current[self._idx(row, col)] = color
