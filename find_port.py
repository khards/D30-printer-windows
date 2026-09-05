#!/usr/bin/env python3
"""Scan COM ports to find one that accepts the D30 init sequence.

By default, brute-forces a numeric range (COM1..COM8) since that's the
fastest way to check "is anything listening here". Pass --listed to
instead probe only the ports Windows currently enumerates (shows their
descriptions too, useful for telling Bluetooth ports apart from others).

The D30 never replies (one-way protocol), so "accepted" here means the OS
took the write without timing out -- a strong signal the port has a live
connection behind it, not 100% proof it's specifically a D30.
"""

from __future__ import annotations

import argparse
import sys

from d30 import discovery


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--range", metavar="START-END", default="1-8", help="COM<START>..COM<END> to probe (default: 1-8)")
    parser.add_argument("--listed", action="store_true", help="probe only ports Windows currently lists, instead of a numeric range")
    parser.add_argument("--write-timeout", type=float, default=2.0, help="seconds to wait per port before giving up")
    args = parser.parse_args()

    if args.listed:
        listed = discovery.list_candidate_ports()
        if not listed:
            print("Windows doesn't currently list any serial ports.")
            sys.exit(1)
        print("Ports Windows currently lists:")
        for p in listed:
            print(f"  {p.device}: {p.description}")
        candidates = [p.device for p in listed]
    else:
        start, end = (int(x) for x in args.range.split("-"))
        candidates = [f"COM{n}" for n in range(start, end + 1)]
        print(f"Probing COM{start}..COM{end}...")

    print()
    print(f"Sending the D30 init sequence to each (write_timeout={args.write_timeout}s)...")
    working = []
    for device in candidates:
        sys.stdout.write(f"  {device}: ")
        sys.stdout.flush()
        ok = discovery.probe_port(device, write_timeout=args.write_timeout)
        print("accepted data" if ok else "no response / timed out / unavailable")
        if ok:
            working.append(device)

    print()
    if not working:
        print(
            "No port accepted the init sequence. Check the printer is paired, powered on, and shows "
            "'Connected' (not just 'Paired') in Windows Bluetooth settings."
        )
        sys.exit(1)
    elif len(working) == 1:
        print(f"Found it: {working[0]}")
        print(f'Use it with: python print_text.py "..." --port {working[0]}')
    else:
        print(f"Multiple ports accepted data: {', '.join(working)}")
        print(
            "The D30 protocol has no reply, so this can't tell them apart automatically -- Windows "
            "usually creates both an Outgoing and an Incoming port per Bluetooth device; use the "
            "Outgoing one (check Bluetooth settings > More Bluetooth options > COM Ports), or just "
            "try printing on each."
        )


if __name__ == "__main__":
    main()
