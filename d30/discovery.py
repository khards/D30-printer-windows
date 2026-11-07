"""Locate the D30's outgoing Bluetooth serial port on Windows."""

from __future__ import annotations

import re
import sys
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


def _windows_d30_ports() -> List[str]:
    if sys.platform != "win32":
        raise PortResolutionError("Automatic D30 discovery requires Windows; specify a COM port explicitly.")

    import winreg

    base = r"SYSTEM\CurrentControlSet\Enum\BTHENUM"
    addresses = set()
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as root:
            for index in range(winreg.QueryInfoKey(root)[0]):
                name = winreg.EnumKey(root, index)
                match = re.fullmatch(r"Dev_([0-9a-f]{12})", name, re.IGNORECASE)
                if not match:
                    continue
                with winreg.OpenKey(root, name) as device:
                    for child_index in range(winreg.QueryInfoKey(device)[0]):
                        with winreg.OpenKey(device, winreg.EnumKey(device, child_index)) as instance:
                            try:
                                friendly_name = winreg.QueryValueEx(instance, "FriendlyName")[0]
                            except FileNotFoundError:
                                continue
                            if isinstance(friendly_name, str) and friendly_name.strip().casefold() == "d30":
                                addresses.add(match.group(1).upper())
    except FileNotFoundError as exc:
        raise PortResolutionError("Windows Bluetooth device information is unavailable; pair the D30 first.") from exc
    except OSError as exc:
        raise PortResolutionError(f"Unable to read Windows Bluetooth device information: {exc}") from exc

    ports = set()
    for port in list_ports.comports():
        # Windows identifies outgoing SPP ports with the remote Bluetooth address;
        # incoming ports instead have an all-zero address.
        match = re.fullmatch(
            r"BTHENUM\\\{00001101-0000-1000-8000-00805F9B34FB\}_LOCALMFG&[0-9A-F]+"
            r"\\[^\\]*&([0-9A-F]{12})_C[0-9A-F]+",
            port.hwid or "",
            re.IGNORECASE,
        )
        if match and match.group(1).upper() in addresses:
            ports.add(port.device)
    return sorted(ports)


def resolve_port(explicit: Optional[str], write_timeout: float = 2.0) -> str:
    """Return `explicit` unchanged, or find the D30's outgoing Windows COM port.

    Raises PortResolutionError (rather than exiting) on failure/ambiguity,
    so this is safe to call from a long-running process like the API
    server -- see d30/cli.py for the version that prints and exits, for
    scripts.
    """
    if explicit is not None:
        return explicit

    working = _windows_d30_ports()
    if not working:
        raise PortResolutionError(
            "No outgoing Bluetooth COM port was found for a device named D30. Pair the printer "
            "and check More Bluetooth settings > COM Ports, or specify the outgoing port explicitly."
        )
    if len(working) > 1:
        raise PortResolutionError(
            f"Multiple outgoing D30 ports found: {', '.join(working)}. Specify one explicitly."
        )
    return working[0]
