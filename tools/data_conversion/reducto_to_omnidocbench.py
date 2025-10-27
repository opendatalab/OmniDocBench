#!/usr/bin/env python3
"""
Convert Reducto JSON outputs into an OmniDocBench-style dataset file.

Each Reducto JSON is expected to summarise the full document and contain the
parsed blocks for all pages under ``result.parse.result.chunks[*].blocks``. This
utility splits the document into per-page entries, converts bounding boxes into
OmniDoc polygons, and preserves the original block type, content, and
confidence. Optionally, a reference OmniDocBench JSON can be provided to reuse
page metadata (image paths, dimensions).
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageMetadata:
    width: float
    height: float
    image_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Reducto predictions into OmniDocBench JSON format."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing Reducto JSON files (one per document).",
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
        help="Glob pattern (relative to input_dir) used to pick Reducto files.",
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
    """Build a lookup from (doc_id, page_idx) to page metadata."""
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
    """Return a sorted list of JSON files to process."""
    files = sorted(path for path in input_dir.rglob(pattern) if path.is_file())
    LOGGER.info("Discovered %d Reducto JSON files", len(files))
    return files


def bbox_to_polygon(left: float, top: float, width: float, height: float) -> List[float]:
    """Convert axis-aligned bounding boxes to OmniDocBench polygon format."""
    x1 = float(left)
    y1 = float(top)
    x2 = x1 + float(width)
    y2 = y1 + float(height)
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def infer_doc_id(json_path: Path) -> str:
    """Derive the document identifier from the JSON filename."""
    return json_path.stem


def resolve_page_metadata(
    doc_id: str,
    page_idx: int,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> PageMetadata:
    """Fetch page metadata from reference lookup or fall back to defaults."""
    if (doc_id, page_idx) in metadata_lookup:
        return metadata_lookup[(doc_id, page_idx)]

    image_path = f"{doc_id}_{page_idx}.jpg"
    LOGGER.debug("Metadata missing for %s page %d, falling back to unit dimensions.", doc_id, page_idx)
    return PageMetadata(width=1.0, height=1.0, image_path=image_path)


def normalize_confidence(block: Dict) -> Optional[float]:
    """Return a numeric confidence when available."""
    granular = block.get("granular_confidence") or {}
    parse_conf = granular.get("parse_confidence")
    if isinstance(parse_conf, (float, int)):
        return float(parse_conf)
    return None


def convert_reducto_file(
    json_path: Path,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> List[Dict]:
    """Convert a single Reducto document JSON into per-page OmniDoc entries."""
    LOGGER.debug("Processing %s", json_path)
    with json_path.open("r", encoding="utf-8") as file:
        try:
            payload = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"File {json_path} is not valid JSON.") from exc

    parse_result = (
        payload.get("result", {})
        .get("parse", {})
        .get("result", {})
    )
    chunks = parse_result.get("chunks") or []

    pages = defaultdict(list)  # page_idx -> List[blocks]
    for chunk in chunks:
        for block in chunk.get("blocks", []):
            bbox = block.get("bbox") or {}
            page_number = bbox.get("page")
            if page_number is None:
                continue
            page_idx = int(page_number) - 1
            if page_idx < 0:
                page_idx = 0
            pages[page_idx].append(block)

    doc_id = infer_doc_id(json_path)
    converted_pages: List[Dict] = []

    for page_idx in sorted(pages.keys()):
        blocks = pages[page_idx]
        meta = resolve_page_metadata(doc_id, page_idx, metadata_lookup)
        layout_dets = []

        for idx, block in enumerate(blocks, start=1):
            bbox = block.get("bbox") or {}
            left = float(bbox.get("left", 0.0)) * meta.width
            top = float(bbox.get("top", 0.0)) * meta.height
            width = float(bbox.get("width", 0.0)) * meta.width
            height = float(bbox.get("height", 0.0)) * meta.height
            polygon = bbox_to_polygon(left, top, width, height)

            det = OrderedDict(
                [
                    ("anno_id", idx),
                    ("category_type", block.get("type", "unknown")),
                    ("ignore", False),
                    ("order", idx),
                    ("poly", polygon),
                ]
            )

            content = block.get("content")
            if content:
                det["text"] = content

            numeric_conf = normalize_confidence(block)
            if numeric_conf is not None:
                det["confidence"] = numeric_conf
            elif block.get("confidence") is not None:
                det["confidence_label"] = block["confidence"]

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
        LOGGER.warning("No pages produced for %s; the file might lack block data.", json_path)

    return converted_pages


def convert_directory(
    input_dir: Path,
    pattern: str,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> List[Dict]:
    """Convert every Reducto JSON file found in the directory tree."""
    records: List[Dict] = []
    for json_path in gather_input_files(input_dir, pattern):
        try:
            records.extend(convert_reducto_file(json_path, metadata_lookup))
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
