#!/usr/bin/env python3
"""
Orbitsville Lunar Relay Monitor (Pane 1)
Intercepts and decodes WSJT-X UDP broadcasts on 127.0.0.1:2237.
"""

import datetime
import socket
import struct
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 2237
WSJTX_MAGIC = b"\xad\xbc\xcb\xda"


def bind_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((UDP_IP, UDP_PORT))
    except OSError as exc:
        print(f"[FATAL] Cannot bind UDP {UDP_IP}:{UDP_PORT} -> {exc}")
        sys.exit(1)
    return sock


def read_utf8(buf: bytes, offset: int) -> tuple[str, int]:
    """Unpack a Qt QDataStream length-prefixed UTF-8 string."""
    if offset + 4 > len(buf):
        raise ValueError("Truncated string length")
    length = struct.unpack(">I", buf[offset : offset + 4])[0]
    offset += 4
    # 0xFFFFFFFF denotes a null QString in QDataStream
    if length == 0xFFFFFFFF:
        return "", offset
    if offset + length > len(buf):
        raise ValueError("Truncated string payload")
    text = buf[offset : offset + length].decode("utf-8", errors="replace")
    return text, offset + length


def parse_decode_packet(data: bytes) -> dict:
    """Parse WSJT-X Message Type 2 (Decode) payload starting at byte 12."""
    offset = 12
    client_id, offset = read_utf8(data, offset)

    # New (bool: 1B), Time (quint32 ms: 4B), SNR (qint32: 4B),
    # DeltaTime (double: 8B), DeltaFreq (quint32: 4B) -> 21 bytes
    if offset + 21 > len(data):
        raise ValueError("Truncated decode metrics")

    is_new, time_ms, snr, delta_t, delta_f = struct.unpack(
        ">?IidI", data[offset : offset + 21]
    )
    offset += 21

    mode, offset = read_utf8(data, offset)
    message, offset = read_utf8(data, offset)

    return {
        "client_id": client_id,
        "is_new": is_new,
        "time_ms": time_ms,
        "snr": snr,
        "dt": delta_t,
        "df": delta_f,
        "mode": mode,
        "message": message.strip(),
    }


def main() -> None:
    sock = bind_socket()

    print("=====================================================")
    print("  ORBITSVILLE LUNAR RELAY MONITOR // NODE: DWINGELOO ")
    print("  UPLINK: 432 MHz EME ARRAY // PROTOCOL: Q65 / JT65   ")
    print("=====================================================")
    print(f"[STATUS] Listening for WSJT-X UDP telemetry on :{UDP_PORT}...\n")
    sys.stdout.flush()

    while True:
        try:
            data, _ = sock.recvfrom(4096)

            # Header: Magic (0..4), Schema (4..8), Message Type (8..12)
            if len(data) < 12 or data[:4] != WSJTX_MAGIC:
                continue

            msg_type = struct.unpack(">I", data[8:12])[0]

            # Message Type 2 = Decode
            if msg_type == 2:
                dec = parse_decode_packet(data)
                if dec["is_new"] and dec["message"]:
                    now = datetime.datetime.now(datetime.timezone.utc).strftime(
                        "%H:%M:%S UTC"
                    )
                    print(
                        f"[{now}] [{dec['mode']}] {dec['snr']:+3d} dB | "
                        f"{dec['df']:4d} Hz | {dec['message']}"
                    )
                    sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(f"[WARN] Packet parse anomaly: {exc}")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
