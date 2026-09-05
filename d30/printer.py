"""Serial (COM port) connection to a Phomemo D30 label printer."""

from __future__ import annotations

import time

import serial
from PIL import Image

from . import protocol
from .image import image_to_rows


class D30Printer:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 10, write_timeout: float = 5):
        # Baud rate is largely ignored over Bluetooth SPP (it's a virtual
        # COM port), but pyserial requires a value. write_timeout matters:
        # pyserial's default (None) blocks forever if the RFCOMM link never
        # actually connects, which reads as a silent freeze -- see
        # debug_port.py if writes are timing out.
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=timeout, write_timeout=write_timeout)

    def close(self) -> None:
        self._serial.close()

    def __enter__(self) -> "D30Printer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def initialize(self) -> None:
        for packet in protocol.INIT_PACKETS:
            self._write(packet)
            time.sleep(0.05)

    def print_image(self, image: Image.Image) -> None:
        rows = image_to_rows(image)
        for chunk in protocol.build_print_job(rows):
            self._write(chunk)

    def print_copies(self, image: Image.Image, count: int = 1, pause: float = 0.25) -> None:
        """Print the same image `count` times.

        There's no cut command for die-cut labels on a continuous roll, so
        `pause` (seconds) is a gap between jobs to let the printer settle
        and advance to the next label before the next raster job starts.
        """
        for i in range(count):
            self.print_image(image)
            if i < count - 1 and pause > 0:
                time.sleep(pause)

    def _write(self, data: bytes) -> None:
        self._serial.write(data)
        self._serial.flush()
