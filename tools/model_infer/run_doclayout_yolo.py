import argparse
import json
from pathlib import Path
from typing import Iterable, List

from doclayout_yolo import YOLOv10
from doclayout_yolo.nn.tasks import YOLOv10DetectionModel
from torch.serialization import add_safe_globals

add_safe_globals([YOLOv10DetectionModel])

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    def tqdm(iterable, **kwargs):
        return iterable


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


def format_poly(x1: float, y1: float, x2: float, y2: float) -> List[float]:
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def iter_image_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image type: {root.suffix}")
        yield root
        return

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def ensure_exists(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return path


def get_dimensions(result, image_path: Path) -> tuple[int | None, int | None]:
    if hasattr(result, "orig_shape") and result.orig_shape:
        height, width = result.orig_shape[:2]
        return int(width), int(height)
    try:
        from PIL import Image  # type: ignore

        with Image.open(image_path) as img:
            width, height = img.size
            return int(width), int(height)
    except Exception:
        return None, None


def relative_image_path(image_path: Path, root_dir: Path) -> str:
    try:
        return str(image_path.relative_to(root_dir))
    except ValueError:
        return image_path.name


def run_inference(model_path: Path, images_root: Path, imgsz: int, conf: float, batch: int, limit: int | None):
    model = YOLOv10(str(model_path))

    image_paths = list(iter_image_files(images_root))
    if not image_paths:
        raise FileNotFoundError(f"No images found under {images_root}")

    total = len(image_paths)
    if limit is not None:
        total = min(limit, total)
        image_paths = image_paths[:total]

    results = []
    processed = 0
    for start in tqdm(range(0, len(image_paths), batch), desc="Inferencing", unit="img"):
        chunk_paths = image_paths[start:start + batch]
        output = model.predict(
            [str(p) for p in chunk_paths],
            imgsz=imgsz,
            conf=conf,
            batch=batch,
            verbose=False,
            save=False,
        )
        for image_path, pred in zip(chunk_paths, output):
            width, height = get_dimensions(pred, image_path)
            layout_items = []
            boxes = getattr(pred, "boxes", None)
            if boxes is not None and len(boxes) > 0:
                data = boxes.data.cpu().tolist()
                for idx, det in enumerate(data):
                    x1, y1, x2, y2, score, cls = det
                    cls = int(cls)
                    layout_items.append({
                        "category_type": pred.names[cls],
                        "poly": format_poly(float(x1), float(y1), float(x2), float(y2)),
                        "score": float(score),
                        "ignore": False,
                        "order": None,
                        "anno_id": idx,
                        "line_with_spans": [],
                    })

            page_idx = processed + 1
            page_info = {
                "page_no": page_idx,
                "width": width,
                "height": height,
                "image_path": relative_image_path(image_path, images_root),
                "page_attribute": {},
            }
            results.append({
                "layout_dets": layout_items,
                "extra": {},
                "page_info": page_info,
            })
            processed += 1
    return results


def main():
    parser = argparse.ArgumentParser(description="Run DocLayout-YOLO inference over images in a directory.")
    parser.add_argument("--model", required=True, help="Path to DocLayout-YOLO weight file.")
    parser.add_argument("--images", required=True, help="Directory (or single image) with inputs.")
    parser.add_argument("--output", required=True, help="Path to save predictions JSON.")
    parser.add_argument("--imgsz", type=int, default=1024, help="Inference image size.")
    parser.add_argument("--conf", type=float, default=0.2, help="Confidence threshold.")
    parser.add_argument("--batch", type=int, default=4, help="Batch size for inference.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of images.")
    args = parser.parse_args()

    images_root = ensure_exists(Path(args.images))
    predictions = run_inference(
        model_path=Path(args.model),
        images_root=images_root,
        imgsz=args.imgsz,
        conf=args.conf,
        batch=max(1, args.batch),
        limit=args.limit,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
