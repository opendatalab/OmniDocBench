#!/usr/bin/env python3
"""
Convert LandingAI JSON outputs into OmniDocBench-style prediction entries.

Each LandingAI JSON is assumed to contain the full-document prediction produced by
the provider, with per-element data under ``chunks`` including grounding boxes. The
converter splits the document into per-page records, converts the bounding boxes
into OmniDoc polygons (using optional reference metadata for dimensions), and keeps
the original labels as well as the associated markdown content.
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import OrderedDict, defaultdict
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
        description="Convert LandingAI predictions into OmniDocBench JSON format."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing LandingAI JSON files (one per document).",
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
        help="Glob pattern (relative to input_dir) used to select LandingAI files.",
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
    """Build a lookup from (doc_id, page_idx) to page metadata sourced from OmniDocBench JSON."""
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
    LOGGER.info("Discovered %d LandingAI JSON files", len(files))
    return files


def bbox_to_polygon(left: float, top: float, right: float, bottom: float) -> List[float]:
    """Convert a bounding box defined by corner coordinates into polynomial format."""
    return [left, top, right, top, right, bottom, left, bottom]


def infer_doc_id(json_path: Path) -> str:
    return json_path.stem


def resolve_page_metadata(
    doc_id: str,
    page_idx: int,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> PageMetadata:
    if (doc_id, page_idx) in metadata_lookup:
        return metadata_lookup[(doc_id, page_idx)]

    image_path = f"{doc_id}_{page_idx}.jpg"
    LOGGER.debug("Metadata missing for %s page %d, falling back to unit dimensions.", doc_id, page_idx)
    return PageMetadata(width=1.0, height=1.0, image_path=image_path)


def convert_landingai_file(
    json_path: Path,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> List[Dict]:
    LOGGER.debug("Processing %s", json_path)
    with json_path.open("r", encoding="utf-8") as file:
        try:
            payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"File {json_path} is not valid JSON.") from exc

    chunks = payload.get("chunks") or []
    doc_id = infer_doc_id(json_path)
    pages = defaultdict(list)

    for chunk in chunks:
        grounding = chunk.get("grounding") or {}
        page_number = grounding.get("page")
        box = grounding.get("box") or {}
        if page_number is None or not box:
            continue
        page_idx = int(page_number)
        pages[page_idx].append((chunk, box))

    converted_pages: List[Dict] = []

    for page_idx in sorted(pages.keys()):
        meta = resolve_page_metadata(doc_id, page_idx, metadata_lookup)
        layout_dets = []

        for idx, (chunk, box) in enumerate(pages[page_idx], start=1):
            left = float(box.get("left", 0.0)) * meta.width
            top = float(box.get("top", 0.0)) * meta.height
            right = float(box.get("right", 0.0)) * meta.width
            bottom = float(box.get("bottom", 0.0)) * meta.height
            polygon = bbox_to_polygon(left, top, right, bottom)

            det = OrderedDict(
                [
                    ("anno_id", idx),
                    ("category_type", chunk.get("type", "unknown")),
                    ("ignore", False),
                    ("order", idx),
                    ("poly", polygon),
                ]
            )

            markdown = chunk.get("markdown")
            if markdown:
                det["text"] = markdown

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
        converted_pages.append(entry)

    if not converted_pages:
        LOGGER.warning("No pages produced for %s; the file might lack chunk data.", json_path)

    return converted_pages


def convert_directory(
    input_dir: Path,
    pattern: str,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> List[Dict]:
    records: List[Dict] = []
    for json_path in gather_input_files(input_dir, pattern):
        try:
            records.extend(convert_landingai_file(json_path, metadata_lookup))
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
