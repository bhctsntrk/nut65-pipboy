"""Entry point: python -m nut65_pipboy

Usage:
  uv run python -m nut65_pipboy          Launch Pip-Boy GUI
  uv run python -m nut65_pipboy --demo   Keyboard-only demo (no GUI)
  uv run python -m nut65_pipboy --smoke  Quick color test
"""

from __future__ import annotations

import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def smoke_test() -> None:
    from nut65_pipboy.hid_device import DeviceNotFoundError, HIDDevice
    from nut65_pipboy.keyboard import Keyboard
    from nut65_pipboy.types import HueSat

    GREEN = HueSat(hue=85, sat=255)
    RED = HueSat(hue=0, sat=255)
    BLUE = HueSat(hue=170, sat=255)
    OFF = HueSat(hue=0, sat=0)

    try:
        with HIDDevice() as device:
            device.init_direct_mode()
            kb = Keyboard(device)
            print("GREEN..."); kb.fill(GREEN); kb.flush(); time.sleep(1.5)
            print("RED/BLUE..."); kb.fill(GREEN)
            for c in range(15):
                kb.set_pixel(0, c, RED); kb.set_pixel(1, c, BLUE)
            kb.flush(); time.sleep(1.5)
            print("OFF..."); kb.fill(OFF); kb.flush(); time.sleep(0.5)
    except DeviceNotFoundError as e:
        print(f"ERROR: {e}")


def demo_mode() -> None:
    from nut65_pipboy.games.marquee import MarqueeGame
    from nut65_pipboy.games.pong import PongGame
    from nut65_pipboy.games.snake import SnakeGame
    from nut65_pipboy.hid_device import DeviceDisconnectedError, DeviceNotFoundError, HIDDevice
    from nut65_pipboy.keyboard import Keyboard

    TICK = 1.0 / 12
    DURATION = 10.0

    try:
        with HIDDevice() as device:
            device.init_direct_mode()
            kb = Keyboard(device)
            games = [("SNAKE", SnakeGame()), ("PONG", PongGame()), ("MARQUEE", MarqueeGame())]
            print("Demo: Ctrl+C to stop")
            while True:
                for name, game in games:
                    print(f"\n>>> {name} <<<")
                    game.reset(); kb.force_full_refresh()
                    start = time.perf_counter(); next_tick = start; frames = 0
                    while time.perf_counter() - start < DURATION:
                        game.tick(); kb.set_frame(game.render())
                        try:
                            kb.flush()
                        except DeviceDisconnectedError:
                            print("Disconnected!"); return
                        frames += 1; next_tick += TICK
                        s = next_tick - time.perf_counter()
                        if s > 0: time.sleep(s)
                        else: next_tick = time.perf_counter()
                    elapsed = time.perf_counter() - start
                    print(f"  {frames} frames, {frames/elapsed:.1f} fps")
    except DeviceNotFoundError as e:
        print(f"ERROR: {e}")
    except KeyboardInterrupt:
        print("\nStopped")


def main() -> None:
    if "--smoke" in sys.argv:
        smoke_test()
    elif "--demo" in sys.argv:
        demo_mode()
    else:
        from nut65_pipboy.app import run_app
        run_app()


if __name__ == "__main__":
    main()
