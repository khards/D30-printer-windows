#!/usr/bin/env python3
"""Print a text label on a Phomemo D30 label printer over Bluetooth SPP (COM port)."""

from __future__ import annotations

import argparse
import sys

from d30 import jobs
from d30.cli import resolve_port


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help='Label text. Use "\\n" for line breaks.')
    parser.add_argument("--port", default=None, help="COM port the printer is bound to, e.g. COM4. Auto-detected if omitted.")
    parser.add_argument("--font", default=None, help="Path to a TTF font file (defaults to Arial)")
    parser.add_argument("--length", type=float, default=None, help="Label length in mm, e.g. 30 for a 14x30mm label (default: 40, Phomemo's standard label)")
    parser.add_argument("--count", type=int, default=1, help="Number of copies to print (default: 1)")
    parser.add_argument("--pause-ms", type=float, default=250, help="Pause between copies in ms, for die-cut labels with no cut command (default: 250)")
    args = parser.parse_args()

    port = resolve_port(args.port)

    text = args.text.replace("\\n", "\n")

    try:
        jobs.print_text(
            text,
            port=port,
            font_path=args.font,
            length_mm=args.length,
            count=args.count,
            pause_s=args.pause_ms / 1000,
        )
    except Exception as exc:
        print(f"Failed to print: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Sent {args.count} cop{'y' if args.count == 1 else 'ies'} to printer.")


if __name__ == "__main__":
    main()
