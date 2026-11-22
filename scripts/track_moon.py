#!/usr/bin/env python3
"""
Celestial Ephemeris Tracker (Pane 2)
Calculates real-time Moon Azimuth, Elevation, and slant range for Dwingeloo.
"""

import curses
import math
import time
import ephem

# CAMRAS Dwingeloo Radio Telescope coordinates
OBSERVER_LAT = "52.812"
OBSERVER_LON = "6.396"
OBSERVER_ELEV = 25  # meters
AU_TO_KM = 149597870.7


def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)

    station = ephem.Observer()
    station.lat = OBSERVER_LAT
    station.lon = OBSERVER_LON
    station.elevation = OBSERVER_ELEV

    moon = ephem.Moon()

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            break

        max_y, max_x = stdscr.getmaxyx()
        stdscr.erase()

        # Sanity check: verify pane dimensions before drawing
        if max_y < 13 or max_x < 42:
            stdscr.addstr(0, 0, "PANE TOO SMALL (MIN 42x13)")
            stdscr.refresh()
            time.sleep(0.5)
            continue

        station.date = ephem.now()
        moon.compute(station)

        az_deg = math.degrees(float(moon.az))
        el_deg = math.degrees(float(moon.alt))
        dist_km = float(moon.earth_distance) * AU_TO_KM
        rtt_sec = (dist_km * 2.0) / 299792.458

        status = "IN BEAM (ABOVE HORIZON)" if el_deg > 0.0 else "OCCLUDED (BELOW HORIZON)"

        stdscr.addstr(1, 2, "// CELESTIAL TARGET TRACKER : LUNA //", curses.A_BOLD)
        stdscr.addstr(2, 2, "========================================")
        stdscr.addstr(4, 2, f"STATION LOC  : {OBSERVER_LAT} N, {OBSERVER_LON} E")
        stdscr.addstr(5, 2, f"UTC EPOCH    : {station.date}")
        stdscr.addstr(7, 2, f"AZIMUTH (AZ) : {az_deg:06.2f} DEG")
        stdscr.addstr(8, 2, f"ELEVATION(EL): {el_deg:+06.2f} DEG")
        stdscr.addstr(9, 2, f"SLANT RANGE  : {dist_km:,.0f} KM")
        stdscr.addstr(10, 2, f"ECHO DELAY   : {rtt_sec:.3f} SEC")
        stdscr.addstr(11, 2, f"STATUS       : {status}")

        stdscr.refresh()
        time.sleep(1.0)


if __name__ == "__main__":
    curses.wrapper(main)
