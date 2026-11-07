#!/usr/bin/env python3
"""Install or remove the current user's Windows sign-in startup entry."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "remove"))
    args = parser.parse_args()
    if sys.platform != "win32":
        print("Startup registration requires Windows.", file=sys.stderr)
        return 1

    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    name = "D30 Print Server"
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if args.action == "install":
                command = subprocess.list2cmdline(
                    ["wscript.exe", str(Path(__file__).resolve().with_name("start_minimized.vbs"))]
                )
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
                print("D30 Print Server will start when this user signs in.")
            else:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    print("D30 Print Server was not registered for startup.")
                else:
                    print("D30 Print Server startup registration removed.")
    except OSError as exc:
        print(f"Could not update Windows startup registration: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
