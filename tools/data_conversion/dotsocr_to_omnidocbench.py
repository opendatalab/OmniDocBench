#!/usr/bin/env python3
"""
Convert Dots OCR aggregated JSON outputs into OmniDocBench-style entries.

The raw results file is expected to be a JSON object with a ``results`` list,
where each element contains an ``image_path`` and an ``output`` list of detected
objects, each including ``bbox`` coordinates, ``category``, and the recognised
``text``. This script converts that structure into the OmniDocBench format,
preserving labels and text content, and optionally upgrading markdown tables to
`Table` category labels.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "publicBench_data"

try:
    from PIL import Image  # type: ignore
except ImportError:
    Image = None

LOGGER = logging.getLogger(__name__)
MARKDOWN_TABLE_PATTERN = re.compile(r"\|.+\|\s*(?:\n\s*\|.+\|){1,}", re.MULTILINE)


@dataclass(frozen=True)
class PageMetadata:
    width: float
    height: float
    image_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Dots OCR JSON results into OmniDocBench dataset format."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to the raw dots_ocr_results_public.json file.",
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
        "--md-text-to-table",
        action="store_true",
        help=(
            "Detect markdown-style tables in Text elements and relabel them to Table. "
            "Logs the number of conversions performed."
        ),
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
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Interpret inputs as PDF outputs and rename images to {doc_id}_{page}.jpg while storing the PDF path.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=DATA_ROOT / "images",
        help="Directory containing rendered page images used when --pdf is enabled to scale bounding boxes.",
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


def infer_doc_page(image_path: str) -> Tuple[str, int]:
    image_name = Path(image_path).name
    stem = image_name.rsplit(".", 1)[0]
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
    image_path: str,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
) -> PageMetadata:
    if (doc_id, page_idx) in metadata_lookup:
        return metadata_lookup[(doc_id, page_idx)]
    image_name = Path(image_path).name
    LOGGER.debug(
        "Metadata missing for %s page %d, falling back to image name %s with unit dimensions.",
        doc_id,
        page_idx,
        image_name,
    )
    return PageMetadata(width=1.0, height=1.0, image_path=image_name)


def bbox_to_polygon(x1: float, y1: float, x2: float, y2: float) -> List[float]:
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def detect_markdown_table(text: Optional[str]) -> bool:
    if not text or not isinstance(text, str):
        return False
    match = bool(MARKDOWN_TABLE_PATTERN.search(text))
    if "|" in text and not match:
        LOGGER.debug("Table non cath: "+text)
    return match


def parse_original_dims(dimensions: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    if not dimensions or "x" not in dimensions:
        return None, None
    try:
        width_str, height_str = dimensions.lower().split("x", 1)
        return float(width_str), float(height_str)
    except ValueError:
        return None, None


def get_image_dimensions(
    image_path: Path,
    cache: Dict[Path, Tuple[Optional[float], Optional[float]]],
) -> Tuple[Optional[float], Optional[float]]:
    if image_path in cache:
        return cache[image_path]
    width: Optional[float] = None
    height: Optional[float] = None
    if Image is not None and image_path.exists():
        try:
            with Image.open(image_path) as img:
                width, height = float(img.width), float(img.height)
        except Exception:
            width = height = None
    cache[image_path] = (width, height)
    return cache[image_path]


def ensure_output_items(output: Optional[Iterable]) -> List[Dict]:
    """Normalise the `output` field into a list of dicts."""
    if isinstance(output, list):
        items = []
        for obj in output:
            if isinstance(obj, dict):
                items.append(obj)
        return items
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            LOGGER.warning("Failed to parse string output segment; skipping.")
            return []
        return ensure_output_items(parsed)
    if output is None:
        return []
    LOGGER.warning("Unexpected output type %s encountered; skipping.", type(output).__name__)
    return []


def convert_entry(
    entry: Dict,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
    md_to_table: bool,
    conversions: List[int],
) -> Dict:
    image_path = entry.get("image_path") or ""
    output_items = ensure_output_items(entry.get("output"))
    doc_id, page_idx = infer_doc_page(image_path)
    meta = resolve_page_metadata(doc_id, page_idx, image_path, metadata_lookup)

    layout_dets = []
    for idx, obj in enumerate(output_items, start=1):
        bbox = obj.get("bbox")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = map(float, bbox)
        except (TypeError, ValueError):
            continue
        polygon = bbox_to_polygon(x1, y1, x2, y2)
        category = obj.get("category", "unknown")
        text = obj.get("text")

        if md_to_table and category == "Text" and detect_markdown_table(text):
            conversions[0] += 1
            LOGGER.debug("Markdown table detected for %s page %d, converting to Table.", doc_id, page_idx)
            category = "Table"

        det = OrderedDict(
            [
                ("anno_id", idx),
                ("category_type", category),
                ("ignore", False),
                ("order", idx),
                ("poly", polygon),
                ("bbox", [x1, y1, x2, y2]),
            ]
        )

        if text:
            det["text"] = text

        layout_dets.append(det)

    page_info = OrderedDict(
        [
            ("image_path", meta.image_path),
            ("width", meta.width),
            ("height", meta.height),
            ("page_no", page_idx),
        ]
    )
    entry_out = OrderedDict(
        [
            ("layout_dets", layout_dets),
            ("extra", {"source_doc_id": doc_id}),
            ("page_info", page_info),
        ]
    )
    return entry_out


def convert_dotsocr(
    input_data: Dict,
    metadata_lookup: Dict[Tuple[str, int], PageMetadata],
    md_to_table: bool,
    pdf_mode: bool,
    images_dir: Optional[Path],
) -> List[Dict]:
    results = input_data.get("results") or []
    pdf_path = input_data.get("meta", {}).get("pdf_path")
    converted: List[Dict] = []
    conversions = [0]
    image_cache: Dict[Path, Tuple[Optional[float], Optional[float]]] = {}
    for entry in results:
        converted_entry = convert_entry(entry, metadata_lookup, md_to_table, conversions)
        if pdf_mode:
            doc_id = converted_entry["extra"]["source_doc_id"]
            converted_entry["page_info"]["page_no"] = entry["page_number"] if ".pdf" in entry["image_path"] else 0
            page_no = converted_entry["page_info"]["page_no"]
            new_image_name = f"{doc_id}_{page_no}.jpg"
            converted_entry["page_info"]["image_path"] = new_image_name
            pdf_path_entry = entry.get("image_path")
            converted_entry["page_info"]["pdf_path"] = pdf_path_entry or pdf_path
            pdf_width, pdf_height = parse_original_dims(entry.get("original_dims"))
            image_width = image_height = None
            if images_dir:
                candidate = images_dir / new_image_name
                image_width, image_height = get_image_dimensions(candidate, image_cache)

            width = image_width or pdf_width
            height = image_height or pdf_height
            if width is not None:
                converted_entry["page_info"]["width"] = width
            if height is not None:
                converted_entry["page_info"]["height"] = height

            scale_x = scale_y = 1.0
            if pdf_width and width:
                scale_x = width / pdf_width
            if pdf_height and height:
                scale_y = height / pdf_height

            if scale_x != 1.0 or scale_y != 1.0:
                for det in converted_entry["layout_dets"]:
                    bbox = det.get("bbox")
                    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                        det["bbox"] = [
                            float(bbox[0]) * scale_x,
                            float(bbox[1]) * scale_y,
                            float(bbox[2]) * scale_x,
                            float(bbox[3]) * scale_y,
                        ]
                    poly = det.get("poly")
                    if isinstance(poly, (list, tuple)) and len(poly) % 2 == 0:
                        scaled_poly: List[float] = []
                        for idx in range(0, len(poly), 2):
                            scaled_poly.append(float(poly[idx]) * scale_x)
                            scaled_poly.append(float(poly[idx + 1]) * scale_y)
                        det["poly"] = scaled_poly
        converted.append(converted_entry)
    if md_to_table:
        LOGGER.info("Markdown table conversions performed: %d", conversions[0])
    return converted


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.input_json.exists():
        raise FileNotFoundError(f"Input JSON not found: {args.input_json}")

    with args.input_json.open("r", encoding="utf-8") as input_file:
        try:
            input_data = json.load(input_file)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {args.input_json}") from exc

    metadata_lookup = load_reference_metadata(args.reference_json)
    converted_records = convert_dotsocr(
        input_data,
        metadata_lookup,
        args.md_text_to_table,
        args.pdf,
        args.images_dir if args.pdf else None,
    )

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Writing %d records to %s", len(converted_records), args.output_path)
    with args.output_path.open("w", encoding="utf-8") as output_file:
        json.dump(converted_records, output_file, indent=args.indent, ensure_ascii=False)
        output_file.write("\n")


if __name__ == "__main__":
    main()
