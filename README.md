# ORBITSVILLE // Lunar EME Cyberdeck

A Nix Flake-powered Earth-Moon-Earth (EME) telemetry terminal and signal decoding stack built for NixOS-WSL2. Orbitsville pulls live 70cm RF audio from the Dwingeloo 25m radio telescope WebSDR (`websdr.camras.nl`), routes it through a calibrated PulseAudio virtual bus into WSJT-X for Q65 moonbounce decoding, and renders real-time telemetry inside a three-pane `cool-retro-term` / `tmux` matrix.

---

## Architecture & Pipeline

```text
websdr.camras.nl:8901 (432.065 MHz USB)
       │
       ▼
websdr_pull.py ──▶ pacat ──▶ PulseAudio (lunar_sink @ 30% gain)
                                    │
                                    ▼
                           WSJT-X (Q65-B, 60s T/R)
                                    │
                                    ▼ (UDP 127.0.0.1:2237)
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
        orbitsville_terminal.py             lunar_decodes.log
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
track_moon.py               lunar_radar.py
(Luna Ephemeris)            (25m Dish Vector)
```

---

## Project Structure

```text
orbitsville/
├── flake.nix                        # Reproducible Nix environment & process orchestrator
├── lunar_decodes.log                # Persistent archive of decoded EME signals (auto-generated)
└── scripts/
    ├── websdr_pull.py               # Streams raw PCM audio from CAMRAS WebSDR
    ├── orbitsville_terminal.py      # Parses WSJT-X UDP Message Type 2 packets & logs decodes
    ├── track_moon.py                # Calculates live Azimuth, Elevation, Slant Range & Echo Delay
    └── lunar_radar.py               # Renders ASCII 25m dish vector and lunar transit progress
```

---

## Prerequisites

* **OS:** Windows 10/11 with WSL2 + WSLg enabled, running **NixOS-WSL**.
* **Nix Configuration:** Experimental `nix-command` and `flakes` features enabled in `/etc/nixos/configuration.nix`:
  ```nix
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  ```

---

## Quick Start

1. **Enter the project directory:**
   ```bash
   cd ~/Documents/orbitsville
   ```

2. **Boot the Orbitsville stack:**
   ```bash
   nix run
   ```
   This single command automatically:
   * Initializes PulseAudio and creates the `lunar_sink` (`LunarEME`) virtual audio bus calibrated to **30% gain** (~53 dB input floor in WSJT-X).
   * Connects `websdr_pull.py` to `websdr.camras.nl:8901` tuned to **432.065 MHz USB**.
   * Launches **WSJT-X** in the background.
   * Opens **cool-retro-term** attached to a 3-pane `tmux` dashboard.

---

## First-Time WSJT-X Configuration

On initial launch, verify these settings inside WSJT-X (**File → Settings**):

* **Audio Tab:**
  * **Input:** `lunar_sink.monitor` (`Mono`)
  * **Output:** `lunar_sink` (`Mono`)
* **Reporting Tab:**
  * **UDP Server:** `127.0.0.1`
  * **UDP Server port number:** `2237`
  * **Accept UDP requests:** Checked
* **Main Window:**
  * **Band / Frequency:** `70cm` (`432.065 000` MHz)
  * **Mode:** `Q65` | **Submode:** `B` | **T/R:** `60 s`

> **Note:** Close WSJT-X via **File → Exit** at least once after configuring so preferences are saved permanently to `~/.config/WSJT-X.ini`.

---

## Telemetry & Logs

* **Project Decode Log:** `~/Documents/orbitsville/lunar_decodes.log` (formatted UTC timestamps, SNR, frequency offset, and decoded callsigns).
* **WSJT-X Master Log:** `~/.local/share/WSJT-X/ALL.TXT`
* **Lunar Visibility:** EME reception requires Luna to be above the Dwingeloo horizon (`52.812° N, 6.396° E`, `EL > 0°`). Monitor the top-right **Celestial Target Tracker** pane for `IN BEAM (ABOVE HORIZON)` status.

---

## Controls & Troubleshooting

| Task | Command / Shortcut |
| :--- | :--- |
| **Switch `tmux` panes** | `Ctrl + b`, then `Arrow Keys` |
| **Zoom / unzoom active pane** | `Ctrl + b`, then `z` |
| **Enter debug dev shell** | `nix develop` |
| **Open visual audio mixer** | `nix develop --command pavucontrol` |
| **Adjust sink gain manually** | `pactl set-sink-volume lunar_sink 30%` |
| **Reset broken WSLg display** | Run `wsl --shutdown` in Windows PowerShell |
