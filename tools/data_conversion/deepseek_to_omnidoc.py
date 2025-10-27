#!/usr/bin/env python3
"""
Convert DeepSeek OCR predictions into OmniDocBench format.

Example
-------
python tools/data_conversion/deepseek_to_omnidoc.py \\
    --input data/publicBench_data/predictions/raw/deepseek_ocr_results_public.json \\
    --output data/publicBench_data/predictions/deepseek.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "data/publicBench_data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform DeepSeek OCR results into OmniDocBench schema.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_ROOT / "predictions" / "raw" / "deepseek_ocr_results_public.json",
        help="Path to the DeepSeek raw OCR JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_ROOT / "predictions" / "deepseek.json",
        help="Destination OmniDocBench-formatted JSON file.",
    )
    return parser.parse_args()


def load_raw_predictions(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("DeepSeek OCR JSON must contain a list of page predictions.")
    return data


def bbox_to_poly(bbox: List[float]) -> List[float]:
    if not bbox or len(bbox) != 4:
        return []
    x1, y1, x2, y2 = map(float, bbox)
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def convert_page(entry: Dict[str, Any]) -> Dict[str, Any]:
    image_name = entry.get("image_name") or ""
    width = entry.get("width")
    height = entry.get("height")
    results = entry.get("results") or []

    layout_dets: List[Dict[str, Any]] = []
    for idx, det in enumerate(results, start=1):
        bbox_abs = det.get("bbox_abs") or []
        poly = bbox_to_poly(bbox_abs)
        category = det.get("category") or "unknown"
        text = det.get("text") or ""
        score = det.get("score", 1.0)

        layout_dets.append(
            {
                "anno_id": idx,
                "order": idx,
                "category_type": category,
                "block_type": category,
                "poly": poly,
                "bbox": [float(value) for value in bbox_abs] if bbox_abs else [],
                "score": float(score),
                "ignore": False,
                "line_with_spans": [],
                "content": text,
            }
        )

    return {
        "layout_dets": layout_dets,
        "extra": {
            "source_doc_id": image_name,
        },
        "page_info": {
            "image_path": image_name,
            "width": width,
            "height": height,
            "page_no": 0,
        },
    }


def main() -> int:
    args = parse_args()
    pages = load_raw_predictions(args.input)
    converted = [convert_page(page) for page in pages]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(converted, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(converted)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
