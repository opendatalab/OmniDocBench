#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

DEFAULT_CLASSES = [
    'title',
    'text_block',
    'figure',
    'figure_caption',
    'table',
    'table_caption',
    'equation',
    'page_number',
    'header',
    'footer',
]

GT_NORMALIZE = {
    'equation_isolated': 'equation',
    'equation_caption': 'figure_caption',
    'table_footnote': None,
    'figure_footnote': 'figure_caption',
    'code_txt': 'figure',
    'code_txt_caption': 'figure_caption',
    'text': 'text_block',
    'reference': 'text_block',
    'refernece': 'text_block',
    'text_mask': 'text_block',
    'need_mask': None,
    'abandon': None,
}

PRED_NORMALIZE = {
    'text': 'text_block',
    'plain text': 'text_block',
    'isolate_formula': 'equation',
    'equation_isolated': 'equation',
    'formula_caption': 'figure_caption',
    'table_footnote': None,
    'abandon': None,
}


def normalize_label(label: str, mapping: Dict[str, str]) -> str | None:
    if label in mapping:
        return mapping[label]
    return label


def bbox_iou(box1: np.ndarray, box2: np.ndarray) -> float:
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


def compute_ap(gt_boxes: List[np.ndarray], pred_boxes: List[Tuple[float, np.ndarray]], iou_thresh: float) -> float:
    if not gt_boxes and not pred_boxes:
        return float('nan')
    if not gt_boxes:
        return 0.0
    if not pred_boxes:
        return 0.0

    pred_boxes = sorted(pred_boxes, key=lambda x: x[0], reverse=True)
    matched = [False] * len(gt_boxes)
    tp = []
    fp = []

    for score, bbox in pred_boxes:
        best_iou = 0.0
        best_idx = -1
        for i, gt_bbox in enumerate(gt_boxes):
            if matched[i]:
                continue
            val = bbox_iou(bbox, gt_bbox)
            if val > best_iou:
                best_iou = val
                best_idx = i
        if best_iou >= iou_thresh and best_idx >= 0:
            matched[best_idx] = True
            tp.append(1)
            fp.append(0)
        else:
            tp.append(0)
            fp.append(1)

    tp_cum = 0
    fp_cum = 0
    precisions = [1.0]
    recalls = [0.0]
    for t, f in zip(tp, fp):
        tp_cum += t
        fp_cum += f
        precision = tp_cum / (tp_cum + fp_cum) if (tp_cum + fp_cum) > 0 else 0.0
        recall = tp_cum / len(gt_boxes)
        precisions.append(precision)
        recalls.append(recall)

    ap = 0.0
    for i in range(1, len(precisions)):
        ap += (recalls[i] - recalls[i - 1]) * precisions[i]
    return ap


def compute_hit_rate(gt_boxes: List[np.ndarray], pred_boxes: List[Tuple[float, np.ndarray]], iou_thresh: float) -> float:
    if not gt_boxes and not pred_boxes:
        return float('nan')
    denom = max(len(gt_boxes), len(pred_boxes))
    if denom == 0:
        return float('nan')

    matched = [False] * len(gt_boxes)
    hits = 0
    for score, bbox in sorted(pred_boxes, key=lambda x: x[0], reverse=True):
        best_iou = 0.0
        best_idx = -1
        for i, gt_bbox in enumerate(gt_boxes):
            if matched[i]:
                continue
            val = bbox_iou(bbox, gt_bbox)
            if val > best_iou:
                best_iou = val
                best_idx = i
        if best_iou >= iou_thresh and best_idx >= 0:
            matched[best_idx] = True
            hits += 1

    return hits / denom


def build_records(
    config_path: Path,
    model_name: str,
    output_path: Path,
    target_classes: List[str],
    include_map: bool,
    include_hit: bool,
) -> None:
    import sys
    omni_root = config_path.parents[2]
    if str(omni_root) not in sys.path:
        sys.path.insert(0, str(omni_root))
    import yaml
    from dataset.detection_dataset import DetectionDataset

    cfg = yaml.safe_load(config_path.read_text())
    task_cfg = cfg['detection_eval']
    dataset = DetectionDataset(task_cfg)

    gt_path = Path(task_cfg['dataset']['ground_truth']['data_path'])
    gt_manifest = json.loads(gt_path.read_text())

    gts = dataset.samples['gts']
    preds = dataset.samples['preds']
    classes = list(dataset.meta['CLASSES'])

    if not include_map and not include_hit:
        raise ValueError('At least one of include_map/include_hit must be True')

    headers = ['model', 'image']
    if include_map:
        headers.extend(['mAP50', 'mAP75'])
    if include_hit:
        headers.extend(['hit50', 'hit75'])
    for cls in target_classes:
        if include_map:
            headers.append(f'{cls}_mAP50')
            headers.append(f'{cls}_mAP75')
        if include_hit:
            headers.append(f'{cls}_hit50')
            headers.append(f'{cls}_hit75')

    rows = []

    for idx, (gt_sample, pred_sample, manifest_entry) in enumerate(zip(gts, preds, gt_manifest)):
        image_name = manifest_entry['page_info']['image_path']

        gt_boxes_by_class: Dict[str, List[np.ndarray]] = {cls: [] for cls in target_classes}
        for bbox, label in zip(gt_sample['bboxes'], gt_sample['labels']):
            cls_name = classes[label]
            cls_name = normalize_label(cls_name, GT_NORMALIZE)
            if cls_name in gt_boxes_by_class:
                gt_boxes_by_class[cls_name].append(np.array(bbox, dtype=np.float32))

        pred_boxes_by_class: Dict[str, List[Tuple[float, np.ndarray]]] = {cls: [] for cls in target_classes}
        for bbox, label, score in zip(pred_sample['bboxes'], pred_sample['labels'], pred_sample['scores']):
            cls_name = classes[label]
            cls_name = normalize_label(cls_name, PRED_NORMALIZE)
            if cls_name in pred_boxes_by_class:
                pred_boxes_by_class[cls_name].append((float(score), np.array(bbox, dtype=np.float32)))

        class_ap50: Dict[str, float] | None = {} if include_map else None
        class_ap75: Dict[str, float] | None = {} if include_map else None
        class_hit50: Dict[str, float] | None = {} if include_hit else None
        class_hit75: Dict[str, float] | None = {} if include_hit else None
        for cls in target_classes:
            if include_map:
                ap50 = compute_ap(gt_boxes_by_class[cls], pred_boxes_by_class[cls], 0.5)
                ap75 = compute_ap(gt_boxes_by_class[cls], pred_boxes_by_class[cls], 0.75)
                class_ap50[cls] = ap50
                class_ap75[cls] = ap75
            if include_hit:
                hit50 = compute_hit_rate(gt_boxes_by_class[cls], pred_boxes_by_class[cls], 0.5)
                hit75 = compute_hit_rate(gt_boxes_by_class[cls], pred_boxes_by_class[cls], 0.75)
                class_hit50[cls] = hit50
                class_hit75[cls] = hit75

        row = [model_name, image_name]
        if include_map and class_ap50 is not None and class_ap75 is not None:
            valid_50 = [v for v in class_ap50.values() if not math.isnan(v)]
            valid_75 = [v for v in class_ap75.values() if not math.isnan(v)]
            mean50 = sum(valid_50) / len(valid_50) if valid_50 else float('nan')
            mean75 = sum(valid_75) / len(valid_75) if valid_75 else float('nan')
            row.append(mean50 if not math.isnan(mean50) else None)
            row.append(mean75 if not math.isnan(mean75) else None)
        if include_hit and class_hit50 is not None and class_hit75 is not None:
            valid_hit50 = [v for v in class_hit50.values() if not math.isnan(v)]
            valid_hit75 = [v for v in class_hit75.values() if not math.isnan(v)]
            mean_hit50 = sum(valid_hit50) / len(valid_hit50) if valid_hit50 else float('nan')
            mean_hit75 = sum(valid_hit75) / len(valid_hit75) if valid_hit75 else float('nan')
            row.append(mean_hit50 if not math.isnan(mean_hit50) else None)
            row.append(mean_hit75 if not math.isnan(mean_hit75) else None)
        for cls in target_classes:
            if include_map and class_ap50 is not None and class_ap75 is not None:
                v50 = class_ap50[cls]
                v75 = class_ap75[cls]
                row.append(v50 if not math.isnan(v50) else None)
                row.append(v75 if not math.isnan(v75) else None)
            if include_hit and class_hit50 is not None and class_hit75 is not None:
                h50 = class_hit50[cls]
                h75 = class_hit75[cls]
                row.append(h50 if not math.isnan(h50) else None)
                row.append(h75 if not math.isnan(h75) else None)
        rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with output_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        for row in rows:
            formatted = []
            for value in row:
                if value is None:
                    formatted.append('')
                elif isinstance(value, float):
                    formatted.append(f'{value:.4f}')
                else:
                    formatted.append(value)
            writer.writerow(formatted)


def main():
    parser = argparse.ArgumentParser(description='Export per-image AP metrics')
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--model-name', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--classes', nargs='+', default=DEFAULT_CLASSES)
    parser.add_argument('--show-map', action='store_true', help='Export mAP columns instead of hit-rate')
    args = parser.parse_args()

    include_map = args.show_map
    include_hit = not args.show_map

    build_records(args.config, args.model_name, args.output, args.classes, include_map, include_hit)


if __name__ == '__main__':
    main()
