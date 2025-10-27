from __future__ import annotations

import argparse
import json
import random
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from dataset.detection_dataset import DetectionDataset

DEFAULT_CONFIG = BASE_DIR / 'configs' / 'InvofoxBench' / 'layout_detection_doclayout_yolo_full.yaml'#'layout_detection_pp_doclayout_plus_l_full.yaml'#'layout_detection_mineru_vlm_full.yaml'


def draw_dashed_rectangle(draw: ImageDraw.ImageDraw, bbox, color, width=2, dash=12):
    x1, y1, x2, y2 = bbox

    def _draw_segment(xa, ya, xb, yb):
        dx, dy = xb - xa, yb - ya
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            return
        step = max(int(length // dash), 1)
        for i in range(0, step, 2):
            start = i / step
            end = min((i + 1) / step, 1)
            xs, ys = xa + dx * start, ya + dy * start
            xe, ye = xa + dx * end, ya + dy * end
            draw.line([xs, ys, xe, ye], fill=color, width=width)

    _draw_segment(x1, y1, x2, y1)
    _draw_segment(x2, y1, x2, y2)
    _draw_segment(x2, y2, x1, y2)
    _draw_segment(x1, y2, x1, y1)


def load_config_task(config_path: Path, task_name: str | None) -> tuple[dict, str]:
    with config_path.open('r', encoding='utf-8') as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError('Configuration file must map task names to config blocks.')

    if task_name:
        if task_name not in cfg:
            raise KeyError(f'Task "{task_name}" not found in config. Available: {list(cfg.keys())}')
        selected = task_name
    elif len(cfg) == 1:
        selected = next(iter(cfg))
    elif 'detection_eval' in cfg:
        selected = 'detection_eval'
    else:
        selected = next(iter(cfg))

    cfg_task = deepcopy(cfg[selected])
    if 'dataset' not in cfg_task:
        raise ValueError(f'Task "{selected}" does not contain a dataset section.')
    return cfg_task, selected


def load_ocr_word_polygons(
    ocr_dir: Path | None,
    image_name: str,
    image_size: tuple[int, int],
) -> list[list[tuple[float, float]]]:
    """Load OCR word polygons and map them to image coordinates."""
    if ocr_dir is None:
        return []

    ocr_path = ocr_dir / Path(image_name).with_suffix('.json')
    if not ocr_path.exists():
        print(f'[WARN] OCR file not found: {ocr_path}')
        return []

    try:
        ocr_data = json.loads(ocr_path.read_text())
    except json.JSONDecodeError as exc:
        print(f'[WARN] Failed to parse OCR file {ocr_path}: {exc}')
        return []

    image_width, image_height = image_size
    ocr_width = float(ocr_data.get('width') or 0)
    ocr_height = float(ocr_data.get('height') or 0)

    if image_width <= 0 or image_height <= 0 or ocr_width <= 0 or ocr_height <= 0:
        print(
            f'[WARN] Invalid OCR/image dimensions for {image_name}: '
            f'ocr=({ocr_width}, {ocr_height}), image=({image_width}, {image_height})'
        )
        return []

    scale_x = image_width / ocr_width
    scale_y = image_height / ocr_height
    rel_diff = abs(scale_x - scale_y) / max(scale_x, scale_y)
    if rel_diff < 1e-3:
        uniform = (scale_x + scale_y) / 2.0
        scale_x = scale_y = uniform

    polygons: list[list[tuple[float, float]]] = []
    for line in ocr_data.get('lines', []):
        for word in line.get('words', []):
            coords = word.get('boundingBox') or word.get('bounding_box')
            if not coords or len(coords) < 8:
                continue
            polygon: list[tuple[float, float]] = []
            for x_val, y_val in zip(coords[::2], coords[1::2]):
                polygon.append((x_val * scale_x, y_val * scale_y))
            polygons.append(polygon)
    return polygons


def bbox_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter = inter_w * inter_h
    if inter == 0:
        return 0.0
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


def visualize(
    target_image: str,
    dataset: DetectionDataset,
    image_dir: Path,
    ocr_dir: Path | None,
    output_path: Path | None = None,
    show_ocr: bool = False,
):
    if getattr(dataset, 'img_list', None) is None:
        raise RuntimeError('DetectionDataset does not expose `img_list`; please update the dataset implementation.')

    try:
        sample_idx = dataset.img_list.index(target_image)
    except ValueError as exc:
        preview = ', '.join(dataset.img_list[:5]) + ('...' if len(dataset.img_list) > 5 else '')
        raise FileNotFoundError(
            f'{target_image} not found in dataset image list. Sample names start with: {preview}'
        ) from exc

    gt_sample = dataset.samples['gts'][sample_idx]
    pred_sample = dataset.samples['preds'][sample_idx]

    image_path = image_dir / target_image
    if not image_path.exists():
        raise FileNotFoundError(f'Image not found: {image_path}')
    img = Image.open(image_path).convert('RGBA')

    if show_ocr:
        word_polygons = load_ocr_word_polygons(ocr_dir, target_image, img.size)
        if word_polygons:
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay, 'RGBA')
            for polygon in word_polygons:
                overlay_draw.polygon(polygon, fill=(128, 128, 128, 60))
            img = Image.alpha_composite(img, overlay)
        else:
            print(f'No OCR word boxes found for {target_image}')

    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    classes = list(dataset.meta.get('CLASSES', ()))
    color_map: dict[str, tuple[int, int, int]] = {}

    def get_color(category: str) -> tuple[int, int, int]:
        if category not in color_map:
            color_map[category] = tuple(random.randint(0, 255) for _ in range(3))
        return color_map[category]

    if classes:
        metric_gt = {
            'img_id': 0,
            'bboxes': gt_sample['bboxes'],
            'labels': gt_sample['labels'],
            'ignore_flags': gt_sample.get(
                'ignore_flags',
                np.zeros(len(gt_sample['labels']), dtype=bool),
            ),
            'width': float(gt_sample.get('width', img.size[0])),
            'height': float(gt_sample.get('height', img.size[1])),
        }
        metric_pred = {
            'img_id': 0,
            'bboxes': pred_sample['bboxes'],
            'labels': pred_sample['labels'],
            'scores': pred_sample.get(
                'scores',
                np.ones(len(pred_sample['bboxes']), dtype=np.float32),
            ),
            'width': float(pred_sample.get('width', img.size[0])),
            'height': float(pred_sample.get('height', img.size[1])),
        }
        res = dataset.coco_det_metric([metric_pred], [metric_gt])
        print(f'Metrics for {target_image}')
        if 'bbox_mAP_50' in res and 'bbox_mAP_75' in res:
            print(f"  mAP@0.50: {res['bbox_mAP_50']:.4f}")
            print(f"  mAP@0.75: {res['bbox_mAP_75']:.4f}")
        else:
            print(f"  mAP: {res.get('bbox_mAP', float('nan')):.4f}")
    else:
        print('Metrics skipped: no evaluation classes defined.')

    gt_entries = []
    gt_boxes = gt_sample['bboxes']
    gt_labels = gt_sample['labels']
    gt_ignores = gt_sample.get('ignore_flags', np.zeros(len(gt_labels), dtype=bool))

    for bbox_arr, label_idx, ignore_flag in zip(gt_boxes, gt_labels, gt_ignores):
        bbox = bbox_arr.tolist()
        cat = classes[label_idx] if 0 <= label_idx < len(classes) else str(label_idx)
        color = get_color(cat)
        draw.rectangle(bbox, outline=color, width=1 if ignore_flag else 2)
        label_text = f'{cat}{" (ignore)" if ignore_flag else ""}'
        text_pos = (bbox[0], max(bbox[1] - 12, 0))
        draw.text(text_pos, label_text, fill=color, font=font)
        gt_entries.append({'category': cat, 'bbox': bbox})

    gt_used = [False] * len(gt_entries)

    def find_best_match(pred_box, cat):
        best_iou, best_idx = 0.0, -1
        for idx, entry in enumerate(gt_entries):
            if gt_used[idx] or entry['category'] != cat:
                continue
            iou_val = bbox_iou(pred_box, entry['bbox'])
            if iou_val > best_iou:
                best_iou = iou_val
                best_idx = idx
        if best_idx >= 0:
            gt_used[best_idx] = True
        return best_iou

    pred_boxes = pred_sample['bboxes']
    pred_labels = pred_sample['labels']
    pred_scores = pred_sample.get('scores', np.ones(len(pred_boxes), dtype=np.float32))

    for bbox_arr, label_idx, score in zip(pred_boxes, pred_labels, pred_scores):
        bbox = bbox_arr.tolist()
        cat = classes[label_idx] if 0 <= label_idx < len(classes) else str(label_idx)
        color = get_color(cat)
        draw_dashed_rectangle(draw, bbox, color=color, width=2, dash=12)
        iou_val = find_best_match(bbox, cat)
        header_text = f'{cat} | IoU {iou_val:.2f}'
        footer_text = f'Score {score:.2f}'
        draw.text((bbox[0], max(bbox[1] - 12, 0)), header_text, fill=color, font=font)
        # draw.text((bbox[0], min(bbox[3] + 2, img.size[1] - 10)), footer_text, fill=color, font=font)

    if output_path is None:
        output_path = Path(__file__).resolve().parent / f'{target_image}_overlay.png'
    img.convert('RGB').save(output_path)
    print(f'Saved overlay visualization to {output_path}')


def parse_args():
    parser = argparse.ArgumentParser(description='Visualize GT vs prediction overlay for layout detection.')
    parser.add_argument('--image', required=True, help='Image filename (e.g., 6602c3..._0.jpg)')
    parser.add_argument('--output', help='Optional output image path')
    parser.add_argument('--show-ocr', action='store_true', help='Overlay OCR words as translucent polygons')
    parser.add_argument('--pred', help='Optional override for prediction JSON path')
    parser.add_argument('--config', default=DEFAULT_CONFIG, help='Layout detection config YAML')
    parser.add_argument('--task', help='Task name inside the YAML (default: first task)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    config_path = Path(args.config).resolve()
    cfg_task, task_name = load_config_task(config_path, args.task)

    if args.pred:
        cfg_task['dataset']['prediction']['data_path'] = str(Path(args.pred).resolve())

    dataset = DetectionDataset(cfg_task)
    print(f'Loaded dataset task "{task_name}" with merge variant: {dataset.chosen_variant}')

    gt_path = Path(cfg_task['dataset']['ground_truth']['data_path']).resolve()
    data_root = gt_path.parent
    image_dir = data_root / 'images'
    ocr_dir = data_root / 'ocrs'

    if not image_dir.exists():
        raise FileNotFoundError(f'Image directory not found: {image_dir}')
    if not ocr_dir.exists():
        print(f'[WARN] OCR directory not found: {ocr_dir}. OCR overlay disabled.')
        ocr_dir = None

    output = Path(args.output).resolve() if args.output else None
    visualize(
        args.image,
        dataset=dataset,
        image_dir=image_dir,
        ocr_dir=ocr_dir,
        output_path=output,
        show_ocr=args.show_ocr and ocr_dir is not None,
    )
