#!/usr/bin/env python3
"""Adjust human-labelled text regions to match OCR word extents."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Sequence

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"

TARGET_CATEGORIES = {
    "text_block",
    "title",
    "footer",
    "header",
    "page_number",
    "caption",
    "footnote",
}
WORD_AREA_THRESHOLD = 0.80
IOU_THRESHOLD = 0.4


@dataclass(frozen=True)
class Rect:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def area(self) -> float:
        return self.width * self.height

    def intersection(self, other: "Rect") -> float:
        x_min = max(self.min_x, other.min_x)
        y_min = max(self.min_y, other.min_y)
        x_max = min(self.max_x, other.max_x)
        y_max = min(self.max_y, other.max_y)
        if x_max <= x_min or y_max <= y_min:
            return 0.0
        return (x_max - x_min) * (y_max - y_min)

    def iou(self, other: "Rect") -> float:
        inter = self.intersection(other)
        if inter == 0.0:
            return 0.0
        union = self.area + other.area - inter
        if union <= 0.0:
            return 0.0
        return inter / union

    def to_poly(self) -> List[float]:
        return [
            self.min_x,
            self.min_y,
            self.max_x,
            self.min_y,
            self.max_x,
            self.max_y,
            self.min_x,
            self.max_y,
        ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ocrs",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "ocrs",
        help="Directory with per-page OCR JSON files (default: %(default)s)",
    )
    parser.add_argument(
        "--gt",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "InvofoxBench.json",
        help="Ground-truth JSON file to refine (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "InvofoxBench_fixed.json",
        help="Where to write the refined ground-truth JSON (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with args.gt.open("r", encoding="utf-8") as handle:
        gt_items = json.load(handle)

    ocr_cache: dict[Path, List[Rect]] = {}
    updated_count = 0
    skipped_count = 0

    for item in gt_items:
        image_path = item.get("page_info", {}).get("image_path")
        if not image_path:
            continue

        page_width = float(item["page_info"].get("width", 0) or 0)
        page_height = float(item["page_info"].get("height", 0) or 0)

        if page_width <= 0 or page_height <= 0:
            print(
                f"[WARN] Invalid page dimensions for image={image_path}: "
                f"width={page_width}, height={page_height}"
            )
            continue

        ocr_file = (args.ocrs / Path(image_path).name).with_suffix(".json")
        word_rects = ocr_cache.get(ocr_file)
        if word_rects is None:
            try:
                word_rects = list(load_word_rects(ocr_file, page_width, page_height))
            except FileNotFoundError:
                print(f"[WARN] Missing OCR file: {ocr_file}")
                word_rects = []
            ocr_cache[ocr_file] = word_rects

        for det in item.get("layout_dets", []):
            if det.get("category_type") not in TARGET_CATEGORIES or det.get("ignore", False):
                continue

            region_rect = rect_from_poly(det.get("poly", []))
            if region_rect is None or region_rect.area == 0.0:
                continue

            matching_words: list[Rect] = []
            partial_matches: list[tuple[Rect, float]] = []
            for rect in word_rects:
                if rect.area <= 0.0:
                    continue
                intersection = rect.intersection(region_rect)
                if intersection <= 0.0:
                    continue
                coverage = intersection / rect.area
                if coverage >= WORD_AREA_THRESHOLD:
                    matching_words.append(rect)
                elif coverage >= 0.5:
                    partial_matches.append((rect, coverage))

            if partial_matches:
                skipped_count += 1
                sample_cov = ", ".join(f"{cov:.2f}" for _, cov in partial_matches[:3])
                if len(partial_matches) > 3:
                    sample_cov += ", ..."
                print(
                    f"[WARN] Partial OCR coverage ({sample_cov}) for region anno_id={det.get('anno_id')} "
                    f"category={det.get('category_type')} image={image_path}. Region left unchanged."
                )
                continue

            if not matching_words:
                skipped_count += 1
                print(
                    f"[INFO] No OCR words matched region anno_id={det.get('anno_id')} "
                    f"category={det.get('category_type')} image={image_path}"
                )
                continue

            new_rect = union_rects(matching_words)
            if new_rect.area == 0.0:
                skipped_count += 1
                print(
                    f"[INFO] Zero-area union for region anno_id={det.get('anno_id')} "
                    f"category={det.get('category_type')} image={image_path}"
                )
                continue

            overlap = new_rect.iou(region_rect)
            if overlap >= IOU_THRESHOLD:
                det["poly"] = new_rect.to_poly()
                updated_count += 1
            else:
                skipped_count += 1
                print(
                    f"[INFO] IoU {overlap:.2f} below threshold for region id={det.get('anno_id')} "
                    f"category={det.get('category_type')} image={image_path}"
                )

    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(gt_items, handle, ensure_ascii=False, indent=2)

    print(
        f"[INFO] Completed refinement: {updated_count} regions updated, "
        f"{skipped_count} regions skipped. Output written to {args.output}"
    )


def load_word_rects(path: Path, page_width: float, page_height: float) -> Iterator[Rect]:
    with path.open("r", encoding="utf-8") as handle:
        ocr = json.load(handle)

    ocr_width = float(ocr.get("width") or 0) or 1.0
    ocr_height = float(ocr.get("height") or 0) or 1.0

    scale_x = page_width / ocr_width if ocr_width else 1.0
    scale_y = page_height / ocr_height if ocr_height else 1.0
    rel_diff = abs(scale_x - scale_y) / max(scale_x, scale_y) if max(scale_x, scale_y) else 0.0
    if rel_diff < 1e-3:
        uniform = (scale_x + scale_y) / 2.0
        scale_x = scale_y = uniform

    for line in ocr.get("lines", []):
        for word in line.get("words", []):
            box = word.get("boundingBox") or word.get("bounding_box")
            if not box or len(box) < 8:
                continue
            rect = rect_from_points(box, scale_x, scale_y)
            if rect:
                yield rect


def rect_from_poly(poly: Sequence[float]) -> Rect | None:
    if not poly or len(poly) < 8:
        return None
    xs = poly[::2]
    ys = poly[1::2]
    return Rect(min(xs), min(ys), max(xs), max(ys))


def rect_from_points(points: Sequence[float], scale_x: float, scale_y: float) -> Rect | None:
    if len(points) < 8:
        return None

    xs = [points[i] * scale_x for i in range(0, len(points), 2)]
    ys = [points[i] * scale_y for i in range(1, len(points), 2)]
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)
    if max_x <= min_x or max_y <= min_y:
        return None
    return Rect(min_x, min_y, max_x, max_y)


def union_rects(rects: Sequence[Rect]) -> Rect:
    min_x = min(rect.min_x for rect in rects)
    min_y = min(rect.min_y for rect in rects)
    max_x = max(rect.max_x for rect in rects)
    max_y = max(rect.max_y for rect in rects)
    return Rect(min_x, min_y, max_x, max_y)


if __name__ == "__main__":
    main()
