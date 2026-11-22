#!/usr/bin/env python3
"""
Orbitsville EME Radar & Wireframe Vector Display (Pane 3)
"""

import curses
import math
import time


def safe_addch(stdscr, y: int, x: int, ch: str, max_y: int, max_x: int) -> None:
    if 0 <= y < max_y - 1 and 0 <= x < max_x - 1:
        try:
            stdscr.addch(y, x, ch)
        except curses.error:
            pass


def draw_wireframe_moon(
    stdscr, center_y: int, center_x: int, radius: int, angle: float, max_y: int, max_x: int
) -> None:
    # Latitude rings
    num_lat = 7
    for i in range(1, num_lat):
        lat = (math.pi / num_lat) * i - (math.pi / 2)
        r_ring = radius * math.cos(lat)
        y_offset = int(radius * math.sin(lat) * 0.55)

        for deg in range(0, 360, 20):
            rad = math.radians(deg + angle)
            x = int(r_ring * math.cos(rad))
            y = int(y_offset + (r_ring * math.sin(rad) * 0.2))
            safe_addch(stdscr, center_y + y, center_x + x, ".", max_y, max_x)

    # Longitude ribs
    num_lon = 8
    for i in range(num_lon):
        lon_angle = math.radians((i * (180 / num_lon)) + angle)
        for deg in range(-90, 90, 15):
            rad = math.radians(deg)
            y = int(radius * math.sin(rad) * 0.55)
            x = int(radius * math.cos(rad) * math.sin(lon_angle))
            char = ":" if math.cos(lon_angle) >= 0 else "."
            safe_addch(stdscr, center_y + y, center_x + x, char, max_y, max_x)

    # Outer horizon silhouette
    for deg in range(0, 360, 10):
        rad = math.radians(deg)
        x = int(radius * math.cos(rad))
        y = int(radius * math.sin(rad) * 0.55)
        safe_addch(stdscr, center_y + y, center_x + x, "o", max_y, max_x)


def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)

    angle = 0.0
    pulse_pos = 0.0

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            break

        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        # Sanity check: ensure terminal dimensions can render the wireframe safely
        if max_y < 14 or max_x < 42:
            stdscr.addstr(0, 0, "PANE TOO SMALL FOR RADAR (MIN 42x14)")
            stdscr.refresh()
            time.sleep(0.2)
            continue

        header = "// ORBITSVILLE EME RADAR // 25M DISH VECTOR"
        stdscr.addstr(1, 2, header[: max_x - 3])
        stdscr.addstr(2, 2, "=" * min(len(header), max_x - 4))

        moon_center_x = int(max_x * 0.72)
        moon_center_y = int(max_y * 0.48)
        radius = max(3, min(int(max_y * 0.30), int(max_x * 0.15)))

        draw_wireframe_moon(stdscr, moon_center_y, moon_center_x, radius, angle, max_y, max_x)

        dish_y = max_y - 3
        dish_x = 3
        stdscr.addstr(dish_y, dish_x, "[(=)] 25m ARRAY")

        beam_chars = ["-", "~", "=", "*"]
        steps = 14
        for step in range(1, steps):
            t = step / steps
            bx = int(dish_x + 15 + t * (moon_center_x - radius - (dish_x + 15)))
            by = int(dish_y - t * (dish_y - moon_center_y))
            char_idx = int((t * 5 + pulse_pos) % len(beam_chars))
            safe_addch(stdscr, by, bx, beam_chars[char_idx], max_y, max_x)

        # 2.56-second light transit progress bar
        bounce_cycle = (time.time() % 2.56) / 2.56
        bar_len = max(10, min(26, max_x - 22))
        filled = int(bounce_cycle * bar_len)
        bar_str = "[" + "#" * filled + "-" * (bar_len - filled) + "]"

        label_x = max(2, max_x - bar_len - 4)
        stdscr.addstr(max_y - 3, label_x, "LUNAR TRANSIT (2.56s)"[: max_x - label_x - 1])
        stdscr.addstr(max_y - 2, label_x, bar_str[: max_x - label_x - 1])

        stdscr.refresh()

        angle = (angle + 1.2) % 360.0
        pulse_pos = (pulse_pos + 0.35) % 100.0
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
