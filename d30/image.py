"""Render label images for the Phomemo D30 (96 x 320 dot printhead)."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from .protocol import DOTS_PER_MM, LABEL_WIDTH_PX

DEFAULT_LABEL_LENGTH_PX = 320  # Phomemo's standard full-length label (40mm)

_MARGIN_LENGTH_PX = 16  # padding along the label's length (feed direction)
_MARGIN_WIDTH_PX = 8  # padding across the label's width (max 96px / 12mm -- the printhead's limit)


def mm_to_px(mm: float) -> int:
    return max(round(mm * DOTS_PER_MM), 1)


def render_text_label(
    text: str,
    *,
    font_path: Optional[str] = None,
    length_mm: Optional[float] = None,
) -> Image.Image:
    """Render `text` to a 1-bit-ready image for D30Printer.print_image().

    The printhead is a fixed 96px (12mm) wide regardless of label size, so
    only the length (feed direction) varies -- pass `length_mm` for
    anything other than Phomemo's standard 40mm label (e.g. 30 for a
    14x30mm label).

    Composed in landscape (label's long axis horizontal) so multi-line text
    reads naturally, then rotated 90 degrees into the printer's raster
    orientation (rows come off the head across the label's short edge).
    """
    length_px = mm_to_px(length_mm) if length_mm is not None else DEFAULT_LABEL_LENGTH_PX

    inner_w = max(length_px - _MARGIN_LENGTH_PX, 1)
    inner_h = max(LABEL_WIDTH_PX - _MARGIN_WIDTH_PX, 1)

    landscape = Image.new("L", (length_px, LABEL_WIDTH_PX), color=255)
    draw = ImageDraw.Draw(landscape)
    font = _fit_font(draw, text, font_path, inner_w, inner_h)
    draw.multiline_text(
        (length_px / 2, LABEL_WIDTH_PX / 2),
        text,
        font=font,
        fill=0,
        anchor="mm",
        align="center",
    )

    portrait = landscape.rotate(270, expand=True)
    assert portrait.size == (LABEL_WIDTH_PX, length_px)
    return portrait


def render_two_column_label(
    rows: List[Tuple[str, str]],
    *,
    font_path: Optional[str] = None,
    length_mm: Optional[float] = None,
) -> Image.Image:
    """Render `rows` (label, value) pairs as a table: labels right-aligned
    in a left column, values left-aligned in a right column, sharing one
    column boundary (e.g. "Batch" / "Best Before" lining up on the right,
    their values lining up on the left just after the gap).

    Same sizing rules as render_text_label() -- see there for `length_mm`.
    """
    length_px = mm_to_px(length_mm) if length_mm is not None else DEFAULT_LABEL_LENGTH_PX

    inner_w = max(length_px - _MARGIN_LENGTH_PX, 1)
    inner_h = max(LABEL_WIDTH_PX - _MARGIN_WIDTH_PX, 1)

    landscape = Image.new("L", (length_px, LABEL_WIDTH_PX), color=255)
    draw = ImageDraw.Draw(landscape)

    font, label_col_w, value_col_w, line_height = _fit_two_column_font(draw, rows, font_path, inner_w, inner_h)
    gap = max(round(font.size * 0.4), 4)
    total_w = label_col_w + gap + value_col_w
    total_h = line_height * len(rows)

    start_x = length_px / 2 - total_w / 2
    start_y = LABEL_WIDTH_PX / 2 - total_h / 2

    label_right_x = start_x + label_col_w
    value_left_x = label_right_x + gap

    for i, (label, value) in enumerate(rows):
        line_center_y = start_y + line_height * (i + 0.5)
        draw.text((label_right_x, line_center_y), label, font=font, fill=0, anchor="rm")
        draw.text((value_left_x, line_center_y), value, font=font, fill=0, anchor="lm")

    portrait = landscape.rotate(270, expand=True)
    assert portrait.size == (LABEL_WIDTH_PX, length_px)
    return portrait


def render_batch_label(
    batch: str,
    best_before: str,
    *,
    product: Optional[str] = None,
    font_path: Optional[str] = None,
    length_mm: Optional[float] = None,
) -> Image.Image:
    """Render a Batch/Best-Before label, optionally with a centered,
    underlined product line above the batch table.

    Layout in readable orientation:

        [      This is the product name      ]
        [             Batch: 123123123       ]
        [      Best Before: 131-12-2026      ]

    The product line spans the full label width, is centered, and is
    underlined. The Batch/Best Before lines keep their familiar two-column
    alignment below it. Long product names only shrink the product font,
    not the batch/expiry text.
    """
    length_px = mm_to_px(length_mm) if length_mm is not None else DEFAULT_LABEL_LENGTH_PX

    rows = [("Batch:", batch), ("Best Before:", best_before)]
    if not product:
        return render_two_column_label(rows, font_path=font_path, length_mm=length_mm)

    # Compose in landscape so the readable layout maps directly to the canvas.
    landscape = Image.new("L", (length_px, LABEL_WIDTH_PX), color=255)
    draw = ImageDraw.Draw(landscape)

    # Split the landscape height: product gets the top ~45%, batch table the rest.
    product_h = max(round(LABEL_WIDTH_PX * 0.45), 1)
    table_h = LABEL_WIDTH_PX - product_h

    # Fit fonts independently so a long product name doesn't shrink the table.
    product_font = _fit_font(
        draw,
        product,
        font_path,
        max(length_px - _MARGIN_LENGTH_PX, 1),
        max(product_h - _MARGIN_WIDTH_PX, 1),
    )
    table_font, label_col_w, value_col_w, line_height = _fit_two_column_font(
        draw,
        rows,
        font_path,
        max(length_px - _MARGIN_LENGTH_PX, 1),
        max(table_h - _MARGIN_WIDTH_PX, 1),
    )

    # Product line: centered, underlined.
    draw.text(
        (length_px / 2, product_h / 2),
        product,
        font=product_font,
        fill=0,
        anchor="mm",
        align="center",
    )
    bbox = draw.textbbox((length_px / 2, product_h / 2), product, font=product_font, anchor="mm")
    underline_y = bbox[3] + max(round(product_font.size / 8), 1)
    draw.line([(bbox[0], underline_y), (bbox[2], underline_y)], fill=0, width=max(round(product_font.size / 10), 1))

    # Batch / Best Before table: centered in the remaining lower area.
    gap = max(round(table_font.size * 0.4), 4)
    total_w = label_col_w + gap + value_col_w
    total_h = line_height * len(rows)

    start_x = length_px / 2 - total_w / 2
    start_y = product_h + (table_h / 2 - total_h / 2)

    label_right_x = start_x + label_col_w
    value_left_x = label_right_x + gap

    for i, (label, value) in enumerate(rows):
        line_center_y = start_y + line_height * (i + 0.5)
        draw.text((label_right_x, line_center_y), label, font=table_font, fill=0, anchor="rm")
        draw.text((value_left_x, line_center_y), value, font=table_font, fill=0, anchor="lm")

    portrait = landscape.rotate(270, expand=True)
    assert portrait.size == (LABEL_WIDTH_PX, length_px)
    return portrait


def image_to_rows(image: Image.Image, threshold: int = 128) -> List[List[int]]:
    """Convert an image to rows of 0/1 pixels (1 = print dark), top to bottom."""
    if image.mode != "L":
        image = image.convert("L")

    width, height = image.size
    if width != LABEL_WIDTH_PX:
        raise ValueError(f"image width must be {LABEL_WIDTH_PX}px, got {width}")

    pixels = image.load()
    return [
        [1 if pixels[x, y] < threshold else 0 for x in range(width)]
        for y in range(height)
    ]


def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Optional[str], max_width: int, max_height: int) -> ImageFont.FreeTypeFont:
    size = max_height
    while size > 6:
        font = _load_font(font_path, size)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        if bbox[2] - bbox[0] <= max_width and bbox[3] - bbox[1] <= max_height:
            return font
        size -= 2
    return _load_font(font_path, 6)


def _fit_two_column_font(
    draw: ImageDraw.ImageDraw,
    rows: List[Tuple[str, str]],
    font_path: Optional[str],
    max_width: int,
    max_height: int,
) -> Tuple[ImageFont.FreeTypeFont, int, int, int]:
    size = max_height
    while size > 6:
        font = _load_font(font_path, size)
        label_col_w = max(_text_width(draw, label, font) for label, _ in rows)
        value_col_w = max(_text_width(draw, value, font) for _, value in rows)
        line_height = _line_height(draw, font)
        gap = max(round(size * 0.4), 4)
        total_w = label_col_w + gap + value_col_w
        total_h = line_height * len(rows)
        if total_w <= max_width and total_h <= max_height:
            return font, label_col_w, value_col_w, line_height
        size -= 1

    font = _load_font(font_path, 6)
    label_col_w = max(_text_width(draw, label, font) for label, _ in rows)
    value_col_w = max(_text_width(draw, value, font) for _, value in rows)
    line_height = _line_height(draw, font)
    return font, label_col_w, value_col_w, line_height


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _line_height(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return bbox[3] - bbox[1]


def _load_font(font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    candidates = [font_path] if font_path else ["arial.ttf", "DejaVuSans.ttf"]
    for name in candidates:
        if not name:
            continue
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()
