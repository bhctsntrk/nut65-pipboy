<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Keyboard-Weikav%20NUT65-orange" alt="Weikav NUT65">
</p>

<h1 align="center">NUT-65 PIP-BOY</h1>

<p align="center">
  <b>Fallout Pip-Boy themed desktop GUI that runs AI-controlled mini-games on your keyboard's RGB LEDs</b>
</p>

<p align="center">
  <a href="#-features">Features</a> &bull;
  <a href="#-installation">Installation</a> &bull;
  <a href="#-usage">Usage</a> &bull;
  <a href="#-architecture">Architecture</a> &bull;
  <a href="#-tr-turkce">Turkce</a>
</p>

---

## Overview

A standalone desktop application that turns your **Weikav NUT65** mechanical keyboard into a tiny game console. Three AI-controlled games run directly on the keyboard's 82 RGB LEDs, displayed through a retro CRT terminal interface inspired by Fallout's Pip-Boy.

The games are fully autonomous — no player input needed. The AI plays Snake, Pong, and scrolling Marquee text while you watch (or work).

## Features

- **Snake** — Greedy + tail-escape BFS AI on a 15x4 grid (58 playable cells)
- **Pong** — Two imperfect AI paddles with spin physics
- **Marquee** — 5x5 pixel bitmap font, scrolling custom or system info text
- **CRT Terminal UI** — Scanlines, phosphor glow, vignette, flicker animation
- **Real Keyboard Preview** — SVG replica of the NUT65 layout with live LED colors
- **Color Palette** — 6 color presets (Green, Cyan, Blue, Red, Purple, Amber)
- **Speed Control** — 10-step slider from 2 FPS to 20 FPS
- **Bilingual** — English / Turkish (EN/TR)
- **Browser Demo** — Works standalone in Chrome for design iteration (no keyboard needed)
- **Delta-Optimized HID** — Only changed LEDs are written, with hysteresis to reduce USB traffic

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | [pywebview](https://pywebview.flowrl.com/) (Edge WebView2) |
| Frontend | Vanilla HTML/CSS/JS, SVG |
| Backend | Python 3.12+ |
| HID | [hidapi](https://github.com/trezor/cython-hidapi) via VIA RAW HID protocol |
| Font | [VT323](https://fonts.google.com/specimen/VT323) (Google Fonts) |
| Packaging | [uv](https://docs.astral.sh/uv/) |

## Installation

```bash
# Clone
git clone https://github.com/bhctsntrk/nut65-pipboy.git
cd nut65-pipboy

# Install dependencies (requires uv)
uv sync
```

## Usage

```bash
# Launch the GUI (main mode)
uv run python -m nut65_pipboy

# Keyboard-only demo (no GUI, cycles through games)
uv run python -m nut65_pipboy --demo

# Quick color test (green → red/blue → off)
uv run python -m nut65_pipboy --smoke
```

> **Important:** Close VIA, Vial, and SignalRGB before launching — only one app can control the keyboard's HID interface at a time.

## Architecture

```
pywebview (main thread)          Game Loop (background thread)
┌──────────────────┐             ┌──────────────────────────┐
│  HTML/CSS/JS     │  polls      │  controller.step()       │
│  CRT Terminal UI │◄────────────│    tick → render → state  │
│  SVG Keyboard    │  80ms       │                          │
│                  │             │  keyboard.flush()         │
│  PipboyAPI       │             │    delta HID writes      │
│  (js_api bridge) │             │    hysteresis ±3         │
└──────────────────┘             └──────────────────────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │  USB HID (0xFF60) │
                                 │  NUT65 Keyboard   │
                                 │  82 RGB LEDs      │
                                 └──────────────────┘
```

### Key Design Decisions

- **Pull-based state** — JS polls `get_state()` via `setTimeout`, no `run_js()` push (prevents flickering)
- **Frame caching** — `render()` caches the frame, `state_dict()` reads the cache (prevents torn frames)
- **Command allowlist** — Only `0x07` (SET_VALUE) is permitted over HID. `0x09` (EEPROM write) is blocked to protect firmware
- **HID flush outside lock** — Controller lock only covers tick/render/serialize (~1ms), not USB I/O (up to 250ms on full refresh)

## HID Safety

The keyboard communicates over VIA RAW HID protocol. A strict command allowlist ensures only `SET_VALUE` (0x07) commands are sent — **EEPROM writes (0x09) are permanently blocked** to prevent accidental firmware corruption.

## Project Structure

```
nut65-pipboy/
├── frontend/
│   ├── index.html          # CRT terminal layout
│   ├── style.css           # Pip-Boy theme + CRT effects
│   ├── app.js              # Keyboard SVG, demo games, i18n, bridge
│   └── fonts/VT323.woff2   # Retro terminal font
├── src/nut65_pipboy/
│   ├── app.py              # pywebview window + game loop thread
│   ├── api.py              # JS↔Python bridge (PipboyAPI)
│   ├── controller.py       # Game engine manager + state serialization
│   ├── hid_device.py       # USB HID communication (command allowlist)
│   ├── keyboard.py         # LED matrix + delta-optimized flush
│   ├── pixel_font.py       # 5x5 bitmap font (A-Z, 0-9, symbols)
│   ├── types.py            # HueSat, AppMode
│   └── games/
│       ├── base.py         # GameEngine ABC
│       ├── snake.py        # Snake AI (BFS pathfinding)
│       ├── pong.py         # Pong AI (imperfect tracking)
│       └── marquee.py      # Scrolling text + system info
└── pyproject.toml
```

## License

MIT

---

<h2 id="-tr-turkce">Turkce</h2>

Weikav NUT65 mekanik klavyenizin 82 RGB LED'ini oyun konsoluna donusturen masaustu uygulamasi.

### Ozellikler

- **Yilan** — BFS yapay zeka ile 15x4 izgara uzerinde otonom yilan oyunu
- **Pong** — Iki yapay zeka raket ile ping pong
- **Kayan Yazi** — 5x5 piksel font ile ozel metin veya sistem bilgisi
- **CRT Terminal** — Fallout Pip-Boy temali retro arayuz (tarama cizgileri, fosfor isigi)
- **Gercek Klavye Onizleme** — NUT65 tuslarinin canli SVG gorunumu
- **Renk Paleti** — 6 renk secenegi (Yesil, Camgobegi, Mavi, Kirmizi, Mor, Kehribar)
- **Hiz Kontrolu** — 2 FPS'den 20 FPS'ye 10 kademeli ayar
- **Cift Dil** — Ingilizce / Turkce

### Kurulum

```bash
git clone https://github.com/bhctsntrk/nut65-pipboy.git
cd nut65-pipboy
uv sync
```

### Calistirma

```bash
# GUI ile baslat
uv run python -m nut65_pipboy

# Sadece klavye demosu (GUI yok)
uv run python -m nut65_pipboy --demo
```

> **Onemli:** VIA, Vial veya SignalRGB'yi kapatmayi unutmayin — HID arabirimi ayni anda sadece bir uygulama tarafindan kullanilabilir.
