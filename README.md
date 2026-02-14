# Lightweight VJ Pro (OpenDMX) 🚀

A lightweight, high-performance Python-based DMX lighting controller designed for Techno, Tech House, and Pop parties. Optimized for macOS and FTDI-based "Open DMX" interfaces.

> **Status:** 🚧 Work in Progress - Pre-show release for tomorrow's party!

## 🌟 Features

-   **Real-time Audio Analysis:** Beat and BPM detection via "BlackHole 2ch" virtual audio.
-   **Stable DMX Output:** Custom "Baud-rate Hack" for macOS to ensure flicker-free DMX signals even on cheap FTDI interfaces.
-   **Mobile-First VJ Dashboard:** Responsive web interface for touch-control on smartphones or tablets.
-   **Hardware MIDI Support:** Full integration for **Akai Professional LPK25 MKII** – use your keyboard as a live lighting instrument!
-   **Techno-Ready Presets:** 
    -   *Techno Red, Acid Green, Industrial Amber (Breathing)*
    -   *Alt Kick (Left/Right alternating flashes)*
    -   *R/G Dance (Color swapping per beat)*
    -   *Glitch Mode & Turbo Strobe (15Hz)*
    -   *Pop Presets: Vivid Rainbow, Barbie Party, Pastel Dream*

## 🛠 Hardware Setup

1.  **Mac:** Intel or Apple Silicon.
2.  **Audio:** [BlackHole 2ch](https://existential.audio/blackhole/) (for internal audio routing).
3.  **DMX Interface:** FTDI-based USB interface (e.g., [OpenDMX.de](https://opendmx.de)).
4.  **MIDI (Optional):** Akai LPK25 MKII.
5.  **Lights:** 
    -   LED Panel 1: DMX Channel 10 (Dimmer), 11-13 (RGB)
    -   LED Panel 2: DMX Channel 20 (Dimmer), 21-23 (RGB)
    -   Party Bar: DMX Channel 30+

## 🚀 Getting Started

### 1. Requirements
Ensure you have `portaudio` installed (required for `pyaudio`):
```bash
brew install portaudio
```

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Usage
Run the main application:
```bash
python3 main.py
```
-   **Web Dashboard:** Open `http://localhost:5005` on your Mac or any device in the same network.
-   **MIDI:** Plug in your Akai LPK25 and start playing the lights.

## 🎹 MIDI Mapping (Akai LPK25)
-   **White Keys (Left to Right):** Various Presets (Techno, House, Pop).
-   **Highest B-Key (71):** Instant STROBE (Hold to fire).
-   **Highest C-Key (72):** MASTER BLACKOUT.

## ⚖️ License
MIT - Created by Spekulazarus & Sisyphus AI.
