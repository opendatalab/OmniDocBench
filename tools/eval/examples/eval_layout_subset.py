import os
os.environ.setdefault('NPY_DISABLE_MACOS_ACCELERATE', '1')
os.environ.setdefault('OMNIDOCBENCH_SKIP_END2END', '1')
os.environ.setdefault('OMNIDOCBENCH_SKIP_RECOG', '1')

import json
import yaml
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from dataset.detection_dataset import DetectionDataset  # noqa: E402

CONFIG_PATH = ROOT / 'configs/layout_detection_doclayout_yolo_subset.yaml'
OUTPUT_PATH = ROOT / 'result/doclayout_yolo_pred_10_metrics.json'
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

cfg_task = cfg['detection_eval']
dataset = DetectionDataset(cfg_task)
result = dataset.coco_det_metric(predictions=dataset.samples['preds'], groundtruths=dataset.samples['gts'])

if hasattr(result, 'to_dict'):
    serializable = result.to_dict()
elif isinstance(result, dict):
    serializable = result
else:
    serializable = {'repr': repr(result)}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(serializable, f, ensure_ascii=False, indent=2)

print(f'Metrics written to {OUTPUT_PATH}')
