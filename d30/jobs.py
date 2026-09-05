"""High-level print jobs shared by the CLI scripts and the local API server."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PIL import Image

from .discovery import resolve_port
from .image import render_text_label, render_two_column_label
from .printer import D30Printer


def print_text(
    text: str,
    *,
    port: Optional[str] = None,
    font_path: Optional[str] = None,
    length_mm: Optional[float] = None,
    count: int = 1,
    pause_s: float = 0.25,
) -> str:
    """Render and print a free-text label. Returns the COM port used."""
    image = render_text_label(text, font_path=font_path, length_mm=length_mm)
    return _send(image, port, count, pause_s)


def print_batch(
    batch: str,
    best_before: str,
    *,
    port: Optional[str] = None,
    font_path: Optional[str] = None,
    length_mm: float = 30,
    count: int = 1,
    pause_s: float = 0.25,
) -> str:
    """Render and print a Batch/Best-Before label. Returns the COM port used."""
    rows: List[Tuple[str, str]] = [("Batch:", batch), ("Best Before:", best_before)]
    image = render_two_column_label(rows, font_path=font_path, length_mm=length_mm)
    return _send(image, port, count, pause_s)


def _send(image: Image.Image, port: Optional[str], count: int, pause_s: float) -> str:
    resolved = resolve_port(port)
    with D30Printer(resolved) as printer:
        printer.initialize()
        printer.print_copies(image, count=count, pause=pause_s)
    return resolved
