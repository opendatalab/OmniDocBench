#!/usr/bin/env python3
"""
Generate visual previews for OCR load test responses.

Pipeline:
1. Extract `choices[0].message.content` Markdown from the JSON results.
2. Convert Markdown to HTML using Python standard-library helpers.
3. Parse the static HTML and render it into a PNG image.
4. Compose a side-by-side comparison between the original page image and
   the rendered preview (matching heights).

The script only relies on the Python standard library plus Pillow for image
drawing. No third-party Markdown or HTML rendering engines are used.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
DEFAULT_RESULTS_FILE = REPO_ROOT / "runs" / "load_tests" / "nanonets_run.json"
DEFAULT_IMAGE_DIR = DATA_ROOT / "publicBench_data" / "images"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "runs" / "load_tests" / "previews"
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


# --------------------------------------------------------------------------------------
# Markdown -> HTML conversion using only Python standard library
# --------------------------------------------------------------------------------------


class MarkdownToHtmlConverter:
    """Very small Markdown-to-HTML converter tailored to model outputs."""

    _MD_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)*\s*\|?\s*$")
    _BULLET_PATTERN = re.compile(r"^\s*[-*+]\s+(.*)")
    _ORDERED_PATTERN = re.compile(r"^\s*\d+\.\s+(.*)")

    def convert(self, markdown: str) -> str:
        text = self._normalise(markdown)
        lines = text.split("\n")

        html_parts: List[str] = []
        paragraph_buffer: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                self._flush_paragraph(paragraph_buffer, html_parts)
                i += 1
                continue

            if stripped.startswith("#"):
                self._flush_paragraph(paragraph_buffer, html_parts)
                level = len(stripped) - len(stripped.lstrip("#"))
                content = stripped[level:].strip()
                html_parts.append(f"<h{level}>{escape(content)}</h{level}>")
                i += 1
                continue

            if self._looks_like_markdown_table(lines, i):
                self._flush_paragraph(paragraph_buffer, html_parts)
                table_html, i = self._convert_markdown_table(lines, i)
                html_parts.append(table_html)
                continue

            if stripped.lower().startswith("<table"):
                self._flush_paragraph(paragraph_buffer, html_parts)
                table_html, i = self._collect_html_table(lines, i)
                html_parts.append(table_html)
                continue

            bullet_match = self._BULLET_PATTERN.match(line)
            ordered_match = self._ORDERED_PATTERN.match(line)
            if bullet_match:
                self._flush_paragraph(paragraph_buffer, html_parts)
                list_html, i = self._collect_list(lines, i, ordered=False)
                html_parts.append(list_html)
                continue
            if ordered_match:
                self._flush_paragraph(paragraph_buffer, html_parts)
                list_html, i = self._collect_list(lines, i, ordered=True)
                html_parts.append(list_html)
                continue

            paragraph_buffer.append(line)
            i += 1

        self._flush_paragraph(paragraph_buffer, html_parts)
        body = "\n".join(html_parts)
        return f'<div class="document">\n{body}\n</div>'

    @staticmethod
    def _normalise(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        replacements = {
            "</tabletable>": "</table>",
            "<tabletable>": "<table>",
            "<pagepage_number>": "<page_number>",
            "</pagepage_number>": "</page_number>",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        text = text.replace("<page_number>", '<p class="page-number">').replace("</page_number>", "</p>")
        return text

    @staticmethod
    def _flush_paragraph(buffer: List[str], html_parts: List[str]) -> None:
        if not buffer:
            return
        lines = [escape(line.strip()) for line in buffer if line.strip()]
        if not lines:
            buffer.clear()
            return
        paragraph = "<br/>".join(lines)
        html_parts.append(f"<p>{paragraph}</p>")
        buffer.clear()

    def _looks_like_markdown_table(self, lines: List[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False
        header = lines[index]
        separator = lines[index + 1]
        return "|" in header and self._MD_TABLE_SEPARATOR.match(separator or "")

    def _convert_markdown_table(self, lines: List[str], index: int) -> Tuple[str, int]:
        header_line = lines[index]
        separator_line = lines[index + 1]
        headers = [escape(cell.strip()) for cell in header_line.strip().strip("|").split("|")]
        column_count = len(headers)
        rows: List[List[str]] = []
        i = index + 2
        while i < len(lines):
            if not lines[i].strip():
                break
            if "|" not in lines[i]:
                break
            values = [escape(cell.strip()) for cell in lines[i].strip().strip("|").split("|")]
            if len(values) < column_count:
                values.extend([""] * (column_count - len(values)))
            elif len(values) > column_count:
                values = values[:column_count]
            rows.append(values)
            i += 1

        header_html = "<tr>" + "".join(f"<th>{cell}</th>" for cell in headers) + "</tr>"
        row_html = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
        table_html = f"<table>\n<thead>{header_html}</thead>\n<tbody>{row_html}</tbody>\n</table>"
        return table_html, i

    def _collect_html_table(self, lines: List[str], index: int) -> Tuple[str, int]:
        parts: List[str] = []
        depth = 0
        i = index
        while i < len(lines):
            line = lines[i]
            parts.append(line)
            depth += line.lower().count("<table")
            depth -= line.lower().count("</table")
            i += 1
            if depth <= 0:
                break
        return "\n".join(parts), i

    def _collect_list(self, lines: List[str], index: int, *, ordered: bool) -> Tuple[str, int]:
        items: List[str] = []
        matcher = self._ORDERED_PATTERN if ordered else self._BULLET_PATTERN
        i = index
        while i < len(lines):
            match = matcher.match(lines[i])
            if not match:
                break
            content = escape(match.group(1).strip())
            items.append(f"<li>{content}</li>")
            i += 1
        tag = "ol" if ordered else "ul"
        return f"<{tag}>" + "".join(items) + f"</{tag}>", i


# --------------------------------------------------------------------------------------
# HTML parsing into renderable blocks
# --------------------------------------------------------------------------------------


@dataclass
class HeadingBlock:
    level: int
    text: str


@dataclass
class ParagraphBlock:
    text: str
    css_class: Optional[str] = None


@dataclass
class ListBlock:
    items: List[str]
    ordered: bool


@dataclass
class TableBlock:
    headers: List[str]
    rows: List[List[str]]


ContentBlock = HeadingBlock | ParagraphBlock | ListBlock | TableBlock


class HtmlContentParser(HTMLParser):
    """Turn a very small subset of HTML into structured blocks."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: List[ContentBlock] = []
        self._text_buffer: Optional[List[str]] = None
        self._text_context: Optional[str] = None
        self._heading_level: Optional[int] = None
        self._paragraph_class: Optional[str] = None

        self._list_stack: List[Tuple[Optional[List[str]], bool]] = []
        self._current_list_items: Optional[List[str]] = None
        self._current_list_ordered: bool = False

        self._current_table: Optional[Dict[str, List[List[str]]]] = None
        self._current_row: Optional[List[str]] = None
        self._current_cell: Optional[List[str]] = None
        self._current_cell_is_header: bool = False
        self._row_is_header: bool = False

    # -- text helpers -----------------------------------------------------------------

    def _ensure_text_context(self, context: str, *, heading_level: Optional[int] = None, css_class: Optional[str] = None) -> None:
        if self._text_buffer is not None and self._text_context == context:
            return
        self._flush_paragraph()
        self._text_context = context
        self._heading_level = heading_level
        self._paragraph_class = css_class
        self._text_buffer = []

    def _append_text(self, text: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(text)
        elif self._text_buffer is not None:
            self._text_buffer.append(text)
        else:
            # Default to paragraph context if text appears at the root.
            self._ensure_text_context("paragraph")
            self._text_buffer.append(text)

    def _collect_text(self) -> str:
        if not self._text_buffer:
            return ""
        raw = "".join(self._text_buffer)
        raw = raw.replace("\r", "")
        # Preserve explicit line breaks while normalising interior whitespace.
        segments = [re.sub(r"[ \t]+", " ", segment).strip() for segment in raw.split("\n")]
        cleaned = "\n".join(segment for segment in segments if segment)
        self._text_buffer = None
        return cleaned

    def _flush_paragraph(self) -> None:
        if self._text_buffer is None:
            return
        context = self._text_context
        text = self._collect_text()
        css_class = self._paragraph_class
        self._text_context = None
        self._heading_level = None
        self._paragraph_class = None
        if not text:
            return
        if context == "heading":
            level = max(1, min(6, self._heading_level or 1))
            self.blocks.append(HeadingBlock(level=level, text=text))
        elif context == "paragraph":
            self.blocks.append(ParagraphBlock(text=text, css_class=css_class))

    # -- HTMLParser overrides ---------------------------------------------------------

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self._ensure_text_context("heading", heading_level=level)
        elif tag == "p":
            css_class = attr_dict.get("class")
            self._ensure_text_context("paragraph", css_class=css_class)
        elif tag in {"strong", "b", "em", "i", "span"}:
            # Inline tags do not change context; leave as-is.
            if self._text_buffer is None:
                self._ensure_text_context("paragraph")
        elif tag == "br":
            self._append_text("\n")
        elif tag == "ul":
            self._flush_paragraph()
            self._list_stack.append((self._current_list_items, self._current_list_ordered))
            self._current_list_items = []
            self._current_list_ordered = False
        elif tag == "ol":
            self._flush_paragraph()
            self._list_stack.append((self._current_list_items, self._current_list_ordered))
            self._current_list_items = []
            self._current_list_ordered = True
        elif tag == "li":
            if self._current_list_items is None:
                self._current_list_items = []
            self._ensure_text_context("list-item")
        elif tag == "table":
            self._flush_paragraph()
            self._current_table = {"headers": [], "rows": []}
        elif tag == "tr":
            if self._current_table is not None:
                self._current_row = []
                self._row_is_header = False
        elif tag == "th":
            if self._current_table is not None:
                self._current_cell = []
                self._current_cell_is_header = True
        elif tag == "td":
            if self._current_table is not None:
                self._current_cell = []
                self._current_cell_is_header = False

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_paragraph()
        elif tag == "p":
            self._flush_paragraph()
        elif tag == "li":
            text = self._collect_text()
            self._text_context = None
            self._heading_level = None
            self._paragraph_class = None
            if self._current_list_items is not None and text:
                self._current_list_items.append(text)
        elif tag in {"ul", "ol"}:
            if self._current_list_items is not None:
                self.blocks.append(
                    ListBlock(items=self._current_list_items, ordered=self._current_list_ordered)
                )
            if self._list_stack:
                self._current_list_items, self._current_list_ordered = self._list_stack.pop()
            else:
                self._current_list_items = None
                self._current_list_ordered = False
        elif tag in {"th", "td"}:
            if self._current_cell is not None and self._current_row is not None:
                cell_text = "".join(self._current_cell).replace("\r", "")
                cell_text = re.sub(r"[ \t]+", " ", cell_text)
                cell_text = re.sub(r"\n\s*", "\n", cell_text).strip()
                self._current_row.append(cell_text)
                if self._current_cell_is_header:
                    self._row_is_header = True
            self._current_cell = None
        elif tag == "tr":
            if self._current_table is not None and self._current_row is not None:
                if self._row_is_header and not self._current_table["headers"]:
                    self._current_table["headers"] = self._current_row
                else:
                    self._current_table["rows"].append(self._current_row)
            self._current_row = None
            self._row_is_header = False
        elif tag == "table":
            if self._current_table is not None:
                headers = self._current_table["headers"]
                rows = self._current_table["rows"]
                if headers and rows:
                    width = max(len(headers), max((len(row) for row in rows), default=0))
                    headers = (headers + [""] * width)[:width]
                    normalised_rows = []
                    for row in rows:
                        if len(row) < width:
                            row = row + [""] * (width - len(row))
                        elif len(row) > width:
                            row = row[:width]
                        normalised_rows.append(row)
                    rows = normalised_rows
                self.blocks.append(TableBlock(headers=headers, rows=rows))
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if not data.strip() and "\n" not in data:
            return
        self._append_text(data)

    def close(self) -> None:
        self._flush_paragraph()
        super().close()


# --------------------------------------------------------------------------------------
# Rendering utilities
# --------------------------------------------------------------------------------------


def _candidate_fonts() -> Iterable[Path]:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Helvetica.ttf"),
        Path("/System/Library/Fonts/Supplemental/Tahoma.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/Library/Fonts/Helvetica.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            yield candidate


def _load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    if bold:
        bold_candidates = [
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Helvetica Bold.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/Library/Fonts/Helvetica Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
        ]
        for candidate in bold_candidates:
            if candidate.exists():
                try:
                    return ImageFont.truetype(str(candidate), size=size)
                except OSError:
                    continue
    for candidate in _candidate_fonts():
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    if not text:
        ascent, descent = font.getmetrics()
        height = ascent + descent
        return 0, height
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    if not text:
        return [""]
    words = text.split()
    if not words:
        return [text]
    lines: List[str] = []
    current_words: List[str] = []
    for word in words:
        candidate = " ".join(current_words + [word])
        width, _ = _text_size(draw, candidate, font)
        if current_words and width > max_width:
            lines.append(" ".join(current_words))
            current_words = [word]
        else:
            current_words.append(word)
    if current_words:
        lines.append(" ".join(current_words))
    return lines or [""]


def _wrap_paragraph(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    segments = text.split("\n")
    wrapped: List[str] = []
    for idx, segment in enumerate(segments):
        if segment.strip():
            wrapped.extend(_wrap_text(draw, segment, font, max_width))
        else:
            wrapped.append("")
        if idx < len(segments) - 1:
            if not wrapped or wrapped[-1] != "":
                wrapped.append("")
    return wrapped or [""]


@dataclass
class RenderConfig:
    width: int = 900
    padding: int = 48
    block_spacing: int = 20
    line_spacing: int = 8
    list_indent: int = 36
    table_cell_padding: int = 12
    table_header_fill: Tuple[int, int, int] = (235, 240, 255)
    table_border_color: Tuple[int, int, int] = (200, 200, 210)
    text_color: Tuple[int, int, int] = (25, 25, 25)
    secondary_text_color: Tuple[int, int, int] = (110, 110, 120)


class HtmlRenderer:
    """Render parsed HTML blocks into a Pillow image."""

    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        self.body_font = _load_font(20)
        self.heading_fonts = {
            1: _load_font(34, bold=True),
            2: _load_font(28, bold=True),
            3: _load_font(24, bold=True),
            4: _load_font(22, bold=True),
            5: _load_font(20, bold=True),
            6: _load_font(20, bold=True),
        }
        self.list_font = self.body_font
        self.table_font = _load_font(19)
        self.page_number_font = _load_font(18, bold=True)
        self.measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    # Measurement helpers ------------------------------------------------------------

    def _line_height(self, font: ImageFont.ImageFont) -> int:
        ascent, descent = font.getmetrics()
        return ascent + descent + self.config.line_spacing

    def _measure_blocks(self, blocks: Sequence[ContentBlock]) -> int:
        y = self.config.padding
        for block in blocks:
            y = self._measure_block_height(block, y)
            y += self.config.block_spacing
        y += self.config.padding
        return max(y, self.config.padding * 2 + 100)

    def _measure_block_height(self, block: ContentBlock, y_start: int) -> int:
        content_width = self.config.width - self.config.padding * 2
        if isinstance(block, HeadingBlock):
            font = self.heading_fonts.get(block.level, self.heading_fonts[3])
            lines = _wrap_text(self.measure_draw, block.text, font, content_width)
            return y_start + len(lines) * self._line_height(font)
        if isinstance(block, ParagraphBlock):
            if block.css_class == "page-number":
                font = self.page_number_font
            else:
                font = self.body_font
            lines = _wrap_paragraph(self.measure_draw, block.text, font, content_width)
            return y_start + len(lines) * self._line_height(font)
        if isinstance(block, ListBlock):
            height = y_start
            for item in block.items:
                lines = _wrap_paragraph(
                    self.measure_draw,
                    item,
                    self.list_font,
                    content_width - self.config.list_indent,
                )
                height += len(lines) * self._line_height(self.list_font)
            return height
        if isinstance(block, TableBlock):
            return self._measure_table(block, y_start, content_width)
        return y_start

    def _measure_table(self, block: TableBlock, y_start: int, content_width: int) -> int:
        column_count = max(len(block.headers), *(len(row) for row in block.rows)) if (block.headers or block.rows) else 0
        if column_count == 0:
            return y_start
        col_width = max(1, (content_width - (column_count + 1) * 2) // column_count)
        line_height = self._line_height(self.table_font)
        total_height = 0
        rows = []
        if block.headers:
            rows.append(block.headers)
        rows.extend(block.rows)
        for cells in rows:
            row_height = 0
            for cell in cells:
                lines = _wrap_paragraph(
                    self.measure_draw,
                    cell,
                    self.table_font,
                    col_width - self.config.table_cell_padding * 2,
                )
                row_height = max(row_height, len(lines) * line_height + self.config.table_cell_padding * 2)
            total_height += row_height
        return y_start + total_height

    # Drawing ------------------------------------------------------------------------

    def render(self, blocks: Sequence[ContentBlock]) -> Image.Image:
        height = self._measure_blocks(blocks)
        image = Image.new("RGB", (self.config.width, height), color="white")
        draw = ImageDraw.Draw(image)
        y = self.config.padding
        for block in blocks:
            if isinstance(block, HeadingBlock):
                y = self._draw_heading(draw, y, block)
            elif isinstance(block, ParagraphBlock):
                y = self._draw_paragraph(draw, y, block)
            elif isinstance(block, ListBlock):
                y = self._draw_list(draw, y, block)
            elif isinstance(block, TableBlock):
                y = self._draw_table(draw, y, block)
            y += self.config.block_spacing
        return image

    def _draw_heading(self, draw: ImageDraw.ImageDraw, y: int, block: HeadingBlock) -> int:
        font = self.heading_fonts.get(block.level, self.heading_fonts[3])
        content_width = self.config.width - self.config.padding * 2
        lines = _wrap_text(draw, block.text, font, content_width)
        x = self.config.padding
        for line in lines:
            draw.text((x, y), line, font=font, fill=self.config.text_color)
            y += self._line_height(font)
        return y

    def _draw_paragraph(self, draw: ImageDraw.ImageDraw, y: int, block: ParagraphBlock) -> int:
        font = self.page_number_font if block.css_class == "page-number" else self.body_font
        text_color = self.secondary_text_color if block.css_class == "page-number" else self.config.text_color
        content_width = self.config.width - self.config.padding * 2
        lines = _wrap_paragraph(draw, block.text, font, content_width)
        x = self.config.padding
        for line in lines:
            draw.text((x, y), line, font=font, fill=text_color)
            y += self._line_height(font)
        return y

    def _draw_list(self, draw: ImageDraw.ImageDraw, y: int, block: ListBlock) -> int:
        bullet = "\u2022"
        content_width = self.config.width - self.config.padding * 2 - self.config.list_indent
        x_text = self.config.padding + self.config.list_indent
        x_bullet = self.config.padding
        for index, item in enumerate(block.items, start=1):
            lines = _wrap_paragraph(draw, item, self.list_font, content_width)
            bullet_text = f"{index}." if block.ordered else bullet
            draw.text((x_bullet, y), bullet_text, font=self.list_font, fill=self.config.text_color)
            for idx, line in enumerate(lines):
                draw.text((x_text, y), line, font=self.list_font, fill=self.config.text_color)
                y += self._line_height(self.list_font)
            if not lines:
                y += self._line_height(self.list_font)
        return y

    def _draw_table(self, draw: ImageDraw.ImageDraw, y: int, block: TableBlock) -> int:
        content_width = self.config.width - self.config.padding * 2
        column_count = max(len(block.headers), *(len(row) for row in block.rows)) if (block.headers or block.rows) else 0
        if column_count == 0:
            return y
        col_width = max(1, (content_width - (column_count + 1) * 2) // column_count)
        line_height = self._line_height(self.table_font)
        x_start = self.config.padding
        rows: List[Tuple[str, List[str]]] = []
        if block.headers:
            rows.append(("header", block.headers))
        rows.extend(("row", row) for row in block.rows)

        for row_type, cells in rows:
            cell_lines: List[List[str]] = []
            row_height = 0
            for cell in cells:
                lines = _wrap_paragraph(
                    draw,
                    cell,
                    self.table_font,
                    col_width - self.config.table_cell_padding * 2,
                )
                cell_lines.append(lines)
                row_height = max(
                    row_height,
                    len(lines) * line_height + self.config.table_cell_padding * 2,
                )
            x = x_start
            for lines in cell_lines:
                rect = [
                    (x, y),
                    (x + col_width, y + row_height),
                ]
                fill_color = self.config.table_header_fill if row_type == "header" else "white"
                draw.rectangle(rect, fill=fill_color, outline=self.config.table_border_color, width=1)
                text_y = y + self.config.table_cell_padding
                for line in lines:
                    draw.text(
                        (x + self.config.table_cell_padding, text_y),
                        line,
                        font=self.table_font,
                        fill=self.config.text_color,
                    )
                    text_y += line_height
                x += col_width + 2
            y += row_height
        return y


# --------------------------------------------------------------------------------------
# Image composition utilities
# --------------------------------------------------------------------------------------


def _load_image(path: Path) -> Image.Image:
    with Image.open(path) as img:
        return img.convert("RGB")


def _resize_to_height(image: Image.Image, target_height: int) -> Image.Image:
    if image.height == target_height:
        return image.copy()
    ratio = target_height / image.height
    new_width = max(1, int(image.width * ratio))
    return image.resize((new_width, target_height), Image.LANCZOS)


def _pad_to_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image
    canvas = Image.new("RGB", (width, image.height), color="white")
    offset_x = (width - image.width) // 2
    canvas.paste(image, (offset_x, 0))
    return canvas


def _pad_to_height(image: Image.Image, height: int) -> Image.Image:
    if image.height == height:
        return image.copy()
    canvas = Image.new("RGB", (image.width, height), color="white")
    canvas.paste(image, (0, 0))
    return canvas


def _compose_side_by_side(original: Image.Image, rendered: Image.Image, *, max_height: Optional[int] = None) -> Image.Image:
    target_render_height = min(rendered.height, original.height * 2)
    target_height = max(original.height, target_render_height)
    if max_height is not None and target_height > max_height:
        target_height = max_height

    if original.height > target_height:
        original_panel = _resize_to_height(original, target_height)
    else:
        original_panel = _pad_to_height(original, target_height)

    if rendered.height > target_height:
        rendered_panel = _resize_to_height(rendered, target_height)
    elif rendered.height < target_height:
        rendered_panel = _pad_to_height(rendered, target_height)
    else:
        rendered_panel = rendered.copy()

    resized_original = original_panel
    resized_rendered = rendered_panel
    panel_width = max(resized_original.width, resized_rendered.width)
    original_panel = _pad_to_width(resized_original, panel_width)
    rendered_panel = _pad_to_width(resized_rendered, panel_width)
    gutter = 48
    combined = Image.new("RGB", (panel_width * 2 + gutter, target_height), color="white")
    combined.paste(original_panel, (0, 0))
    combined.paste(rendered_panel, (panel_width + gutter, 0))
    return combined


# --------------------------------------------------------------------------------------
# CLI utilities
# --------------------------------------------------------------------------------------


def _extract_markdown(result: Dict) -> str:
    raw = result.get("raw_response", {})
    choices = raw.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            fragments = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    fragments.append(part.get("text", ""))
            return "\n\n".join(fragments)
    return result.get("response_text", "") or ""


@dataclass
class PreviewRecord:
    markdown_text: str
    image_path: Path
    output_stem: str
    display_name: str


def _build_image_lookup(image_dir: Path) -> Dict[str, Path]:
    lookup: Dict[str, Path] = {}
    if not image_dir.exists():
        return lookup
    for path in image_dir.iterdir():
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        lookup.setdefault(path.stem, path)
    return lookup


def _load_records_from_directory(results_dir: Path, image_dir: Path) -> List[PreviewRecord]:
    lookup = _build_image_lookup(image_dir)
    records: List[PreviewRecord] = []
    markdown_files = sorted(p for p in results_dir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".markdown"})
    for md_path in markdown_files:
        markdown_text = md_path.read_text(encoding="utf-8")
        if not markdown_text.strip():
            print(f"[dir] Skipping {md_path.name}: empty file.")
            continue
        candidate = lookup.get(md_path.stem)
        if candidate is None:
            for path in image_dir.glob(f"{md_path.stem}.*"):
                if path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
                    candidate = path
                    lookup[md_path.stem] = path
                    break
        if candidate is None:
            print(f"[dir] Skipping {md_path.name}: original image not found in {image_dir}.")
            continue
        records.append(
            PreviewRecord(
                markdown_text=markdown_text,
                image_path=candidate,
                output_stem=candidate.stem,
                display_name=md_path.name,
            )
        )
    return records


def _load_records_from_json(results_file: Path, image_dir: Path) -> List[PreviewRecord]:
    with results_file.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    records: List[PreviewRecord] = []
    for item in payload.get("results", []):
        if item.get("status") != "ok":
            continue
        image_name = item.get("image")
        if not image_name:
            continue
        image_path = image_dir / image_name
        if not image_path.exists():
            print(f"[json] Skipping {image_name}: original file not found in {image_dir}.")
            continue

        markdown_text = _extract_markdown(item)
        if not markdown_text.strip():
            print(f"[json] Skipping {image_name}: empty response.")
            continue

        records.append(
            PreviewRecord(
                markdown_text=markdown_text,
                image_path=image_path,
                output_stem=Path(image_name).stem,
                display_name=image_name,
            )
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render load test Markdown outputs into side-by-side PNG previews.",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="Path to the load test JSON file or directory of Markdown files (default: runs/load_tests/nanonets_run.json).",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=DEFAULT_IMAGE_DIR,
        help="Directory with original document images (default: data/publicBench_data/images).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to store preview images.",
    )
    parser.add_argument(
        "--render-width",
        type=int,
        default=900,
        help="Width (pixels) for the rendered Markdown preview.",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=None,
        help="Optional maximum height for the final side-by-side image.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Limit the number of records processed (useful for smoke tests).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.results_file.exists():
        raise FileNotFoundError(f"Results file {args.results_file} not found.")
    if not args.image_dir.exists():
        raise FileNotFoundError(f"Image directory {args.image_dir} not found.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir = args.output_dir / "markdown_previews"
    side_by_side_dir = args.output_dir / "side_by_side"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    side_by_side_dir.mkdir(parents=True, exist_ok=True)

    if args.results_file.is_dir():
        records = _load_records_from_directory(args.results_file, args.image_dir)
    else:
        records = _load_records_from_json(args.results_file, args.image_dir)
    if args.max_items is not None:
        records = records[: args.max_items]

    md_converter = MarkdownToHtmlConverter()
    renderer = HtmlRenderer(config=RenderConfig(width=args.render_width))

    for idx, record in enumerate(records, start=1):
        markdown_text = record.markdown_text
        html_text = md_converter.convert(markdown_text)
        parser = HtmlContentParser()
        parser.feed(html_text)
        parser.close()

        blocks = parser.blocks
        if not blocks:
            print(f"[{idx}] Skipping {record.display_name}: no renderable blocks.")
            continue

        rendered_image = renderer.render(blocks)
        markdown_output = markdown_dir / f"{record.output_stem}_markdown.png"
        rendered_image.save(markdown_output)

        original_image = _load_image(record.image_path)
        comparison = _compose_side_by_side(original_image, rendered_image, max_height=args.max_height)
        comparison_output = side_by_side_dir / f"{record.output_stem}_comparison.png"
        comparison.save(comparison_output)

        print(f"[{idx}] Rendered preview for {record.display_name} -> {comparison_output}")


if __name__ == "__main__":
    main()
