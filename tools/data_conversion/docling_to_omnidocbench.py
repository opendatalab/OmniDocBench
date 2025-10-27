#!/usr/bin/env python3
"""
Convert DocTags predictions from Docling-Granite models into OmniDocBench layout JSON.

The script expects one DocTags dump per page, stored as text files whose base name
matches the source image (e.g., `foo.jpg` -> `foo.txt`). It reads an OmniDocBench
manifest to fetch page metadata (image path, width, height) and produces predictions
in the same JSON structure used by existing benchmark scripts.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

LOC_PATTERN = re.compile(
    r"<(?P<tag>[a-zA-Z0-9_]+)><loc_(?P<x1>\d+)>"
    r"<loc_(?P<y1>\d+)><loc_(?P<x2>\d+)><loc_(?P<y2>\d+)>(?P<content>[^<]*)"
)

# DocTags encode coordinates over a fixed grid of 0..500 (inclusive) per paper appendix A.4.
DEFAULT_LOC_GRID = 500


@dataclass
class DoclingElement:
    tag: str
    x1: int
    y1: int
    x2: int
    y2: int
    text: str

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Docling DocTags into OmniDocBench prediction JSON."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to OmniDocBench manifest JSON (list with page_info entries).",
    )
    parser.add_argument(
        "--docling-dir",
        required=True,
        type=Path,
        help=(
            "Directory with DocTags outputs. Each file must reuse the image relative "
            "path from the manifest, but with its extension swapped to .txt"
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination JSON path for OmniDocBench-formatted predictions.",
    )
    parser.add_argument(
        "--default-score",
        type=float,
        default=1.0,
        help="Score assigned to every region (DocTags do not produce confidences).",
    )
    parser.add_argument(
        "--loc-grid",
        type=int,
        default=DEFAULT_LOC_GRID,
        help="Coordinate grid size used by DocTags (default: 500).",
    )
    return parser.parse_args()


def load_manifest(manifest_path: Path) -> List[dict]:
    data = json.loads(manifest_path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Manifest must be a list, got {type(data)!r}")
    return data


def parse_docling_elements(raw_text: str) -> List[DoclingElement]:
    elements: List[DoclingElement] = []
    for match in LOC_PATTERN.finditer(raw_text):
        tag = match.group("tag")
        if not tag:
            continue
        try:
            x1 = int(match.group("x1"))
            y1 = int(match.group("y1"))
            x2 = int(match.group("x2"))
            y2 = int(match.group("y2"))
        except (TypeError, ValueError):
            continue
        text = match.group("content").strip()
        elements.append(DoclingElement(tag=tag, x1=x1, y1=y1, x2=x2, y2=y2, text=text))
    return elements


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def rect_from_locs(
    element: DoclingElement, width: float, height: float, loc_grid: int
) -> tuple[float, float, float, float]:
    """Scale DocTags grid coordinates back to pixel coordinates."""
    x_scale = width / loc_grid
    y_scale = height / loc_grid

    x1 = clamp(min(element.x1, element.x2) * x_scale, 0.0, width)
    x2 = clamp(max(element.x1, element.x2) * x_scale, 0.0, width)
    y1 = clamp(min(element.y1, element.y2) * y_scale, 0.0, height)
    y2 = clamp(max(element.y1, element.y2) * y_scale, 0.0, height)
    return x1, y1, x2, y2


def rect_to_poly(rect: Sequence[float]) -> List[float]:
    x1, y1, x2, y2 = rect
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def docling_tag_to_category(tag: str) -> Optional[str]:
    lowered = tag.lower()
    if lowered.startswith("section_header"):
        return "title"
    if lowered in {"text", "list_item", "ordered_list", "unordered_list", "code", "document_index"}:
        return "text_block"
    if lowered == "title":
        return "title"
    if lowered in {"picture", "chart"}:
        return "figure"
    if lowered == "caption":
        return "caption"  # resolved later into figure/table caption
    if lowered in {"footnote"}:
        return "page_footnote"
    if lowered == "page_header":
        return "header"
    if lowered == "page_footer":
        return "footer"
    if lowered == "page_number":
        return "page_number"
    if lowered == "otsl":
        return "table"
    if lowered in {"formula"}:
        return "equation"
    return None


def is_page_number_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    candidates = [
        r"^p(?:age|\.)?\s*\d+(\s*/\s*\d+)?$",
        r"^página\s*\d+(\s*/\s*\d+)?$",
        r"^\d+(\s*/\s*\d+)?$",
    ]
    return any(re.match(pattern, stripped, flags=re.IGNORECASE) for pattern in candidates)


def rect_center(rect: Sequence[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = rect
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def assign_caption_category(
    caption_rect: Sequence[float],
    figure_rects: Iterable[Sequence[float]],
    table_rects: Iterable[Sequence[float]],
) -> str:
    candidates: list[tuple[float, str]] = []
    cap_cx, cap_cy = rect_center(caption_rect)

    for rect in figure_rects:
        _, cy = rect_center(rect)
        candidates.append((abs(cap_cy - cy), "figure_caption"))

    for rect in table_rects:
        _, cy = rect_center(rect)
        candidates.append((abs(cap_cy - cy), "table_caption"))

    if not candidates:
        return "figure_caption"

    candidates.sort(key=lambda item: item[0])
    closest_distance, assigned = candidates[0]

    # If both figure and table are distant, default to figure caption.
    # Distance is measured in DocTags grid units scaled to pixels; use a lenient threshold.
    if closest_distance > 400:  # roughly a full page height, indicates uncertain pairing
        return "figure_caption"
    return assigned


def convert_elements_to_predictions(
    elements: Sequence[DoclingElement],
    page_info: dict,
    default_score: float,
    loc_grid: int,
) -> dict:
    width = page_info.get("width")
    height = page_info.get("height")
    if width is None or height is None:
        raise ValueError("page_info must include width and height")

    layout_dets: List[dict] = []
    table_rects: List[Sequence[float]] = []
    figure_rects: List[Sequence[float]] = []
    caption_indices: List[int] = []

    anno_id = 0
    for element in elements:
        category = docling_tag_to_category(element.tag)
        if category is None:
            continue

        rect = rect_from_locs(element, width, height, loc_grid)
        poly = rect_to_poly(rect)

        det = {
            "category_type": category,
            "poly": poly,
            "score": default_score,
            "ignore": False,
            "order": None,
            "anno_id": anno_id,
            "line_with_spans": [],
            "extra": {
                "docling_tag": element.tag,
                "text": element.text or None,
            },
        }

        if category == "table":
            table_rects.append(rect)
        elif category == "figure":
            figure_rects.append(rect)
        elif category == "caption":
            caption_indices.append(len(layout_dets))

        layout_dets.append(det)
        anno_id += 1

    # Resolve captions (figure vs table)
    for idx in caption_indices:
        rect = layout_dets[idx]["poly"]
        caption_rect = (
            rect[0],
            rect[1],
            rect[2],
            rect[5],
        )
        assigned = assign_caption_category(caption_rect, figure_rects, table_rects)
        layout_dets[idx]["category_type"] = assigned

    # Reclassify page numbers
    for det in layout_dets:
        if det["category_type"] == "footer":
            text = det["extra"].get("text") or ""
            if is_page_number_text(text):
                det["category_type"] = "page_number"

    return {
        "layout_dets": layout_dets,
        "extra": {},
        "page_info": page_info,
    }


def build_docling_path(docling_dir: Path, image_path: str) -> Path:
    image_relative = Path(image_path)
    docling_relative = image_relative.with_suffix(".txt")
    return docling_dir / docling_relative


def main() -> None:
    args = parse_args()

    manifest = load_manifest(args.manifest)
    docling_dir = args.docling_dir
    if not docling_dir.exists():
        raise FileNotFoundError(f"Docling directory not found: {docling_dir}")

    predictions: List[dict] = []
    for page in manifest:
        page_info = page.get("page_info")
        if not page_info:
            raise ValueError("Manifest entry missing page_info")

        image_path = page_info.get("image_path")
        if not image_path:
            raise ValueError("page_info missing image_path")

        docling_path = build_docling_path(docling_dir, image_path)
        if not docling_path.exists():
            raise FileNotFoundError(f"Missing Docling output for {image_path}: {docling_path}")

        raw_text = docling_path.read_text()
        elements = parse_docling_elements(raw_text)
        if not elements:
            raise ValueError(f"No DocTags elements found in {docling_path}")

        predictions.append(
            convert_elements_to_predictions(
                elements,
                page_info=page_info,
                default_score=args.default_score,
                loc_grid=args.loc_grid,
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(predictions, ensure_ascii=False))


if __name__ == "__main__":
    main()
