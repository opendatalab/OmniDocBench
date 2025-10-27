#!/usr/bin/env python3
"""
Convert an AWS GroundTruth manifest into OmniDocBench JSON format.

The manifest is expected to be in JSON Lines format where each record includes one
or more annotation job outputs (label sets). A specific label set can be selected
via --label-set. If omitted, the converter uses the last label set present in each
record. Bounding boxes are transformed into OmniDocBench polygons and the label
names are preserved as provided by the manifest's class map.
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert AWS GroundTruth manifest into OmniDocBench dataset JSON."
    )
    parser.add_argument(
        "manifest_path",
        type=Path,
        help="Path to the input AWS GroundTruth manifest (JSON Lines).",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Destination path for the OmniDocBench JSON file.",
    )
    parser.add_argument(
        "--label-set",
        dest="label_set",
        help=(
            "Name of the label set to use from the manifest. If omitted, the last "
            "label set present on each record is used."
        ),
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for the output file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Silence progress logging.",
    )
    return parser.parse_args()


def select_label_set(record: Dict, preferred: Optional[str]) -> str:
    """Return the manifest key that holds the desired label set."""
    label_keys: List[str] = [
        key
        for key in record.keys()
        if key != "source-ref" and not key.endswith("-metadata")
    ]

    if not label_keys:
        raise ValueError("No label sets found in manifest record.")

    if preferred:
        if preferred not in record:
            raise KeyError(f"Label set '{preferred}' not found in manifest record.")
        return preferred

    # The manifest preserves insertion order; taking the last matches authoring time.
    return label_keys[-1]


def class_id_to_label(class_id: int, class_map: Dict[str, str]) -> str:
    """Lookup the human-readable label for a class id."""
    key = str(class_id)
    if class_map and key in class_map:
        return class_map[key]
    return key


def bbox_to_polygon(left: float, top: float, width: float, height: float) -> List[float]:
    """Convert axis-aligned bounding box to OmniDocBench polygon representation."""
    x1 = float(left)
    y1 = float(top)
    x2 = x1 + float(width)
    y2 = y1 + float(height)
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def convert_manifest_records(
    manifest_lines: Iterable[str], label_set: Optional[str]
) -> List[Dict]:
    """Convert all records from the manifest to OmniDocBench entries."""
    results: List[Dict] = []

    for line_no, raw_line in enumerate(manifest_lines, start=1):
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        record = json.loads(raw_line)
        label_key = select_label_set(record, label_set)
        metadata_key = f"{label_key}-metadata"

        label_payload = record.get(label_key)
        if label_payload is None:
            raise KeyError(f"Missing payload for label set '{label_key}' at line {line_no}.")

        metadata = record.get(metadata_key, {})
        class_map = metadata.get("class-map", {})

        image_sizes = label_payload.get("image_size", [])
        if not image_sizes:
            raise KeyError(f"Missing image size information at line {line_no}.")
        image_info = image_sizes[0]
        width = image_info.get("width")
        height = image_info.get("height")

        if width is None or height is None:
            raise KeyError(f"Width/height not present at line {line_no}.")

        annotations = label_payload.get("annotations", [])
        layout_dets = []
        for idx, anno in enumerate(annotations, start=1):
            class_id = anno.get("class_id")
            if class_id is None:
                raise KeyError(f"class_id missing for annotation #{idx} at line {line_no}.")

            left = anno.get("left")
            top = anno.get("top")
            box_width = anno.get("width")
            box_height = anno.get("height")

            if None in (left, top, box_width, box_height):
                raise KeyError(
                    f"Incomplete bounding box for annotation #{idx} at line {line_no}."
                )

            polygon = bbox_to_polygon(left, top, box_width, box_height)
            category_type = class_id_to_label(class_id, class_map)

            layout_det = OrderedDict(
                [
                    ("anno_id", idx),
                    ("category_type", category_type),
                    ("ignore", False),
                    ("order", idx),
                    ("poly", polygon),
                ]
            )
            layout_dets.append(layout_det)

        source_ref = record.get("source-ref", "")
        image_path = Path(source_ref).name if source_ref else f"line_{line_no:05d}.jpg"

        page_info = OrderedDict(
            [
                ("image_path", image_path),
                ("width", width),
                ("height", height),
                ("page_no", 0),
            ]
        )

        converted_record = OrderedDict(
            [
                ("layout_dets", layout_dets),
                ("extra", {}),
                ("page_info", page_info),
            ]
        )
        results.append(converted_record)

    return results


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {args.manifest_path}")

    LOGGER.info("Reading manifest from %s", args.manifest_path)
    with args.manifest_path.open("r", encoding="utf-8") as manifest_file:
        converted = convert_manifest_records(manifest_file, args.label_set)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Writing %d records to %s", len(converted), args.output_path)
    with args.output_path.open("w", encoding="utf-8") as output_file:
        json.dump(converted, output_file, indent=args.indent, ensure_ascii=False)
        output_file.write("\n")


if __name__ == "__main__":
    main()
