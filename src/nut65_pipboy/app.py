"""Main application — pywebview window + game loop thread.

Game loop runs in background thread via webview.start(func=...).
Frontend polls state via pywebview.api.get_state() (pull-based).
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time

import webview

from nut65_pipboy.api import PipboyAPI, StateRelay
from nut65_pipboy.controller import GameController
from nut65_pipboy.hid_device import DeviceDisconnectedError, DeviceNotFoundError, HIDDevice
from nut65_pipboy.keyboard import Keyboard

log = logging.getLogger(__name__)


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource — works for dev and PyInstaller."""
    base = getattr(sys, "_MEIPASS", None)
    if base is not None:
        return os.path.join(base, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", relative_path)


def game_loop(
    window: webview.Window,
    controller: GameController,
    relay: StateRelay,
    api: PipboyAPI,
    shutdown: threading.Event,
) -> None:
    """Background thread: tick game, flush HID, publish state."""

    # Wait for frontend to be ready
    log.info("Game loop waiting for frontend...")
    if not api.wait_for_client(timeout=30):
        log.warning("Frontend did not signal ready in 30s, starting anyway")

    # Try to connect to keyboard
    device: HIDDevice | None = None
    keyboard: Keyboard | None = None

    def try_connect() -> bool:
        nonlocal device, keyboard
        try:
            device = HIDDevice()
            device.connect()
            device.init_direct_mode()
            keyboard = Keyboard(device)
            keyboard.force_full_refresh()
            controller.set_connected(True)
            log.info("Keyboard connected")
            return True
        except DeviceNotFoundError:
            controller.set_connected(False)
            log.info("Keyboard not found, will retry...")
            return False

    connected = try_connect()
    reconnect_counter = 0

    next_tick = time.perf_counter()

    while not shutdown.is_set():
        # Reconnect logic
        if not connected:
            reconnect_counter += 1
            if reconnect_counter >= 24:  # every 2s at 12fps
                reconnect_counter = 0
                connected = try_connect()
            shutdown.wait(controller.tick_interval)
            continue

        # Tick game — lock is handled inside step()
        frame, state = controller.step()

        # Flush to keyboard (outside controller lock)
        if keyboard:
            try:
                keyboard.set_frame(frame)
                keyboard.flush()
            except DeviceDisconnectedError:
                log.warning("Keyboard disconnected")
                connected = False
                device = None
                keyboard = None
                controller.set_connected(False)
                continue

        # Publish state for frontend
        relay.publish(state)

        # Fixed timestep
        next_tick += controller.tick_interval
        sleep_time = next_tick - time.perf_counter()
        if sleep_time > 0:
            shutdown.wait(sleep_time)
        else:
            next_tick = time.perf_counter()

    # Cleanup
    if device:
        try:
            device.close()
        except (OSError, DeviceDisconnectedError):
            pass
    log.info("Game loop stopped")


def run_app() -> None:
    """Launch the Pip-Boy application."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    controller = GameController()
    relay = StateRelay()
    api = PipboyAPI(controller, relay)

    shutdown = threading.Event()

    frontend_path = resource_path("frontend/index.html")
    if not os.path.exists(frontend_path):
        log.error("Frontend not found at %s", frontend_path)
        sys.exit(1)

    window = webview.create_window(
        title="NUT-65 PIPBOY",
        url=frontend_path,
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 600),
        background_color="#0a0a0a",
        confirm_close=True,
    )

    api.set_window(window)

    def on_closing():
        shutdown.set()
        return True

    window.events.closing += on_closing

    log.info("Starting NUT-65 Pip-Boy...")

    webview.start(
        game_loop,
        (window, controller, relay, api, shutdown),
        debug=False,
    )
