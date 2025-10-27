#!/usr/bin/env python3
"""
Convert Marker OCR raw responses into the OmniDocBench prediction schema.

Example
-------
python tools/data_conversion/marker_to_omnidoc.py \\
    --input-dir data/publicBench_data/predictions/raw/marker \\
    --image-dir data/publicBench_data/images \\
    --output data/publicBench_data/predictions/marker.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "data/publicBench_data"


TAG_RE = re.compile(r"<[^>]+>")
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform Marker OCR JSON outputs into OmniDocBench format.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_ROOT / "predictions" / "raw" / "marker",
        help="Directory containing Marker OCR JSON responses.",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=DATA_ROOT / "images",
        help="Directory with the source page images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_ROOT / "predictions" / "marker.json",
        help="Destination OmniDocBench-formatted JSON file.",
    )
    return parser.parse_args()


def ensure_directory(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Expected directory but found file: {path}")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten_polygon(polygon: Iterable[Iterable[float]]) -> List[float]:
    flattened: List[float] = []
    for point in polygon:
        if not isinstance(point, Iterable):
            continue
        x, y = point
        flattened.extend([float(x), float(y)])
    return flattened


def html_to_text(html_snippet: Optional[str]) -> str:
    if not html_snippet:
        return ""
    text = TAG_RE.sub(" ", html.unescape(html_snippet))
    return " ".join(text.split())


def find_image(stem: str, image_dir: Path) -> Tuple[str, Optional[Path]]:
    for ext in SUPPORTED_EXTS:
        candidate = image_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate.name, candidate
    matches = list(image_dir.glob(f"{stem}.*"))
    if matches:
        match = matches[0]
        return match.name, match
    fallback = image_dir / f"{stem}.jpg"
    return fallback.name, fallback if fallback.exists() else None


def get_image_size(image_path: Optional[Path]) -> Tuple[Optional[int], Optional[int]]:
    if image_path is None or not image_path.exists():
        return None, None
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return None, None

    try:
        with Image.open(image_path) as img:
            return int(img.width), int(img.height)
    except Exception:  # noqa: BLE001
        return None, None


def derive_dimensions(
    data: Dict[str, Any],
    fallback_width: Optional[int],
    fallback_height: Optional[int],
) -> Tuple[Optional[int], Optional[int]]:
    page_info = data.get("chunks", {}).get("page_info") or {}
    if page_info:
        first_page = next(iter(page_info.values()))
        if isinstance(first_page, dict):
            bbox = first_page.get("bbox")
            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                x0, y0, x1, y1 = bbox
                width = int(round(float(x1) - float(x0)))
                height = int(round(float(y1) - float(y0)))
                return width, height
    return fallback_width, fallback_height


def build_layout_det(block: Dict[str, Any], index: int) -> Dict[str, Any]:
    polygon = block.get("polygon") or []
    poly = flatten_polygon(polygon) if polygon else []
    if not poly:
        bbox = block.get("bbox")
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            x0, y0, x1, y1 = bbox
            poly = [float(x0), float(y0), float(x1), float(y0), float(x1), float(y1), float(x0), float(y1)]

    html_content = block.get("html") or ""
    text_content = html_to_text(html_content)

    det: Dict[str, Any] = {
        "anno_id": index,
        "order": index,
        "category_type": block.get("block_type") or "unknown",
        "block_type": block.get("block_type") or "unknown",
        "ignore": False,
        "poly": poly,
        "bbox": block.get("bbox", []),
        "html": html_content,
        "content": text_content,
    }

    if block.get("id"):
        det["block_id"] = block["id"]

    return det


def convert_marker_doc(
    json_path: Path,
    image_dir: Path,
) -> Dict[str, Any]:
    marker_data = read_json(json_path)
    stem = json_path.stem
    image_name, image_path = find_image(stem, image_dir)
    img_width, img_height = get_image_size(image_path)
    width, height = derive_dimensions(marker_data, img_width, img_height)

    blocks = marker_data.get("chunks", {}).get("blocks") or []
    layout_dets = [build_layout_det(block, index + 1) for index, block in enumerate(blocks)]

    result: Dict[str, Any] = {
        "layout_dets": layout_dets,
        "extra": {
            "source_doc_id": stem,
            "status": marker_data.get("status"),
            "html": marker_data.get("html"),
            "markdown": marker_data.get("markdown"),
        },
        "page_info": {
            "image_path": image_name,
            "width": width,
            "height": height,
            "page_no": 0,
        },
    }

    if marker_data.get("metadata"):
        result["extra"]["metadata"] = marker_data["metadata"]
    if marker_data.get("json"):
        result["extra"]["structured_json"] = marker_data["json"]

    return result


def convert_directory(input_dir: Path, image_dir: Path) -> List[Dict[str, Any]]:
    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found under {input_dir}")

    converted = []
    for json_file in json_files:
        try:
            converted.append(convert_marker_doc(json_file, image_dir))
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Failed to convert {json_file.name}: {exc}", file=sys.stderr)
    return converted


def main() -> int:
    args = parse_args()
    try:
        ensure_directory(args.input_dir)
        ensure_directory(args.image_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Path validation error: {exc}", file=sys.stderr)
        return 1

    converted = convert_directory(args.input_dir, args.image_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(converted, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(converted)} entries to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
