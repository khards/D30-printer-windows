#!/usr/bin/env python3
"""Windows notification-area controller for the local print server."""

from __future__ import annotations

import argparse
import ctypes
import logging
import os
import sys
import threading
import webbrowser
from pathlib import Path


def message_box(message: str, title: str = "D30 Print Server") -> None:
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x40)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="open the print page after starting")
    args = parser.parse_args()

    log_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "D30PrintServer"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = (log_dir / "server.log").open("a", encoding="utf-8", buffering=1)
    except OSError as exc:
        message_box(f"Cannot open the D30 log file: {exc}")
        return 1
    sys.stdout = sys.stderr = log_file
    logging.basicConfig(stream=log_file, level=logging.INFO)

    try:
        import pystray
        from PIL import Image, ImageDraw
        from werkzeug.serving import make_server
        from server import app

        try:
            http_server = make_server("127.0.0.1", 8787, app, threaded=True)
        except (OSError, SystemExit) as exc:
            logging.error("Unable to start server: %s", exc)
            message_box("Could not start the print server. Another server may already be using port 8787.")
            return 1

        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((7, 18, 57, 48), radius=5, fill="#225ca8")
        draw.rectangle((17, 7, 47, 24), fill="#a5c9f3")
        draw.rectangle((17, 35, 47, 58), fill="white", outline="#225ca8", width=3)
        draw.ellipse((46, 26, 51, 31), fill="white")

        last_error = ["No print errors since the server started."]

        def notify_error(message: str) -> None:
            logging.error("Print failed: %s", message)
            last_error[0] = message
            try:
                icon.notify(message[:240], "D30 printing failed")
            except Exception:
                logging.exception("Could not display the print notification")

        def open_page(icon, item):
            webbrowser.open("http://127.0.0.1:8787/")

        def show_error(icon, item):
            message_box(last_error[0], "D30 - Last print error")

        def open_log(icon, item):
            os.startfile(str(log_dir / "server.log"))

        def quit_server(icon, item):
            icon.stop()

        icon = pystray.Icon(
            "d30_print_server",
            image,
            "D30 Print Server",
            menu=pystray.Menu(
                pystray.MenuItem("Open print page", open_page, default=True),
                pystray.MenuItem("Show last print error", show_error),
                pystray.MenuItem("Open log", open_log),
                pystray.MenuItem("Quit", quit_server),
            ),
        )
        app.config["PRINT_ERROR_CALLBACK"] = notify_error
        thread = threading.Thread(target=http_server.serve_forever, name="d30-http", daemon=True)
        thread.start()
        try:
            if args.open:
                open_page(None, None)
            icon.run()
        finally:
            app.config.pop("PRINT_ERROR_CALLBACK", None)
            http_server.shutdown()
            http_server.server_close()
            thread.join()
        return 0
    except Exception as exc:
        logging.exception("D30 tray application failed")
        message_box(f"The D30 print server could not run: {exc}\nSee {log_dir / 'server.log'} for details.")
        return 1
    finally:
        log_file.close()


if __name__ == "__main__":
    sys.exit(main())
