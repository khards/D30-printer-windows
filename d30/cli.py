"""Shared CLI helpers."""

from __future__ import annotations

import sys
from typing import Optional

from . import discovery


def resolve_port(explicit: Optional[str]) -> str:
    """Return `explicit` unchanged, or auto-detect a working COM port.

    Prints progress and exits the process with a clear message if
    detection fails or is ambiguous. For non-CLI callers (e.g. the API
    server), use discovery.resolve_port() instead, which raises rather
    than exiting.
    """
    if explicit is not None:
        return explicit

    print("No --port given, looking for the D30's outgoing Bluetooth port...")
    try:
        port = discovery.resolve_port(None)
    except discovery.PortResolutionError as exc:
        print(str(exc), file=sys.stderr)
        print("Run find_port.py or debug_port.py to diagnose, or pass --port explicitly.", file=sys.stderr)
        sys.exit(1)

    print(f"Using {port}")
    return port
