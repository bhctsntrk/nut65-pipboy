"""HID communication layer for Weikav NUT65 keyboard.

Uses VIA RAW HID protocol over USB. Only command 0x07 (SET_VALUE) is permitted.
All writes go to RAM only — EEPROM is never touched.
"""

from __future__ import annotations

import logging
from types import TracebackType

import hid

log = logging.getLogger(__name__)

VID = 0x342D
PID = 0xE51A
USAGE_PAGE = 0xFF60
USAGE = 0x61
REPORT_SIZE = 33

# Security: only SET_VALUE (0x07) is allowed. 0x09 writes EEPROM — never send it.
ALLOWED_COMMANDS = frozenset({0x07})

CMD_SET = 0x07
MODE_DIRECT = 45
MODE_SOLID = 1


class DeviceNotFoundError(Exception):
    pass


class DeviceDisconnectedError(Exception):
    pass


class HIDDevice:
    """Context-managed HID connection to the NUT65."""

    def __init__(self) -> None:
        self._dev: hid.device | None = None
        self._consecutive_failures = 0
        self._max_failures = 5

    def __enter__(self) -> HIDDevice:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def connect(self) -> None:
        """Find and open the NUT65 VIA RAW HID endpoint."""
        devices = hid.enumerate(VID, PID)
        target = None
        for d in devices:
            if d.get("usage_page") == USAGE_PAGE and d.get("usage") == USAGE:
                target = d
                break

        if target is None:
            raise DeviceNotFoundError(
                f"NUT65 not found (VID=0x{VID:04X} PID=0x{PID:04X}). "
                "Is it connected via USB-C? Is VIA/Vial/SignalRGB closed?"
            )

        dev = hid.device()
        try:
            dev.open_path(target["path"])
        except OSError as e:
            raise DeviceNotFoundError(
                f"Cannot open HID device: {e}. Is VIA or SignalRGB running?"
            ) from e

        dev.set_nonblocking(False)
        self._dev = dev
        self._consecutive_failures = 0
        log.info("Connected to %s", dev.get_product_string())

    def close(self) -> None:
        if self._dev is not None:
            try:
                self.restore_mode()
            except (OSError, DeviceDisconnectedError):
                pass
            if self._dev is not None:
                self._dev.close()
            self._dev = None
            log.info("HID device closed")

    def _send(self, cmd: list[int]) -> list[int] | None:
        """Send a 33-byte HID report. Validates command byte against allowlist."""
        if self._dev is None:
            raise DeviceDisconnectedError("HID device not connected")

        if not cmd:
            raise ValueError("Empty command")

        command_byte = cmd[0]
        if command_byte not in ALLOWED_COMMANDS:
            raise ValueError(
                f"Forbidden HID command: 0x{command_byte:02X}. "
                f"Only {[f'0x{c:02X}' for c in ALLOWED_COMMANDS]} are allowed."
            )

        packet = [0x00] + cmd + [0x00] * (REPORT_SIZE - 1 - len(cmd))
        packet = packet[:REPORT_SIZE]

        try:
            self._dev.write(packet)
            self._consecutive_failures = 0
            resp = self._dev.read(64, 100)
            return list(resp) if resp else None
        except OSError as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                log.warning("HID watchdog: %d consecutive failures, disconnecting", self._max_failures)
                self._dev = None
                raise DeviceDisconnectedError(f"Device lost after {self._max_failures} failures") from e
            raise DeviceDisconnectedError(str(e)) from e

    def init_direct_mode(self) -> None:
        """Set keyboard to Direct Control mode (45) with max brightness."""
        self._send([CMD_SET, 0x03, 0x02, MODE_DIRECT])
        self._send([CMD_SET, 0x03, 0x01, 0xFF])
        self._send([CMD_SET, 0x03, 0x03, 0x00])
        self._send([CMD_SET, 0x00, 0x01, 0x01])  # lightstrip static
        log.info("Direct control mode activated (mode 45)")

    def restore_mode(self) -> None:
        """Restore keyboard to Solid Color mode (1)."""
        self._send([CMD_SET, 0x03, 0x02, MODE_SOLID])
        log.info("Restored to Solid Color mode")

    def set_key_color(self, row: int, col: int, hue: int, sat: int) -> None:
        """Set a single key's color. row: 0-5, col: 0-14, hue/sat: 0-255."""
        if row < 0 or row > 5 or col < 0 or col > 14:
            return
        self._send([CMD_SET, 0x00, 0x03, 0x00, row, col, sat, hue])

    def apply(self) -> None:
        """Flush all pending per-key colors to the display."""
        self._send([CMD_SET, 0x00, 0x02, 0x00])
