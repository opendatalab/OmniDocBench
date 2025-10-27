#!/usr/bin/env python3
"""
Convert MonkeyOCR JSONL predictions into the OmniDocBench layout schema.

Example
-------
python tools/data_conversion/monkeyocr_to_omnidoc.py \\
    --input data/publicBench_data/predictions/raw/monkeyocr_results.jsonl \\
    --images-dir data/publicBench_data/images \\
    --output data/publicBench_data/predictions/monkeyocr-pro-3b.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "data/publicBench_data"


try:
    from PIL import Image  # type: ignore
except ImportError:
    Image = None  # type: ignore[assignment]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform MonkeyOCR outputs to OmniDocBench format.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_ROOT / "predictions" / "raw" / "monkeyocr_results.jsonl",
        help="Path to the MonkeyOCR JSONL file.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=DATA_ROOT / "images",
        help="Directory containing the benchmark images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_ROOT / "predictions" / "monkeyocr-pro-3b.json",
        help="Destination path for the OmniDocBench-formatted predictions.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def bbox_to_poly(x1: float, y1: float, x2: float, y2: float) -> List[float]:
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def extract_text(block: Dict[str, Any]) -> str:
    pieces: List[str] = []
    for line in block.get("lines") or []:
        spans = line.get("spans") or []
        for span in spans:
            content = span.get("content")
            if content:
                pieces.append(content)
    return "\n".join(pieces).strip()


def extract_score(block: Dict[str, Any]) -> Optional[float]:
    for line in block.get("lines") or []:
        for span in line.get("spans") or []:
            score = span.get("score")
            if score is not None:
                try:
                    return float(score)
                except (TypeError, ValueError):
                    return None
    return None


def get_image_size(image_name: str, images_dir: Path, cache: Dict[str, Tuple[Optional[int], Optional[int]]]) -> Tuple[Optional[int], Optional[int]]:
    if image_name in cache:
        return cache[image_name]

    path = images_dir / image_name
    width: Optional[int] = None
    height: Optional[int] = None

    if Image is not None and path.exists():
        try:
            with Image.open(path) as img:
                width, height = int(img.width), int(img.height)
        except Exception:
            width = height = None

    cache[image_name] = (width, height)
    return cache[image_name]


def scale_bbox(bbox: Iterable[float], scale_x: float, scale_y: float) -> Optional[List[float]]:
    values = list(bbox)
    if len(values) != 4:
        return None
    x1, y1, x2, y2 = values
    return [
        float(x1) * scale_x,
        float(y1) * scale_y,
        float(x2) * scale_x,
        float(y2) * scale_y,
    ]


def convert_blocks(
    blocks: Iterable[Dict[str, Any]],
    start_index: int,
    scale_x: float,
    scale_y: float,
    block_type_override: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    converted: List[Dict[str, Any]] = []
    next_index = start_index
    for block in blocks:
        bbox = block.get("bbox")
        if not bbox:
            continue
        scaled_bbox = scale_bbox(bbox, scale_x, scale_y)
        if not scaled_bbox:
            continue
        block_type = block_type_override or block.get("type") or "unknown"
        text = extract_text(block)
        score = extract_score(block)

        det: Dict[str, Any] = {
            "anno_id": next_index,
            "order": next_index,
            "category_type": block_type,
            "block_type": block_type,
            "poly": bbox_to_poly(*scaled_bbox),
            "bbox": scaled_bbox,
            "ignore": block_type == "discarded",
            "line_with_spans": [],
            "content": text,
        }
        if score is not None:
            det["score"] = score
        converted.append(det)
        next_index += 1
    return converted, next_index


def convert_record(
    record: Dict[str, Any],
    images_dir: Path,
    size_cache: Dict[str, Tuple[Optional[int], Optional[int]]],
) -> List[Dict[str, Any]]:
    image_name = Path(record.get("image_path", "")).name
    results: List[Dict[str, Any]] = []

    pdf_infos = record.get("blocks", {}).get("pdf_info") or []
    for page_idx, page in enumerate(pdf_infos):
        preproc_blocks = page.get("preproc_blocks") or []
        discarded_blocks = page.get("discarded_blocks") or []
        page_size = page.get("page_size") or [None, None]
        width, height = get_image_size(image_name, images_dir, size_cache)
        raw_width, raw_height = (None, None)
        if isinstance(page_size, (list, tuple)) and len(page_size) == 2:
            raw_width = float(page_size[0]) if page_size[0] not in (None, 0) else None
            raw_height = float(page_size[1]) if page_size[1] not in (None, 0) else None
        if width is None and raw_width is not None:
            width = int(round(raw_width))
        if height is None and raw_height is not None:
            height = int(round(raw_height))

        scale_x = scale_y = 1.0
        if raw_width and width:
            scale_x = width / raw_width
        if raw_height and height:
            scale_y = height / raw_height

        layout_dets: List[Dict[str, Any]] = []
        next_index = 1

        converted_preproc, next_index = convert_blocks(
            preproc_blocks,
            start_index=next_index,
            scale_x=scale_x,
            scale_y=scale_y,
        )
        layout_dets.extend(converted_preproc)

        converted_discarded, next_index = convert_blocks(
            discarded_blocks,
            start_index=next_index,
            scale_x=scale_x,
            scale_y=scale_y,
            block_type_override="discarded",
        )
        layout_dets.extend(converted_discarded)

        results.append(
            {
                "layout_dets": layout_dets,
                "extra": {
                    "source_doc_id": image_name,
                    "status": record.get("status"),
                },
                "page_info": {
                    "image_path": image_name,
                    "width": width,
                    "height": height,
                    "page_no": page.get("page_idx", page_idx),
                },
            }
        )
    return results


def main() -> int:
    args = parse_args()
    records = load_jsonl(args.input)

    size_cache: Dict[str, Tuple[Optional[int], Optional[int]]] = {}
    converted: List[Dict[str, Any]] = []
    for record in records:
        converted.extend(convert_record(record, args.images_dir, size_cache))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(converted, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(converted)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
