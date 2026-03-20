from enum import StrEnum
from typing import NamedTuple


class HueSat(NamedTuple):
    hue: int  # 0-255 (QMK scale, not 0-360)
    sat: int  # 0-255


class AppMode(StrEnum):
    SNAKE = "snake"
    PONG = "pong"
    MARQUEE = "marquee"
