import argparse
import json
from copy import deepcopy
from pathlib import Path

from doclayout_yolo import YOLOv10
from doclayout_yolo.nn.tasks import YOLOv10DetectionModel
from torch.serialization import add_safe_globals

add_safe_globals([YOLOv10DetectionModel])

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    def tqdm(iterable, **kwargs):
        return iterable


def load_ground_truth(gt_path):
    with open(gt_path, "r") as f:
        return json.load(f)


def format_poly(x1, y1, x2, y2):
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def run_inference(model_path, images_dir, gt_data, imgsz, conf, batch, limit=None):
    model = YOLOv10(model_path)
    total = len(gt_data) if limit is None else min(limit, len(gt_data))
    gt_subset = gt_data[:total]

    image_paths = []
    for item in gt_subset:
        image_path = Path(images_dir) / item["page_info"]["image_path"]
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        image_paths.append(str(image_path))

    results = []
    for start in tqdm(range(0, len(image_paths), batch), desc="Inferencing", unit="img"):
        chunk_paths = image_paths[start:start + batch]
        chunk_gt = gt_subset[start:start + len(chunk_paths)]
        outputs = model.predict(
            chunk_paths,
            imgsz=imgsz,
            conf=conf,
            batch=batch,
            verbose=False,
            save=False,
        )
        for gt_item, res in zip(chunk_gt, outputs):
            layout_items = []
            boxes = res.boxes
            if boxes is not None and len(boxes) > 0:
                data = boxes.data.cpu().tolist()
                for idx, det in enumerate(data):
                    x1, y1, x2, y2, score, cls = det
                    cls = int(cls)
                    layout_items.append({
                        "category_type": res.names[cls],
                        "poly": format_poly(float(x1), float(y1), float(x2), float(y2)),
                        "score": float(score),
                        "ignore": False,
                        "order": None,
                        "anno_id": idx,
                        "line_with_spans": [],
                    })
            page_info = deepcopy(gt_item["page_info"])
            results.append({
                "layout_dets": layout_items,
                "extra": {},
                "page_info": page_info,
            })
    return results


def main():
    parser = argparse.ArgumentParser(description="Run DocLayout-YOLO on OmniDocBench images and save predictions.")
    parser.add_argument("--model", required=True, help="Path to DocLayout-YOLO weight file.")
    parser.add_argument("--gt", required=True, help="Path to OmniDocBench ground truth JSON.")
    parser.add_argument("--images", required=True, help="Directory containing OmniDocBench images.")
    parser.add_argument("--output", required=True, help="Path to save predictions JSON.")
    parser.add_argument("--imgsz", type=int, default=1024, help="Inference image size.")
    parser.add_argument("--conf", type=float, default=0.2, help="Confidence threshold.")
    parser.add_argument("--batch", type=int, default=4, help="Batch size for inference.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of pages.")
    args = parser.parse_args()

    gt_data = load_ground_truth(args.gt)
    predictions = run_inference(
        model_path=args.model,
        images_dir=args.images,
        gt_data=gt_data,
        imgsz=args.imgsz,
        conf=args.conf,
        batch=max(1, args.batch),
        limit=args.limit,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(predictions, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
