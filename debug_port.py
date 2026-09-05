#!/usr/bin/env python3
"""Low-level connectivity probe for a Phomemo D30 over a COM port.

Opens the port, sends the printer's init sequence one packet at a time, and
reports exactly what happens at each step (with timestamps) so a hang or
failure is visible immediately instead of the whole thing just freezing.

Usage:
    python debug_port.py --port COM3
"""

from __future__ import annotations

import argparse
import sys
import time

import serial

from d30 import protocol


def log(msg: str, start: float) -> None:
    print(f"[{time.monotonic() - start:6.2f}s] {msg}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="COM port, e.g. COM3")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--read-timeout", type=float, default=5.0, help="read timeout in seconds")
    parser.add_argument("--write-timeout", type=float, default=5.0, help="write timeout in seconds (prevents hanging forever)")
    parser.add_argument("--listen-after", type=float, default=2.0, help="seconds to listen for a reply after each packet")
    args = parser.parse_args()

    start = time.monotonic()

    log(f"Opening {args.port} @ {args.baud} baud (write_timeout={args.write_timeout}s)...", start)
    try:
        ser = serial.Serial(
            args.port,
            baudrate=args.baud,
            timeout=args.read_timeout,
            write_timeout=args.write_timeout,
        )
    except serial.SerialException as exc:
        log(f"FAILED to open port: {exc}", start)
        sys.exit(1)
    log("Port opened.", start)

    for name in ("cts", "dsr", "cd", "ri"):
        try:
            log(f"  line {name}: {getattr(ser, name)}", start)
        except Exception as exc:
            log(f"  line {name}: unreadable ({exc})", start)

    total_sent = 0
    total_received = 0

    packets = list(protocol.INIT_PACKETS)
    for i, packet in enumerate(packets, 1):
        log(f"Sending init packet {i}/{len(packets)}: {packet.hex()} ({len(packet)} bytes)...", start)
        try:
            n = ser.write(packet)
            ser.flush()
            total_sent += n
            log(f"  wrote {n} bytes OK.", start)
        except serial.SerialTimeoutException:
            log(
                f"  WRITE TIMED OUT after {args.write_timeout}s -- the OS accepted the port handle but "
                "never drained data to the device. This usually means the Bluetooth SPP link isn't "
                "actually connected (matches 'Driver unavailable' in Windows Bluetooth settings).",
                start,
            )
            break
        except serial.SerialException as exc:
            log(f"  WRITE FAILED: {exc}", start)
            break

        log(f"  listening for a reply for {args.listen_after}s...", start)
        deadline = time.monotonic() + args.listen_after
        got_any = False
        while time.monotonic() < deadline:
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                total_received += len(data)
                got_any = True
                log(f"  <<< received {len(data)} bytes: {data.hex()}", start)
            time.sleep(0.1)
        if not got_any:
            log("  (no reply)", start)

    ser.close()

    print()
    print(f"Summary: sent {total_sent} bytes, received {total_received} bytes.")
    if total_sent == 0:
        print(
            "Nothing was sent successfully -- the port never accepted data. This points at a "
            "Windows-side Bluetooth pairing/driver problem, not the script. Try removing and "
            "re-pairing the D30 in Bluetooth settings, and make sure it shows 'Connected' (not just "
            "'Paired') before retrying."
        )
    elif total_received == 0:
        print(
            "Data was sent but nothing came back -- that matches the known D30 protocol, which is "
            "one-way / fire-and-forget with no acknowledgement. That alone doesn't confirm the label "
            "actually printed, but it does confirm the COM port and pairing are working."
        )
    else:
        print(
            "The printer sent data back -- unexpected for this protocol, worth a closer look at the "
            "hex above."
        )


if __name__ == "__main__":
    main()
