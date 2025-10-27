#!/usr/bin/env python3
"""
DocLayout-YOLO to GroundTruth conversion helper

Convert DocLayout-YOLO inference .txt files to an AWS SageMaker Ground Truth
input manifest (JSON Lines) with pre-annotations.

- Reads all .txt files in an input directory (one per image).
- Maps DocLayout-YOLO class IDs to your Ground Truth label set (from data_annotation_tool.json).
- Converts YOLO normalized xywh into pixel left/top/width/height required by Ground Truth.
- Writes a JSONL manifest with "source-ref" pointing to s3://{bucket}/{prefix}/{name}.jpg.
- Optionally fetches image size (W,H) from local images or from S3 to de-normalize boxes.
- Supports a confidence threshold to filter out low-confidence boxes.
- NEW: Deduplicates highly-overlapping boxes using IoU-based suppression (NMS-style).

Usage
-----
python dlyolo_to_groundtruth.py \
  --input-dir /path/to/yolo_txts \
  --data-annotation-tool /path/to/data_annotation_tool.json \
  --output /path/to/manifest.jsonl \
  --s3-prefix s3://ocr-regions-dataset/images \
  [--job-name doclayout-prelabels] \
  [--local-images-dir /path/to/images] \
  [--fetch-s3-dims] \
  [--map-abandon-to footer] \
  [--conf-threshold 0.5] \
  [--iou-threshold 0.9]

Notes
-----
* DocLayout-YOLO classes (id_to_names):
    0: title
    1: plain text
    2: abandon
    3: figure
    4: figure_caption
    5: table
    6: table_caption
    7: table_footnote
    8: isolate_formula
    9: formula_caption

* YOLO prediction .txt lines are typically: class x_center y_center width height [confidence]
  All coords are normalized [0,1]. This script expects the "confidence" (if present) to be the
  last value. If your files are in a different order, use --format class-conf-xywh to parse
  "class confidence x y w h".

* Handling of confidence:
  - If a line does NOT include confidence, it is treated as 1.0 (so it will pass any threshold <= 1.0).
  - Use --conf-threshold to filter: only boxes with confidence >= threshold are included.

* IoU-based suppression (NMS-style):
  - After confidence filtering and label mapping, we compute pairwise IoU across ALL remaining
    boxes (not per-class). If IoU > --iou-threshold (default 0.9), we keep the box with higher
    confidence and drop the other.
  - Greedy algorithm: sort boxes by confidence (desc) and keep a box if it doesn't exceed the
    IoU threshold with any already-kept box.
  - When confidences tie, earlier boxes in the sorted order are kept.

* "abandon" is a catch-all (headers/footers/page numbers/marginalia). By default we skip it.
  You can map it to a specific Ground Truth label via --map-abandon-to <label>.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Optional imports
try:
    from PIL import Image
except Exception:
    Image = None

try:
    import boto3  # only needed if you want to fetch image dims from S3
except Exception:
    boto3 = None

# ---------------------------
# DocLayout-YOLO class mapping
# ---------------------------
DOC_LAYOUT_ID_TO_NAME = {
    0: "title",
    1: "plain text",
    2: "abandon",
    3: "figure",
    4: "figure_caption",
    5: "table",
    6: "table_caption",
    7: "table_footnote",
    8: "isolate_formula",
    9: "formula_caption",
}

# These images must be skipped for the dataset
ignore_list = [
    "642e9610ed30fd5af1dea300_0",
    "64108bfccb901bc68b892070_1",
    "642e9e4ea3926c3c2b6bc289_0",
    "642ec7cf95a59120380dbf6f_0",
    "643ea3add4112bb1596ebd24_0",
    "6494045709ea90747cd9b1ee_0",
    "6494073709ea90747cd9c29b_0",
    "649951c10414def46174f69a_0",
    "652534724b365bf75de3be9a_0",
    "6544b0d5102b205ffdacffe5_0",
    "65538a06169b867ba844cfbc_0",
    "65faf6857c5dadf207da53c6_5",
    "660296ce289521448a565e25_1",
    "6602a8ff0f40f05b378a3ca3_0",
    "666aa590509b013396289bc4_1",
    "666aa590509b013396289bc4_4",
]

# These classes must be skipped for the dataset
ignore_classes = [
    "table",
]

# Map DocLayout-YOLO names -> canonical Ground Truth label names.
# You can customize these if your label taxonomy differs.
DEFAULT_NAME_TO_GT_LABEL = {
    "title": "title",
    "plain text": "text_block",
    "figure": "figure",
    "figure_caption": "figure_caption",
    "table": "table",
    "table_caption": "table_caption",
    "table_footnote": "table_footnote",
    "isolate_formula": "equation",
    "formula_caption": "equation_caption",
    # 'abandon' handled via CLI flag (--map-abandon-to) or skipped by default
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert DocLayout-YOLO txt predictions to Ground Truth manifest"
    )
    p.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Folder with YOLO .txt prediction files",
    )
    p.add_argument(
        "--data-annotation-tool",
        required=True,
        type=Path,
        help="Path to data_annotation_tool.json",
    )
    p.add_argument(
        "--output", required=True, type=Path, help="Path to write JSONL manifest"
    )
    p.add_argument(
        "--s3-prefix",
        default="s3://ocr-regions-dataset/images",
        help="S3 prefix to images (no trailing slash)",
    )
    p.add_argument(
        "--job-name",
        default="doclayout-prelabels",
        help="Attribute name to store annotations (arbitrary but consistent)",
    )
    p.add_argument(
        "--local-images-dir",
        type=Path,
        default=None,
        help="Optional local folder containing images (to read W,H)",
    )
    p.add_argument(
        "--fetch-s3-dims",
        action="store_true",
        help="Fetch image dimensions from S3 if local not found (requires boto3 + AWS creds)",
    )
    p.add_argument(
        "--map-abandon-to",
        type=str,
        default="text_block",
        help="Map 'abandon' predictions to this GT label (e.g., footer, page_number, watermark). If omitted, 'abandon' is dropped.",
    )
    p.add_argument(
        "--format",
        choices=["class-xywh-conf", "class-conf-xywh"],
        default="class-xywh-conf",
        help="Order of numbers per line. Default assumes conf is the last value.",
    )
    p.add_argument(
        "--image-ext",
        default=".jpg",
        help="Image extension to append on S3 URIs (default: .jpg)",
    )
    p.add_argument(
        "--conf-threshold",
        type=float,
        default=0.6,
        help="Only include boxes whose confidence >= threshold. If a line lacks confidence, it is treated as 1.0.",
    )
    p.add_argument(
        "--iou-threshold",
        type=float,
        default=0.75,
        help="IoU threshold for deduplicating overlapping boxes (keep higher confidence; drop the other).",
    )
    return p.parse_args()


def load_gt_labels(tool_json_path: Path) -> Tuple[List[str], Dict[str, int]]:
    """Read the AWS Ground Truth label list from data_annotation_tool.json"""
    tool = json.loads(tool_json_path.read_text(encoding="utf-8"))
    labels = [item["label"] for item in tool["labels"]]
    label_to_id = {label: idx for idx, label in enumerate(labels)}
    return labels, label_to_id


def s3_parse(uri: str) -> Tuple[str, str]:
    """Split s3://bucket/key -> (bucket, key)"""
    assert uri.startswith("s3://"), f"Not an S3 URI: {uri}"
    no_scheme = uri[len("s3://") :]
    bucket, _, key = no_scheme.partition("/")
    return bucket, key


def get_image_size(
    name: str,
    image_ext: str,
    local_images_dir: Optional[Path],
    s3_prefix: str,
    fetch_s3_dims: bool,
) -> Optional[Tuple[int, int, int]]:
    """
    Return (width, height, depth). Tries local path first, then S3 (if enabled).
    Returns None if size cannot be determined.
    """
    # Try local
    if Image is not None and local_images_dir is not None:
        local_path = local_images_dir / f"{name}{image_ext}"
        if local_path.exists():
            with Image.open(local_path) as im:
                w, h = im.size
                depth = len(im.getbands()) if hasattr(im, "getbands") else 3
            return int(w), int(h), int(depth)

    # Try S3
    if fetch_s3_dims:
        if boto3 is None:
            print(
                "WARNING: boto3 not installed; cannot fetch S3 image dims. Skipping dims for",
                name,
            )
            return None
        try:
            bucket, key_prefix = s3_parse(
                s3_prefix if not s3_prefix.endswith("/") else s3_prefix[:-1]
            )
            key = f"{key_prefix}/{name}{image_ext}"
            s3 = boto3.client("s3")
            obj = s3.get_object(Bucket=bucket, Key=key)
            if Image is None:
                print(
                    "WARNING: Pillow not installed; cannot read image dims from S3 bytes. Install pillow."
                )
                return None
            from io import BytesIO

            with Image.open(BytesIO(obj["Body"].read())) as im:
                w, h = im.size
                depth = len(im.getbands()) if hasattr(im, "getbands") else 3
            return int(w), int(h), int(depth)
        except Exception as e:
            print(f"WARNING: Unable to fetch S3 image dims for {name}{image_ext}: {e}")

    return None


def yolo_line_to_xywh(
    parts: List[str], fmt: str
) -> Tuple[int, float, float, float, float, Optional[float]]:
    """
    Parse one YOLO prediction line.
    Returns: (cls_id, x, y, w, h, conf_or_None)
    """
    if fmt == "class-xywh-conf":
        # class x y w h [conf?]
        if len(parts) < 5:
            raise ValueError(
                f"Invalid YOLO line (need at least 5 values): {' '.join(parts)}"
            )
        cls_id = int(float(parts[0]))
        x, y, w, h = map(float, parts[1:5])
        conf = float(parts[5]) if len(parts) >= 6 else None
        return cls_id, x, y, w, h, conf
    else:
        # class conf x y w h
        if len(parts) < 6:
            raise ValueError(
                f"Invalid YOLO line for class-conf-xywh: {' '.join(parts)}"
            )
        cls_id = int(float(parts[0]))
        conf = float(parts[1])
        x, y, w, h = map(float, parts[2:6])
        return cls_id, x, y, w, h, conf


def denorm_to_box(
    x: float, y: float, w: float, h: float, img_w: int, img_h: int
) -> Tuple[int, int, int, int]:
    """
    Convert YOLO normalized center-based xywh into left/top/width/height in integer pixels.
    Clamp to image boundaries.
    """
    left = round((x - w / 2.0) * img_w)
    top = round((y - h / 2.0) * img_h)
    bw = round(w * img_w)
    bh = round(h * img_h)

    # Clamp
    left = max(0, min(left, img_w - 1))
    top = max(0, min(top, img_h - 1))
    # Ensure width/height are at least 1 and stay within the image
    bw = max(1, min(bw, img_w - left))
    bh = max(1, min(bh, img_h - top))
    return int(left), int(top), int(bw), int(bh)


def box_iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """
    Compute IoU between two boxes defined as (left, top, width, height).
    """
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    inter_w = max(0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    if inter == 0:
        return 0.0

    area_a = aw * ah
    area_b = bw * bh
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def nms_greedy(
    annotations: List[dict], confidences: List[float], iou_thr: float
) -> Tuple[List[dict], List[float], int]:
    """
    Greedy NMS across all boxes regardless of class.
    Keeps the highest-confidence boxes and suppresses any with IoU > iou_thr w.r.t kept ones.

    Returns: (filtered_annotations, filtered_confidences, num_suppressed)
    """
    if not annotations:
        return annotations, confidences, 0

    # Prepare boxes list for IoU
    boxes = [(a["left"], a["top"], a["width"], a["height"]) for a in annotations]
    order = sorted(range(len(annotations)), key=lambda i: confidences[i], reverse=True)

    kept: List[int] = []
    suppressed = set()

    for i in order:
        if i in suppressed:
            continue
        keep = True
        for j in kept:
            if box_iou(boxes[i], boxes[j]) > iou_thr:
                keep = False
                break
        if keep:
            kept.append(i)
        else:
            suppressed.add(i)

    filtered_annotations = [annotations[i] for i in kept]
    filtered_confidences = [confidences[i] for i in kept]
    num_suppressed = len(annotations) - len(filtered_annotations)
    return filtered_annotations, filtered_confidences, num_suppressed


def main():
    args = parse_args()

    labels, label_to_id = load_gt_labels(args.data_annotation_tool)
    # Inverse map to include in metadata
    id_to_label = {str(i): name for i, name in enumerate(labels)}

    # Prepare mapping from DLYOLO class name -> GT label id
    name_to_gt = DEFAULT_NAME_TO_GT_LABEL.copy()
    abandon_label = args.map_abandon_to
    if abandon_label:
        if abandon_label not in label_to_id:
            raise SystemExit(
                f"--map-abandon-to '{abandon_label}' is not a valid Ground Truth label. "
                f"Valid labels from data_annotation_tool.json: {list(label_to_id)}"
            )
        name_to_gt["abandon"] = abandon_label

    # Verify that all mapped labels exist in the GT tool
    for src_name, tgt_label in name_to_gt.items():
        if tgt_label not in label_to_id:
            raise SystemExit(
                f"Target label '{tgt_label}' (for '{src_name}') not found in data_annotation_tool.json"
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    num_files = 0
    num_records = 0
    total_low_conf = 0
    total_suppressed = 0

    with args.output.open("w", encoding="utf-8") as fout:
        for txt_path in sorted(args.input_dir.glob("*.txt")):
            name = txt_path.stem  # image base name without extension
            if name in ignore_list:
                continue
            s3_uri = f"{args.s3_prefix.rstrip('/')}/{name}{args.image_ext}"

            # Try to get image size; required to de-normalize YOLO coordinates
            size = get_image_size(
                name,
                args.image_ext,
                args.local_images_dir,
                args.s3_prefix,
                args.fetch_s3_dims,
            )
            if size is None:
                print(
                    f"WARNING: Could not determine image size for {name}{args.image_ext}. Skipping."
                )
                continue
            img_w, img_h, depth = size

            annotations: List[dict] = []
            confidences: List[float] = []
            dropped = 0
            low_conf_skipped = 0

            with txt_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    try:
                        cls_id, x, y, w, h, conf = yolo_line_to_xywh(parts, args.format)
                    except Exception as e:
                        print(f"WARNING: Skipping line in {txt_path.name}: {e}")
                        continue

                    # Effective confidence (treat missing as 1.0)
                    conf_eff = float(conf) if conf is not None else 1.0
                    if conf_eff < args.conf_threshold:
                        low_conf_skipped += 1
                        continue

                    if cls_id in ignore_classes:
                        dropped += 1
                        continue

                    # Map to Ground Truth label
                    src_name = DOC_LAYOUT_ID_TO_NAME.get(cls_id, None)
                    if src_name is None:
                        print(
                            f"WARNING: Unknown class id {cls_id} in {txt_path.name} -- skipping."
                        )
                        continue

                    if src_name == "abandon" and "abandon" not in name_to_gt:
                        dropped += 1
                        continue  # skip abandon by default

                    gt_label = name_to_gt.get(src_name, None)
                    if gt_label is None:
                        dropped += 1
                        continue

                    gt_class_id = label_to_id[gt_label]

                    left, top, bw, bh = denorm_to_box(x, y, w, h, img_w, img_h)

                    annotations.append(
                        {
                            "class_id": gt_class_id,
                            "left": left,
                            "top": top,
                            "width": bw,
                            "height": bh,
                        }
                    )
                    confidences.append(conf_eff)

            if not annotations:
                # Nothing to write for this image but we need to print a message and write the image to the output
                if dropped > 0 or low_conf_skipped > 0:
                    print(
                        f"INFO: {txt_path.name}: no output (dropped={dropped}, low_conf_skipped={low_conf_skipped})."
                    )

            # IoU-based suppression (NMS-style) across all boxes
            annotations, confidences, suppressed = nms_greedy(
                annotations, confidences, args.iou_threshold
            )
            total_suppressed += suppressed

            record = {
                "source-ref": s3_uri,
                args.job_name: {
                    "annotations": annotations,
                    "image_size": [{"width": img_w, "height": img_h, "depth": depth}],
                },
                f"{args.job_name}-metadata": {
                    "class-map": id_to_label,
                    "type": "groundtruth/object-detection",
                    "human-annotated": "no",
                    "confidence": confidences,
                },
            }

            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            num_records += 1
            num_files += 1
            total_low_conf += low_conf_skipped

    print(
        f"Done. Wrote {num_records} manifest lines from {num_files} .txt files to {args.output}"
    )
    print(
        f"Total low-confidence boxes skipped (< {args.conf_threshold}): {total_low_conf}"
    )
    print(f"Total boxes suppressed by IoU (>{args.iou_threshold}): {total_suppressed}")
    if "abandon" not in name_to_gt:
        print(
            "Note: 'abandon' predictions were skipped. Use --map-abandon-to <label> to include them."
        )
    else:
        print(f"Note: 'abandon' predictions were mapped to '{name_to_gt['abandon']}'.")


if __name__ == "__main__":
    main()
