import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "data" / "OmniDocBench_data"

GT_PATH = DATA_ROOT / "OmniDocBench_mineru_single.json"
PRED_PATH = DATA_ROOT / "predictions" / "mineru_vlm_single.json"

CATEGORIES = ['title','text_block','figure','figure_caption','table','table_caption','equation','page_number','header','footer']

with GT_PATH.open() as f:
    gt_sample = json.load(f)[0]
with PRED_PATH.open() as f:
    pred_sample = json.load(f)[0]

width = gt_sample['page_info']['width']
height = gt_sample['page_info']['height']


def poly_to_bbox(poly):
    x1,y1,x2,_,x3,y3,_,_ = poly
    return [min(x1,x2), min(y1,y3), max(x1,x2), max(y1,y3)]


def iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])
    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter = inter_w * inter_h
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    if union <= 0:
        return 0.0
    return inter / union


# Prepare GT and preds per class
class_gt = {cat: [] for cat in CATEGORIES}
for det in gt_sample['layout_dets']:
    cat = det['category_type']
    if cat not in class_gt:
        continue
    class_gt[cat].append(poly_to_bbox(det['poly']))

class_pred = {cat: [] for cat in CATEGORIES}
for det in pred_sample['layout_dets']:
    cat = det['category_type']
    if cat not in class_pred:
        continue
    class_pred[cat].append((poly_to_bbox(det['poly']), det.get('score', 1.0)))


def average_precision(gt_boxes, pred_boxes, iou_thresh):
    if not gt_boxes and not pred_boxes:
        return float('nan')
    if not gt_boxes:
        return 0.0
    if not pred_boxes:
        return 0.0

    pred_boxes = sorted(pred_boxes, key=lambda x: x[1], reverse=True)
    tp = [0] * len(pred_boxes)
    fp = [0] * len(pred_boxes)
    matched = [False] * len(gt_boxes)

    for idx, (bbox, score) in enumerate(pred_boxes):
        best_iou = 0.0
        best_gt = -1
        for j, gt_bbox in enumerate(gt_boxes):
            iou_val = iou(bbox, gt_bbox)
            if iou_val > best_iou:
                best_iou = iou_val
                best_gt = j
        if best_iou >= iou_thresh and best_gt >= 0 and not matched[best_gt]:
            tp[idx] = 1
            matched[best_gt] = True
        else:
            fp[idx] = 1

    tp_cumsum = []
    fp_cumsum = []
    total_tp = 0
    total_fp = 0
    for t, f in zip(tp, fp):
        total_tp += t
        total_fp += f
        tp_cumsum.append(total_tp)
        fp_cumsum.append(total_fp)

    precisions = []
    recalls = []
    for tp_i, fp_i in zip(tp_cumsum, fp_cumsum):
        precision = tp_i / (tp_i + fp_i) if (tp_i + fp_i) > 0 else 0
        recall = tp_i / len(gt_boxes)
        precisions.append(precision)
        recalls.append(recall)

    # Append start point
    precisions = [1.0] + precisions
    recalls = [0.0] + recalls

    ap = 0.0
    for i in range(1, len(precisions)):
        ap += (recalls[i] - recalls[i - 1]) * precisions[i]
    return ap


for thresh in [0.5, 0.75]:
    print(f'IoU threshold {thresh}')
    class_aps = {}
    aps = []
    for cat in CATEGORIES:
        ap = average_precision(class_gt[cat], class_pred[cat], thresh)
        class_aps[cat] = ap
        if not (ap != ap):  # NaN check
            aps.append(ap)
    mAP = sum(aps) / len(aps) if aps else float('nan')
    print(f'  mAP: {mAP:.4f}')
    for cat, ap in class_aps.items():
        if ap != ap:  # NaN
            continue
        print(f'    {cat:15s} {ap:.4f}')
    print()
