"""Low-level Phomemo D30 print protocol.

Reverse-engineered from the "Print Master" Android app's Bluetooth traffic
by the phomemo_d30 project (github.com/polskafan/phomemo_d30), which in
turn credits vivier/phomemo-tools and theacodes/phomemo_m02s.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List

LABEL_WIDTH_PX = 96  # dots across the printhead; fixed by the hardware, regardless of label width
MAX_CHUNK_ROWS = 255  # the row-count field in the raster header is one byte
DOTS_PER_MM = 8  # 203dpi

# Sent once, right after opening the port, before any image data.
INIT_PACKETS: tuple[bytes, ...] = tuple(
    bytes.fromhex(p)
    for p in (
        "1f1138",
        "1f11121f1113",
        "1f1109",
        "1f1111",
        "1f1119",
        "1f1107",
        "1f110a1f110202",
    )
)


def _image_header(width_px: int, height_px: int) -> bytes:
    """ESC/POS-style raster header: control code, page-init, mode, then
    width/height in dots as little-endian uint16s (width is in bytes)."""
    return (
        bytes.fromhex("1f1124001b401d763000")
        + (width_px // 8).to_bytes(2, "little")
        + height_px.to_bytes(2, "little")
    )


def _pack_row(row: Iterable[int]) -> bytes:
    """Pack a row of 0/1 pixels (MSB first) into bytes."""
    row = list(row)
    packed = bytearray((len(row) + 7) // 8)
    for i, pixel in enumerate(row):
        if pixel:
            packed[i // 8] |= 0x80 >> (i % 8)
    return bytes(packed)


def build_print_job(rows: List[List[int]]) -> Iterator[bytes]:
    """Yield the byte chunks to write to the printer for a 1-bit image.

    `rows` is a list of rows top-to-bottom, each a list of 0/1 pixels,
    LABEL_WIDTH_PX wide (1 = print dark). The printer's row-count field
    only holds one byte, so a label taller than MAX_CHUNK_ROWS is split
    into multiple writes; only the first carries the header, which
    declares the *total* label height.
    """
    total_height = len(rows)
    first = True
    for start in range(0, total_height, MAX_CHUNK_ROWS):
        chunk = rows[start : start + MAX_CHUNK_ROWS]
        packed = b"".join(_pack_row(r) for r in chunk)
        if first:
            yield _image_header(LABEL_WIDTH_PX, total_height) + packed
            first = False
        else:
            yield packed
