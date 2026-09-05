"""Locate the D30's COM port automatically.

The D30 protocol is one-way -- it never sends anything back -- so "is this
the right port" can't be answered by reading a reply. The best available
signal is whether the OS accepts a write without timing out: a port with no
live Bluetooth SPP connection behind it (e.g. the "Driver unavailable"
case) blocks on write forever, which is exactly the freeze this was built
to avoid. See debug_port.py for a step-by-step version of the same probe.
"""

from __future__ import annotations

from typing import List, NamedTuple, Optional

import serial
from serial.tools import list_ports

from . import protocol


class PortCandidate(NamedTuple):
    device: str
    description: str


def list_candidate_ports() -> List[PortCandidate]:
    """All serial ports Windows currently lists, Bluetooth-looking ones first."""
    ports = list(list_ports.comports())
    ports.sort(key=lambda p: 0 if "bluetooth" in (p.description or "").lower() else 1)
    return [PortCandidate(p.device, p.description or "") for p in ports]


def probe_port(device: str, write_timeout: float = 2.0) -> bool:
    """True if `device` accepts the printer's init bytes without timing out.

    This only proves *some* live serial link is behind the port -- not that
    it's specifically a D30 -- since the protocol has no acknowledgement.
    """
    try:
        with serial.Serial(device, baudrate=115200, timeout=1, write_timeout=write_timeout) as ser:
            for packet in protocol.INIT_PACKETS:
                ser.write(packet)
                ser.flush()
        return True
    except serial.SerialException:
        return False


def find_port(candidates: Optional[List[str]] = None, write_timeout: float = 2.0) -> List[str]:
    """Return the device names (out of `candidates`) that accepted the init sequence.

    Defaults to every port Windows currently lists.
    """
    if candidates is None:
        candidates = [p.device for p in list_candidate_ports()]
    return [device for device in candidates if probe_port(device, write_timeout=write_timeout)]


class PortResolutionError(RuntimeError):
    """Raised by resolve_port() when no port, or more than one, is found."""


def resolve_port(explicit: Optional[str], write_timeout: float = 2.0) -> str:
    """Return `explicit` unchanged, or auto-detect a single working COM port.

    Raises PortResolutionError (rather than exiting) on failure/ambiguity,
    so this is safe to call from a long-running process like the API
    server -- see d30/cli.py for the version that prints and exits, for
    scripts.
    """
    if explicit is not None:
        return explicit

    working = find_port(write_timeout=write_timeout)
    if not working:
        raise PortResolutionError(
            "No COM port accepted the D30 init sequence. Check it's paired, powered on, and shows "
            "'Connected' (not just 'Paired') in Windows Bluetooth settings."
        )
    if len(working) > 1:
        raise PortResolutionError(
            f"Multiple ports responded: {', '.join(working)}. Specify one explicitly "
            "(the D30 usually shows up as both an Outgoing and an Incoming port)."
        )
    return working[0]
