import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import yaml


ROOT = Path(__file__).resolve().parents[2]
OMNIDOCBENCH_DIR = ROOT
if str(OMNIDOCBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(OMNIDOCBENCH_DIR))

# The imports below rely on the OmniDocBench package layout.
import dataset as omnidoc_dataset  # noqa: F401  - side effects register datasets
from registry.registry import DATASET_REGISTRY  # type: ignore
from mmeval.metrics.coco_detection import COCODetection  # type: ignore


def load_config(config_path: Path) -> Dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def evaluate_detection(cfg: Dict, output_dir: Path) -> Path:
    task_name, task_cfg = next(iter(cfg.items()))
    dataset_name = task_cfg["dataset"]["dataset_name"]
    dataset_cls = DATASET_REGISTRY.get(dataset_name)
    dataset = dataset_cls(task_cfg)

    preds = dataset.samples["preds"]
    gts = dataset.samples["gts"]
    classes = tuple(dataset.meta["CLASSES"])

    metric_kwargs = dict(dataset_meta={"classes": classes}, metric="bbox", classwise=True, print_results=False)
    metric_main = COCODetection(**metric_kwargs)
    metric_50 = COCODetection(**metric_kwargs, iou_thrs=[0.5])
    metric_75 = COCODetection(**metric_kwargs, iou_thrs=[0.75])

    res_main = metric_main(preds, gts)
    res_50 = metric_50(preds, gts)
    res_75 = metric_75(preds, gts)

    results = dict(res_main)
    results["_merge_selected"] = dataset.chosen_variant
    results["_merge_variants"] = dataset.variant_metrics

    for cls in classes:
        key = f"bbox_{cls}_precision"
        if key in res_50:
            results[f"bbox_{cls}_mAP50"] = res_50[key]
        if key in res_75:
            results[f"bbox_{cls}_mAP75"] = res_75[key]

    prediction_path = Path(task_cfg["dataset"]["prediction"]["data_path"])
    output_name = f"{prediction_path.stem}_detection_eval_metrics.json"
    output_path = output_dir / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OmniDocBench detection evaluation and persist metrics.")
    parser.add_argument("--config", required=True, type=Path, help="Path to the YAML config.")
    parser.add_argument(
        "--output-dir",
        default=ROOT / "result",
        type=Path,
        help="Directory where the metrics JSON will be written.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    output_path = evaluate_detection(cfg, args.output_dir)
    print(f"Wrote detection metrics to {output_path}")


if __name__ == "__main__":
    main()
