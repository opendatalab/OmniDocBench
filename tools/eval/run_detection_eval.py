import argparse
import json
import os
from pathlib import Path
import sys

# Avoid optional dependencies and Accelerate issues on macOS
os.environ.setdefault('NPY_DISABLE_MACOS_ACCELERATE', '1')
os.environ.setdefault('OMNIDOCBENCH_SKIP_END2END', '1')
os.environ.setdefault('OMNIDOCBENCH_SKIP_RECOG', '1')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
import numpy as np
from mmeval import COCODetection
from dataset.detection_dataset import DetectionDataset  # noqa: E402


def _bbox_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    if xB <= xA or yB <= yA:
        return 0.0
    inter = (xB - xA) * (yB - yA)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    if union <= 0:
        return 0.0
    return inter / union


def _count_hits(gt_boxes, pred_boxes, scores, iou_thresh):
    gt_list = [np.asarray(box, dtype=np.float32) for box in gt_boxes]
    pred_list = [np.asarray(box, dtype=np.float32) for box in pred_boxes]
    if not gt_list and not pred_list:
        return 0, 0
    denom = max(len(gt_list), len(pred_list))
    if denom == 0:
        return 0, 0

    matched = [False] * len(gt_list)
    if len(pred_list) and scores is not None and len(scores):
        order = np.argsort(-scores)
    else:
        order = range(len(pred_list))

    hits = 0
    for idx in order:
        bbox = pred_list[idx]
        best_iou = 0.0
        best_idx = -1
        for gt_idx, gt_bbox in enumerate(gt_list):
            if matched[gt_idx]:
                continue
            val = _bbox_iou(bbox, gt_bbox)
            if val > best_iou:
                best_iou = val
                best_idx = gt_idx
        if best_iou >= iou_thresh and best_idx >= 0:
            matched[best_idx] = True
            hits += 1

    return hits, denom


def _json_default(value):
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f'Type {type(value)} not serializable')


def _per_class_ap(dataset, iou_thresh):
    metric = COCODetection(
        dataset_meta=dataset.meta,
        metric=['bbox'],
        classwise=True,
        iou_thrs=[iou_thresh],
    )
    scores = metric(
        predictions=dataset.samples['preds'],
        groundtruths=dataset.samples['gts'],
    )
    suffix = f'_mAP{int(iou_thresh * 100):02d}'
    result = {}
    for key, value in scores.items():
        if not key.startswith('bbox_') or not key.endswith('_precision'):
            continue
        cls = key[len('bbox_'):-len('_precision')]
        result[f'bbox_{cls}{suffix}'] = float(value)
    return result


def _per_class_hit(dataset, iou_thresh):
    classes = list(dataset.meta['CLASSES'])
    suffix = f'_hit{int(iou_thresh * 100):02d}'
    hits_sum = {cls: 0 for cls in classes}
    denom_sum = {cls: 0 for cls in classes}

    for gt_sample, pred_sample in zip(dataset.samples['gts'], dataset.samples['preds']):
        gt_boxes = gt_sample['bboxes']
        pred_boxes = pred_sample['bboxes']
        scores = pred_sample.get('scores')
        gt_labels = gt_sample['labels']
        pred_labels = pred_sample['labels']

        for cls_idx, cls_name in enumerate(classes):
            gt_mask = (gt_labels == cls_idx)
            pred_mask = (pred_labels == cls_idx)

            gt_cls = gt_boxes[gt_mask]
            pred_cls = pred_boxes[pred_mask]
            score_cls = scores[pred_mask] if scores is not None else np.ones(len(pred_cls), dtype=np.float32)

            if len(gt_cls) == 0 and len(pred_cls) == 0:
                continue

            hits, denom = _count_hits(gt_cls, pred_cls, score_cls, iou_thresh)
            hits_sum[cls_name] += hits
            denom_sum[cls_name] += denom

    per_class = {}
    valid_values = []
    for cls in classes:
        denom = denom_sum[cls]
        if denom == 0:
            per_class[f'bbox_{cls}{suffix}'] = None
            continue
        value = hits_sum[cls] / denom
        per_class[f'bbox_{cls}{suffix}'] = value
        valid_values.append(value)

    mean_key = f'bbox{suffix}'
    mean_value = sum(valid_values) / len(valid_values) if valid_values else None
    return mean_key, mean_value, per_class


def main():
    parser = argparse.ArgumentParser(description="Run OmniDocBench layout detection evaluation")
    parser.add_argument("--config", required=True, help="Path to layout detection config YAML")
    parser.add_argument(
        "--output",
        help="Output directory (default: <repo>/result)",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError("Configuration must be a mapping of task names to config blocks")

    output_dir = Path(args.output).resolve() if args.output else ROOT / 'result'
    output_dir.mkdir(parents=True, exist_ok=True)

    for task_name, cfg_task in cfg.items():
        print(f"Running task: {task_name}")
        dataset = DetectionDataset(cfg_task)
        if getattr(dataset, 'variant_metrics', None):
            print("  Merge variant scores:")
            for variant_name, metrics in sorted(dataset.variant_metrics.items()):
                primary = metrics.get('bbox_mAP', metrics.get('bbox_mAP_50', float('nan')))
                print(f"    {variant_name:12s} -> mAP {primary:.4f}")
            if getattr(dataset, 'chosen_variant', 'base') != 'base':
                print(f"  Selected merge variant: {dataset.chosen_variant}")
        result = dataset.coco_det_metric(
            predictions=dataset.samples['preds'],
            groundtruths=dataset.samples['gts'],
        )
        if getattr(dataset, 'variant_metrics', None):
            result = dict(result)
            result['_merge_selected'] = dataset.chosen_variant
            result['_merge_variants'] = dataset.variant_metrics

        per_class_metrics = {}
        hit_metrics = {}
        for thr in (0.50, 0.75):
            per_class_metrics.update(_per_class_ap(dataset, thr))
            mean_key, mean_value, per_class_hit = _per_class_hit(dataset, thr)
            hit_metrics.update(per_class_hit)
            result[mean_key] = mean_value
        result.update(per_class_metrics)
        result.update(hit_metrics)

        pred_path = Path(cfg_task['dataset']['prediction']['data_path'])
        default_name = f"{pred_path.stem}_{task_name}_metrics.json"
        output_path = output_dir / default_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=_json_default)

        print(f"[{task_name}] Metrics written to {output_path}")


if __name__ == "__main__":
    main()
