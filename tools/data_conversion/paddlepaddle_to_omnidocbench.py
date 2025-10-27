#!/usr/bin/env python3
"""
Convert PP-Structure-V3 (PaddlePaddle DocLayout) per-page JSON outputs into
OmniDocBench-style prediction entries.

Each JSON file is expected to describe a single page with an ``input_path`` that
points to the corresponding image and a ``boxes`` list holding bounding boxes
with absolute coordinates and labels. The converter aggregates all files into a
single OmniDocBench JSON list, preserving labels and scores, and reusing
reference metadata when provided.
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageMetadata:
    width: float
    height: float
    image_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert PaddlePaddle PP-Structure DocLayout outputs into OmniDocBench JSON format."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing PP-Structure JSON files (one per page).",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Destination file for the generated OmniDocBench JSON.",
    )
    parser.add_argument(
        "--reference-json",
        type=Path,
        help=(
            "Optional OmniDocBench JSON file providing page metadata (width, height, "
            "image paths). When supplied, generated entries reuse those dimensions."
        ),
    )
    parser.add_argument(
        "--pattern",
        default="*.json",
        help="Glob pattern (relative to input_dir) used to select PP-Structure files.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation level for the output JSON.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational logging.",
    )
    return parser.parse_args()


def load_reference_metadata(reference_path: Optional[Path]) -> Dict[Tuple[str, int], PageMetadata]:
    metadata: Dict[Tuple[str, int], PageMetadata] = {}
    if not reference_path:
        return metadata

    LOGGER.info("Loading reference metadata from %s", reference_path)
    with reference_path.open("r", encoding="utf-8") as ref_file:
        try:
            reference_data = json.load(ref_file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in reference file {reference_path}") from exc

    for entry in reference_data:
        page_info = entry.get("page_info") or {}
        image_path = page_info.get("image_path")
        width = page_info.get("width")
        height = page_info.get("height")
        if not image_path:
            continue
        base, _, suffix = image_path.rpartition("_")
        if not suffix:
            continue
        page_part, _, _ = suffix.partition(".")
        try:
            page_idx = int(page_part)
        except ValueError:
            continue
        doc_id = base or image_path
        if width is None or height is None:
            continue
        metadata[(doc_id, page_idx)] = PageMetadata(width=width, height=height, image_path=image_path)

    LOGGER.info("Loaded metadata for %d pages", len(metadata))
    return metadata


def gather_input_files(input_dir: Path, pattern: str) -> List[Path]:
    files = sorted(path for path in input_dir.rglob(pattern) if path.is_file())
    LOGGER.info("Discovered %d PP-Structure JSON files", len(files))
    return files


def bbox_to_polygon(x1: float, y1: float, x2: float, y2: float) -> List[float]:
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def infer_doc_page(json_path: Path) -> Tuple[str, int]:
    stem = json_path.stem  # e.g. 68f0eadcfcc7ebaa042738ac_0
    if "_" not in stem:
        return stem, 0
    doc_id, _, page_part = stem.rpartition("_")
    try:
        page_idx = int(page_part)
    except ValueError:
        page_idx = 0
    return doc_id, page_idx


def resolve_page_metadata(
    doc_id: str,
    page_idx: int,
    input_path: Optional[str],
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> PageMetadata:
    if (doc_id, page_idx) in metadata_lookup:
        return metadata_lookup[(doc_id, page_idx)]

    if input_path:
        image_name = Path(input_path).name
    else:
        image_name = f"{doc_id}_{page_idx}.jpg"
    LOGGER.debug(
        "Metadata missing for %s page %d, using fallback image name %s with unit dimensions.",
        doc_id,
        page_idx,
        image_name,
    )
    return PageMetadata(width=1.0, height=1.0, image_path=image_name)


def convert_pp_file(
    json_path: Path,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> Dict:
    LOGGER.debug("Processing %s", json_path)
    with json_path.open("r", encoding="utf-8") as file:
        try:
            payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"File {json_path} is not valid JSON.") from exc

    boxes = payload.get("boxes") or []
    input_path = payload.get("input_path")
    doc_id, page_idx = infer_doc_page(json_path)
    meta = resolve_page_metadata(doc_id, page_idx, input_path, metadata_lookup)

    layout_dets = []
    for idx, box in enumerate(boxes, start=1):
        coordinates = box.get("coordinate")
        if not coordinates or len(coordinates) != 4:
            continue
        x1, y1, x2, y2 = map(float, coordinates)
        polygon = bbox_to_polygon(x1, y1, x2, y2)
        det = OrderedDict(
            [
                ("anno_id", idx),
                ("category_type", box.get("label", "unknown")),
                ("ignore", False),
                ("order", idx),
                ("poly", polygon),
            ]
        )
        score = box.get("score")
        if isinstance(score, (float, int)):
            det["confidence"] = float(score)
        layout_dets.append(det)

    page_info = OrderedDict(
        [
            ("image_path", meta.image_path),
            ("width", meta.width),
            ("height", meta.height),
            ("page_no", page_idx),
        ]
    )
    entry = OrderedDict(
        [
            ("layout_dets", layout_dets),
            ("extra", {"source_doc_id": doc_id}),
            ("page_info", page_info),
        ]
    )
    return entry


def convert_directory(
    input_dir: Path,
    pattern: str,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> List[Dict]:
    records: List[Dict] = []
    for json_path in gather_input_files(input_dir, pattern):
        try:
            records.append(convert_pp_file(json_path, metadata_lookup))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Failed to convert %s: %s", json_path, exc)
            raise
    return records


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    metadata_lookup = load_reference_metadata(args.reference_json)
    converted_records = convert_directory(args.input_dir, args.pattern, metadata_lookup)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Writing %d records to %s", len(converted_records), args.output_path)
    with args.output_path.open("w", encoding="utf-8") as output_file:
        json.dump(converted_records, output_file, indent=args.indent, ensure_ascii=False)
        output_file.write("\n")


if __name__ == "__main__":
    main()
