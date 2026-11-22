#!/usr/bin/env python3
"""
Headless WebSDR Client for CAMRAS Dwingeloo EME Stream.
Tunes to 70cm EME band and writes raw signed 16-bit PCM to stdout.
"""

import sys
import time
import asyncio
import requests
import websockets

HOST = "websdr.camras.nl:8901"
BASE_URL = f"http://{HOST}"
WS_URL = f"ws://{HOST}/~~stream?v=11"

# Target: 432.065 MHz USB for EME Q65
# band: 0 = 70cm on Dwingeloo
# mode: 1 = USB
TUNER_PARAMS = {
    "band": "0",
    "f": "432065",
    "lo": "0.1",
    "hi": "3.0",
    "mode": "1",
}


def log_err(msg: str) -> None:
    sys.stderr.write(f"[WEBSDR-PULL] {msg}\n")
    sys.stderr.flush()


def get_session() -> str:
    session = requests.Session()
    resp = session.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    return "; ".join([f"{c.name}={c.value}" for c in session.cookies])


async def stream_audio() -> None:
    while True:
        try:
            cookie_str = get_session()
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
                "Origin": BASE_URL,
                "Cookie": cookie_str,
            }

            async with websockets.connect(
                WS_URL, additional_headers=headers, ping_interval=20, ping_timeout=20
            ) as ws:
                param_cmd = (
                    f"GET /~~param?f={TUNER_PARAMS['f']}"
                    f"&band={TUNER_PARAMS['band']}"
                    f"&lo={TUNER_PARAMS['lo']}"
                    f"&hi={TUNER_PARAMS['hi']}"
                    f"&mode={TUNER_PARAMS['mode']}&name=EME_Node"
                )
                await ws.send(param_cmd)
                log_err(f"Locked onto {HOST} @ {TUNER_PARAMS['f']} kHz USB")

                while True:
                    frame = await ws.recv()
                    # Sanity check: ensure payload is valid even-length 16-bit PCM bytes
                    if isinstance(frame, bytes) and len(frame) >= 2:
                        if len(frame) % 2 != 0:
                            frame = frame[:-1]
                        sys.stdout.buffer.write(frame)
                        sys.stdout.buffer.flush()

        except (websockets.exceptions.WebSocketException, requests.RequestException, OSError) as exc:
            log_err(f"Stream interrupted ({exc}). Reconnecting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(stream_audio())
    except KeyboardInterrupt:
        sys.exit(0)
