import argparse
import csv
import json
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import yaml

# Avoid optional dependencies and Accelerate issues on macOS
os.environ.setdefault("NPY_DISABLE_MACOS_ACCELERATE", "1")
os.environ.setdefault("OMNIDOCBENCH_SKIP_END2END", "1")
os.environ.setdefault("OMNIDOCBENCH_SKIP_RECOG", "1")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DATA_ROOT = ROOT / "data"
AZURE_ROOT = DATA_ROOT / "publicBench_data" / "azure-ocr"

from utils.ocr_utils import poly2bbox  # noqa: E402
from utils.match_utils import (
    bbox_iou,
    union_box,
    compute_matches,
    load_azure_words,
)  # noqa: E402


def aggregate_results(per_doc: List[Dict[str, object]], eval_classes: Sequence[str]) -> Dict[str, object]:
    total_docs = len(per_doc)
    total_gt = 0
    total_pred = 0
    total_matches = 0
    total_fn = 0
    total_fp = 0
    total_iou = 0.0
    all_confusion: Dict[str, Dict[str, float]] = {}
    per_class_totals: Dict[str, float] = {cls: 0.0 for cls in eval_classes}
    per_class_failures: Dict[str, float] = {cls: 0.0 for cls in eval_classes}

    for doc in per_doc:
        total_gt += doc["num_gt"]
        total_pred += doc["num_pred"]
        total_matches += doc["total_matches"]
        total_fn += doc["false_negatives"]
        total_fp += doc["false_positives"]
        total_iou += doc["mean_iou"] * doc["total_matches"]

        confusion = doc["confusion"]
        for gt_class, pred_map in confusion.items():
            cls_conf = all_confusion.setdefault(gt_class, {})
            for pred_class, value in pred_map.items():
                cls_conf[pred_class] = cls_conf.get(pred_class, 0.0) + float(value)

        for cls, value in doc["per_class_totals"].items():
            per_class_totals[cls] = per_class_totals.get(cls, 0.0) + float(value)
        for cls, value in doc["per_class_failures"].items():
            per_class_failures[cls] = per_class_failures.get(cls, 0.0) + float(value)

    overall_mean_iou = total_iou / total_matches if total_matches else 0.0

    per_class_summary = {}
    for cls in eval_classes:
        total_cls = per_class_totals.get(cls, 0.0)
        failures_cls = per_class_failures.get(cls, 0.0)
        failure_rate = failures_cls / total_cls if total_cls > 0 else None
        confusion_row = all_confusion.get(cls, {})
        per_class_summary[cls] = {
            "gt_total": total_cls,
            "failures": failures_cls,
            "failure_rate": failure_rate,
            "confusion": confusion_row,
        }

    return {
        "documents": total_docs,
        "total_gt_boxes": total_gt,
        "total_pred_boxes": total_pred,
        "total_matches": total_matches,
        "total_false_negatives": total_fn,
        "total_false_positives": total_fp,
        "mean_iou": overall_mean_iou,
        "avg_false_negatives_per_document": total_fn / total_docs if total_docs else 0.0,
        "avg_false_positives_per_document": total_fp / total_docs if total_docs else 0.0,
        "per_class": per_class_summary,
        "confusion": all_confusion,
    }


def write_csv(output_path: Path, records: List[Dict[str, object]], eval_classes: Sequence[str]) -> None:
    fieldnames = [
        "document",
        "num_gt",
        "num_pred",
        "total_matches",
        "false_negatives",
        "false_positives",
        "mean_iou",
    ]
    for cls in eval_classes:
        fieldnames.append(f"gt_total_{cls}")
        fieldnames.append(f"failures_{cls}")
        fieldnames.append(f"failure_rate_{cls}")

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {
                "document": record["document"],
                "num_gt": record["num_gt"],
                "num_pred": record["num_pred"],
                "total_matches": record["total_matches"],
                "false_negatives": record["false_negatives"],
                "false_positives": record["false_positives"],
                "mean_iou": record["mean_iou"],
            }
            for cls in eval_classes:
                totals = record["per_class_totals"].get(cls, 0.0)
                failures = record["per_class_failures"].get(cls, 0.0)
                failure_rate = failures / totals if totals else None
                row[f"gt_total_{cls}"] = totals
                row[f"failures_{cls}"] = failures
                row[f"failure_rate_{cls}"] = failure_rate
            writer.writerow(row)


def _draw_dashed_line(draw, start, end, fill, width, dash_length=12, gap=6):
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        direction = 1 if y2 >= y1 else -1
        y = y1
        while (direction == 1 and y < y2) or (direction == -1 and y > y2):
            y_end = y + direction * dash_length
            if (direction == 1 and y_end > y2) or (direction == -1 and y_end < y2):
                y_end = y2
            draw.line((x1, y, x2, y_end), fill=fill, width=width)
            y = y_end + direction * gap
    elif y1 == y2:
        direction = 1 if x2 >= x1 else -1
        x = x1
        while (direction == 1 and x < x2) or (direction == -1 and x > x2):
            x_end = x + direction * dash_length
            if (direction == 1 and x_end > x2) or (direction == -1 and x_end < x2):
                x_end = x2
            draw.line((x, y1, x_end, y2), fill=fill, width=width)
            x = x_end + direction * gap
    else:
        draw.line((x1, y1, x2, y2), fill=fill, width=width)


def draw_dashed_rectangle(draw, box, fill, width=3, dash_length=12, gap=6):
    x1, y1, x2, y2 = [int(round(v)) for v in box]
    _draw_dashed_line(draw, (x1, y1), (x2, y1), fill, width, dash_length, gap)
    _draw_dashed_line(draw, (x2, y1), (x2, y2), fill, width, dash_length, gap)
    _draw_dashed_line(draw, (x2, y2), (x1, y2), fill, width, dash_length, gap)
    _draw_dashed_line(draw, (x1, y2), (x1, y1), fill, width, dash_length, gap)


def render_debug_image(
    image_path: Path,
    output_path: Path,
    metrics: Dict[str, object],
    gt_sample: Dict[str, object],
    pred_sample: Dict[str, object],
    class_names: Sequence[str],
    azure_words: Optional[Sequence[Sequence[float]]] = None,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for visualization. Install with `pip install pillow`.") from exc

    image = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    font = ImageFont.load_default()

    def draw_label(anchor, text, color):
        x, y = anchor
        bbox = draw.textbbox((x, y), text, font=font)
        draw.rectangle([bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2], fill=(255, 255, 255))
        draw.text((x, y), text, fill=color, font=font)

    if azure_words:
        for word_box in azure_words:
            x1, y1, x2, y2 = [int(round(v)) for v in word_box]
            draw.rectangle([x1, y1, x2, y2], fill=(128, 128, 128, 50), outline=None)

    error_color = (220, 20, 60)
    label_colors = {
        "text": (72, 181, 163),
        "figure": (60, 120, 216),
        "table": (252, 202, 70),
        "qr": (166, 206, 227),
    }
    default_colors = [(102, 194, 165), (255, 237, 160), (197, 224, 180)]

    false_negatives = len(metrics["unmatched_gt"])
    false_positives = len(metrics["unmatched_pred"])
    mean_iou = metrics["mean_iou"]
    confusion = metrics.get("confusion", {})
    confusion_total = 0.0
    confusion_off = 0.0
    for gt_label, pred_map in confusion.items():
        for pred_label, value in pred_map.items():
            val = float(value)
            confusion_total += val
            if pred_label != gt_label:
                confusion_off += val
    confusion_error = confusion_off / confusion_total if confusion_total else 0.0

    summary_text = (
        f"FP: {false_positives}  |  FN: {false_negatives}  |  IoU: {mean_iou:.3f}  |  Conf err: {confusion_error:.3f}"
    )
    draw_label((10, 10), summary_text, color=(0, 0, 0))

    for idx, match in enumerate(metrics["matches"]):
        gt_union = union_box(gt_sample["bboxes"], match["gt_indices"])
        pred_union = union_box(pred_sample["bboxes"], match["pred_indices"])
        if gt_union is None or pred_union is None:
            continue
        iou_val = bbox_iou(gt_union, pred_union)
        gt_labels = sorted({class_names[int(gt_sample["labels"][gi])] for gi in match["gt_indices"]})
        pred_labels = sorted({class_names[int(pred_sample["labels"][pi])] for pi in match["pred_indices"]})
        mismatch = gt_labels != pred_labels
        if mismatch:
            color = error_color
        else:
            color = None
            for label in gt_labels:
                color = label_colors.get(label)
                if color:
                    break
            if color is None:
                color = default_colors[idx % len(default_colors)]

        gt_coords = [int(round(v)) for v in gt_union]
        pred_coords = [int(round(v)) for v in pred_union]
        draw.rectangle(gt_coords, outline=color, width=3)
        draw_dashed_rectangle(draw, pred_coords, fill=color, width=3)

        if mismatch:
            for gi in match["gt_indices"]:
                sub_box = gt_sample["bboxes"][gi]
                draw.rectangle([int(round(v)) for v in sub_box], outline=color, width=1)
                cls = class_names[int(gt_sample["labels"][gi])]
                x2, y1 = int(round(sub_box[2])), int(round(sub_box[1]))
                draw_label((x2 - 80, y1 + 4), f"GT:{cls}", color=color)
            for pi in match["pred_indices"]:
                sub_box = pred_sample["bboxes"][pi]
                draw_dashed_rectangle(draw, sub_box, fill=color, width=1, dash_length=6, gap=4)
                cls = class_names[int(pred_sample["labels"][pi])]
                x2, y1 = int(round(sub_box[2])), int(round(sub_box[1]))
                draw_label((x2 - 100, y1 + 4), f"Pred:{cls}", color=color)

        label_text = f"{iou_val:.3f} {', '.join(gt_labels) or '—'} ({', '.join(pred_labels) or '—'})"
        anchor_x = int(round(min(gt_union[0], pred_union[0]))) + 4
        anchor_y = int(round(min(gt_union[1], pred_union[1]))) + 4
        draw_label((anchor_x, anchor_y), label_text, color=color)

    for gi in metrics["unmatched_gt"]:
        box = gt_sample["bboxes"][gi]
        color = error_color
        draw.rectangle([int(round(v)) for v in box], outline=color, width=3)
        cls = class_names[int(gt_sample["labels"][gi])]
        draw_label((int(round(box[0])) + 4, int(round(box[1])) + 4), f"FN: {cls}", color)

    for pi in metrics["unmatched_pred"]:
        box = pred_sample["bboxes"][pi]
        color = error_color
        draw_dashed_rectangle(draw, box, fill=color, width=3)
        cls = class_names[int(pred_sample["labels"][pi])]
        draw_label((int(round(box[0])) + 4, int(round(box[1])) + 4), f"FP: {cls}", color)

    output_path = output_path.with_suffix('.png')
    image = Image.alpha_composite(image, overlay)
    image.save(output_path, format='PNG')


def extract_annotations(
    sample: Dict[str, object],
    category_mapping: Dict[str, str],
    class_to_index: Dict[str, int],
    level_cfg: Dict[str, Sequence[str]],
) -> Tuple[List[List[float]], List[int], List[float]]:
    boxes: List[List[float]] = []
    labels: List[int] = []
    scores: List[float] = []

    block_set = set(level_cfg.get("block_level") or [])
    span_set = set(level_cfg.get("span_level") or [])

    for item in sample.get("layout_dets", []):
        cat = item.get("category_type")
        mapped = category_mapping.get(cat, cat)
        if mapped in class_to_index and mapped in block_set:
            boxes.append([float(v) for v in poly2bbox(item["poly"])])
            labels.append(class_to_index[mapped])
            scores.append(float(item.get("score", 1.0)))
        for span in item.get("line_with_spans", []):
            span_cat = span.get("category_type")
            mapped_span = category_mapping.get(span_cat, span_cat)
            if mapped_span in class_to_index and mapped_span in span_set:
                boxes.append([float(v) for v in poly2bbox(span["poly"])])
                labels.append(class_to_index[mapped_span])
                scores.append(float(span.get("score", 1.0)))

    return boxes, labels, scores


def build_sample_name(sample: Dict[str, object], basename: str, fallback_index: int) -> str:
    page_info = sample.get("page_info", {})
    image_path = page_info.get("image_path")
    if image_path:
        return image_path
    page_no = page_info.get("page_no", fallback_index)
    return f"{basename}_{page_no}"


def filter_gt_samples(
    samples: List[Dict[str, object]],
    dataset_cfg: Dict[str, object],
) -> List[Dict[str, object]]:
    filtered_types = dataset_cfg.get("filter")
    if not filtered_types:
        return samples

    result = []
    for sample in samples:
        page_info = sample.get("page_info", {})
        attributes = page_info.get("page_attribute", {}) or {}
        keep = True
        for key, value in filtered_types.items():
            if attributes.get(key) != value:
                keep = False
                break
        if keep:
            result.append(sample)
    return result


def load_ground_truths(
    dataset_cfg: Dict[str, object],
    label_classes: Sequence[str],
    level_cfg: Dict[str, Sequence[str]],
    category_mapping: Dict[str, str],
) -> Tuple[List[Dict[str, object]], List[str], List[Dict[str, object]]]:
    gt_path = Path(dataset_cfg["ground_truth"]["data_path"])
    with gt_path.open("r", encoding="utf-8") as f:
        gt_samples = json.load(f)

    gt_samples = filter_gt_samples(gt_samples, dataset_cfg)
    basename = gt_path.stem
    class_to_index = {name: idx for idx, name in enumerate(label_classes)}

    formatted: List[Dict[str, object]] = []
    names: List[str] = []
    page_infos: List[Dict[str, object]] = []

    for idx, sample in enumerate(gt_samples):
        boxes, labels, _ = extract_annotations(sample, category_mapping, class_to_index, level_cfg)
        formatted.append({"bboxes": boxes, "labels": labels})
        names.append(build_sample_name(sample, basename, idx))
        page_infos.append(sample.get("page_info", {}) or {})

    return formatted, names, page_infos


def load_predictions(
    dataset_cfg: Dict[str, object],
    label_classes: Sequence[str],
    level_cfg: Dict[str, Sequence[str]],
    category_mapping: Dict[str, str],
    names: Sequence[str],
) -> List[Dict[str, object]]:
    pred_path = Path(dataset_cfg["prediction"]["data_path"])
    with pred_path.open("r", encoding="utf-8") as f:
        pred_samples = json.load(f)

    basename = pred_path.stem
    class_to_index = {name: idx for idx, name in enumerate(label_classes)}

    lookup: Dict[str, Dict[str, object]] = {}
    for sample in pred_samples:
        name = build_sample_name(sample, basename, sample.get("page_info", {}).get("page_no", 0))
        lookup[name] = sample

    formatted: List[Dict[str, object]] = []
    for idx, name in enumerate(names):
        sample = lookup.get(name)
        if sample is None:
            formatted.append({"bboxes": [], "labels": [], "scores": []})
            continue

        boxes, labels, scores = extract_annotations(sample, category_mapping, class_to_index, level_cfg)
        formatted.append({"bboxes": boxes, "labels": labels, "scores": scores})

    return formatted


def load_dataset_samples(
    task_cfg: Dict[str, object]
) -> Tuple[
    List[str],
    List[Dict[str, object]],
    List[Dict[str, object]],
    List[str],
    Dict[str, Sequence[str]],
    List[Dict[str, object]],
]:
    dataset_cfg = task_cfg["dataset"]
    categories_cfg = task_cfg["categories"]

    eval_cat = categories_cfg.get("eval_cat", {})
    block_level = list(dict.fromkeys(eval_cat.get("block_level") or []))
    span_level = list(dict.fromkeys(eval_cat.get("span_level") or []))
    label_classes = list(dict.fromkeys(block_level + span_level))
    level_cfg = {"block_level": block_level, "span_level": span_level}

    gt_cat_mapping = categories_cfg.get("gt_cat_mapping", {})
    pred_cat_mapping = categories_cfg.get("pred_cat_mapping", {})

    gts, names, page_infos = load_ground_truths(dataset_cfg, label_classes, level_cfg, gt_cat_mapping)
    preds = load_predictions(dataset_cfg, label_classes, level_cfg, pred_cat_mapping, names)

    return names, gts, preds, label_classes, level_cfg, page_infos


def process_document(
    gt_sample: Dict[str, object],
    pred_sample: Dict[str, object],
    class_names: Sequence[str],
    eval_classes: Sequence[str],
    allow_merge: bool,
    max_merge: int,
    limit_merge: bool,
    adjust_boxes: bool = False,
    azure_words: Optional[Sequence[Sequence[float]]] = None,
) -> Dict[str, object]:
    def _area(box: Sequence[float]) -> float:
        return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))

    def _intersection_area(box_a: Sequence[float], box_b: Sequence[float]) -> float:
        x1 = max(float(box_a[0]), float(box_b[0]))
        y1 = max(float(box_a[1]), float(box_b[1]))
        x2 = min(float(box_a[2]), float(box_b[2]))
        y2 = min(float(box_a[3]), float(box_b[3]))
        if x2 <= x1 or y2 <= y1:
            return 0.0
        return (x2 - x1) * (y2 - y1)

    def _word_in_box(word_box: Sequence[float], region_box: Sequence[float]) -> bool:
        area_word = _area(word_box)
        if area_word <= 0.0:
            return False
        inter = _intersection_area(word_box, region_box)
        return inter / area_word >= 0.7

    def _shrink_box(box: Sequence[float], words: Sequence[Sequence[float]]) -> Sequence[float]:
        if not words:
            return box
        candidates = [w for w in words if _word_in_box(w, box)]
        if not candidates:
            return box
        x1 = min(float(w[0]) for w in candidates)
        y1 = min(float(w[1]) for w in candidates)
        x2 = max(float(w[2]) for w in candidates)
        y2 = max(float(w[3]) for w in candidates)
        if x2 <= x1 or y2 <= y1:
            return box
        new_box = [x1, y1, x2, y2]
        if _area(new_box) < 0.5 * _area(box):
            return box
        return new_box

    def _combine_boxes(box_list: Sequence[Sequence[float]]) -> Optional[List[float]]:
        if not box_list:
            return None
        x1 = min(float(b[0]) for b in box_list)
        y1 = min(float(b[1]) for b in box_list)
        x2 = max(float(b[2]) for b in box_list)
        y2 = max(float(b[3]) for b in box_list)
        return [x1, y1, x2, y2]

    word_boxes = list(azure_words) if (adjust_boxes and azure_words) else []
    adjusted_gt_cache: Dict[int, Sequence[float]] = {}
    adjusted_pred_cache: Dict[int, Sequence[float]] = {}

    gt_boxes: List[List[float]] = gt_sample["bboxes"]
    pred_boxes: List[List[float]] = pred_sample["bboxes"]
    matches, gt_to_pred, pred_to_gt, unmatched_gt, unmatched_pred = compute_matches(
        gt_boxes, pred_boxes, allow_merge, max_merge, limit_merge
    )

    total_matches = 0
    total_iou = 0.0
    for match in matches:
        g_indices = match["gt_indices"]
        p_indices = match["pred_indices"]
        if not g_indices or not p_indices:
            continue
        has_figure = any(class_names[int(gt_sample["labels"][gi]) ] == "figure" for gi in g_indices) or \
            any(class_names[int(pred_sample["labels"][pi]) ] == "figure" for pi in p_indices)
        if adjust_boxes and word_boxes and not has_figure:
            gt_adjusted = []
            for gi in g_indices:
                if gi not in adjusted_gt_cache:
                    adjusted_gt_cache[gi] = _shrink_box(gt_boxes[gi], word_boxes)
                    gt_sample["bboxes"][gi] = list(adjusted_gt_cache[gi])
                gt_adjusted.append(adjusted_gt_cache[gi])
            pred_adjusted = []
            for pi in p_indices:
                if pi not in adjusted_pred_cache:
                    adjusted_pred_cache[pi] = _shrink_box(pred_boxes[pi], word_boxes)
                    pred_sample["bboxes"][pi] = list(adjusted_pred_cache[pi])
                pred_adjusted.append(adjusted_pred_cache[pi])
            gt_union = _combine_boxes(gt_adjusted)
            pred_union = _combine_boxes(pred_adjusted)
        else:
            gt_union = union_box(gt_boxes, g_indices)
            pred_union = union_box(pred_boxes, p_indices)
        if gt_union is None or pred_union is None:
            continue
        iou_val = bbox_iou(gt_union, pred_union)
        if iou_val <= 0.0:
            continue
        total_matches += 1
        total_iou += iou_val
        match["iou"] = iou_val

    mean_iou = total_iou / total_matches if total_matches else 0.0

    gt_labels: List[int] = gt_sample["labels"]
    pred_labels: List[int] = pred_sample["labels"]
    eval_set = set(eval_classes)

    confusion: Dict[str, Dict[str, float]] = {}
    per_class_totals: Dict[str, float] = {}
    per_class_failures: Dict[str, float] = {}

    for idx, gt_label_idx in enumerate(gt_labels):
        gt_class = class_names[int(gt_label_idx)]
        if gt_class not in eval_set:
            continue

        per_class_totals[gt_class] = per_class_totals.get(gt_class, 0.0) + 1.0

        matched_preds = gt_to_pred.get(idx, [])
        if not matched_preds:
            confusion.setdefault(gt_class, {}).setdefault("missing", 0.0)
            confusion[gt_class]["missing"] += 1.0
            per_class_failures[gt_class] = per_class_failures.get(gt_class, 0.0) + 1.0
            continue

        weight = 1.0 / len(matched_preds)
        failures = 0.0
        for pred_idx in matched_preds:
            pred_class = class_names[int(pred_labels[pred_idx])]
            confusion.setdefault(gt_class, {}).setdefault(pred_class, 0.0)
            confusion[gt_class][pred_class] += weight
            if pred_class != gt_class:
                failures += weight
        if failures > 0:
            per_class_failures[gt_class] = per_class_failures.get(gt_class, 0.0) + failures

    return {
        "matches": matches,
        "gt_to_pred": gt_to_pred,
        "pred_to_gt": pred_to_gt,
        "unmatched_gt": unmatched_gt,
        "unmatched_pred": unmatched_pred,
        "mean_iou": mean_iou,
        "total_matches": total_matches,
        "confusion": confusion,
        "per_class_totals": per_class_totals,
        "per_class_failures": per_class_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute custom detection metrics with flexible merging")
    parser.add_argument("--config", required=True, help="Path to layout detection config YAML")
    parser.add_argument("--output-dir", help="Directory to store outputs")
    parser.add_argument("--merge", action="store_true", help="Allow merging multiple boxes during matching")
    parser.add_argument("--limit-merge", action="store_true", help="Restrict merges to one side at a time")
    parser.add_argument("--image", help="Image file to visualise")
    parser.add_argument(
        "--image-root",
        help="Directory containing page images (defaults to <ground_truth_dir>/images)",
    )
    parser.add_argument(
        "--max-merge",
        type=int,
        default=6,
        help="Maximum number of boxes to consider when evaluating merged candidates",
    )
    parser.add_argument(
        "--adjust-boxes",
        action="store_true",
        help="Adjust matched boxes using Azure OCR word bounding boxes",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError("Configuration must map task names to config blocks")

    output_root = Path(args.output_dir).resolve() if args.output_dir else ROOT / "result"
    output_root.mkdir(parents=True, exist_ok=True)

    model_name = config_path.stem.split("layout_detection_")[-1]

    for task_name, task_cfg in cfg.items():
        names, gts, preds, class_names, level_cfg, page_infos = load_dataset_samples(task_cfg)
        eval_classes = list(dict.fromkeys((level_cfg.get("block_level") or []) + (level_cfg.get("span_level") or [])))

        per_doc_records: List[Dict[str, object]] = []
        debug_payload = None
        flagged_payloads: List[Dict[str, object]] = []
        for idx, (gt_sample, pred_sample) in enumerate(zip(gts, preds)):
            page_info = page_infos[idx] if idx < len(page_infos) else {}
            page_no = int(page_info.get("image_path", idx).split("_")[-1].split(".")[0])
            azure_words = None
            if args.adjust_boxes:
                page_width = page_info.get("width")
                page_height = page_info.get("height")
                azure_words = load_azure_words(names[idx], page_no, AZURE_ROOT, page_width, page_height)

            metrics = process_document(
                gt_sample,
                pred_sample,
                class_names,
                eval_classes,
                allow_merge=args.merge,
                max_merge=max(1, args.max_merge),
                limit_merge=args.limit_merge,
                adjust_boxes=args.adjust_boxes,
                azure_words=azure_words,
            )
            name = names[idx] if idx < len(names) else f"doc_{idx:05d}"
            record = {
                "document": name,
                "num_gt": len(gt_sample["bboxes"]),
                "num_pred": len(pred_sample["bboxes"]),
                "total_matches": metrics["total_matches"],
                "false_negatives": len(metrics["unmatched_gt"]),
                "false_positives": len(metrics["unmatched_pred"]),
                "mean_iou": metrics["mean_iou"],
                "confusion": metrics["confusion"],
                "per_class_totals": metrics["per_class_totals"],
                "per_class_failures": metrics["per_class_failures"],
            }
            per_doc_records.append(record)

            payload = {
                "name": name,
                "metrics": metrics,
                "gt": gt_sample,
                "pred": pred_sample,
                "page_info": page_info,
                "words": azure_words if args.adjust_boxes else None,
            }

            if args.image:
                target = args.image
                if target == name or Path(name).stem == Path(target).stem:
                    debug_payload = payload
            elif metrics["unmatched_gt"] or metrics["unmatched_pred"]:
                flagged_payloads.append(payload)

        aggregate = aggregate_results(per_doc_records, eval_classes)

        task_output_dir = output_root / model_name / task_name
        task_output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = task_output_dir / f"{model_name}_per_document_metrics.csv"
        json_path = task_output_dir / f"{model_name}_aggregate_metrics.json"

        if not args.image:
            write_csv(csv_path, per_doc_records, eval_classes)
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(aggregate, f, indent=2, ensure_ascii=False)

        if args.image:
            if debug_payload is None:
                raise ValueError(f"Image '{args.image}' not found in dataset pages.")
            gt_dir = Path(task_cfg["dataset"]["ground_truth"]["data_path"]).resolve().parent
            image_root = Path(args.image_root).resolve() if args.image_root else gt_dir / "images"
            candidate = image_root / debug_payload["name"]
            if not candidate.exists():
                alt = Path(debug_payload["name"])
                if alt.is_absolute() and alt.exists():
                    candidate = alt
                else:
                    raise FileNotFoundError(
                        f"Could not locate image file for '{debug_payload['name']}' (looked in {image_root})."
                    )
            debug_output = task_output_dir / f"{model_name}_debug_{Path(debug_payload['name']).stem}.png"
            render_debug_image(
                candidate,
                debug_output,
                debug_payload["metrics"],
                debug_payload["gt"],
                debug_payload["pred"],
                class_names,
                azure_words=debug_payload.get("words"),
            )
            print(f"[{task_name}] Wrote debug visualization to {debug_output}")
        elif flagged_payloads:
            gt_dir = Path(task_cfg["dataset"]["ground_truth"]["data_path"]).resolve().parent
            image_root = Path(args.image_root).resolve() if args.image_root else gt_dir / "images"
            for payload in flagged_payloads:
                candidate = image_root / payload["name"]
                if not candidate.exists():
                    alt = Path(payload["name"])
                    if alt.is_absolute() and alt.exists():
                        candidate = alt
                    else:
                        print(f"  [warn] Skipping visualization for {payload['name']} (image not found)")
                        continue
                debug_output = task_output_dir / f"{model_name}_debug_{Path(payload['name']).stem}.png"
                render_debug_image(
                    candidate,
                    debug_output,
                    payload["metrics"],
                    payload["gt"],
                    payload["pred"],
                    class_names,
                    azure_words=payload.get("words"),
                )
            print(f"[{task_name}] Wrote {len(flagged_payloads)} debug visualizations for FP/FN samples")

        if not args.image:
            print(f"[{task_name}] Wrote per-document metrics to {csv_path}")
            print(f"[{task_name}] Wrote aggregate metrics to {json_path}")
        else:
            print(f"[{task_name}] Generated debug visualization only")


if __name__ == "__main__":
    main()
