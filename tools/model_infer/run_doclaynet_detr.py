#!/usr/bin/env python3
"""
Run DocLayNet Deformable DETR inference on OmniDocBench images.

This script loads the Hugging Face model `Aryn/deformable-detr-DocLayNet`
from a local clone (for offline use) and performs layout detection on the
first N images of the OmniDocBench dataset. It records per-page latency and
exports detections (label, confidence, bounding boxes) to JSON.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence

import torch
from PIL import Image
from transformers import AutoImageProcessor, DeformableDetrForObjectDetection


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
DEFAULT_MODEL_DIR = REPO_ROOT / "DETR_DocLayNet"
DEFAULT_IMAGE_DIR = DATA_ROOT / "OmniDocBench_data" / "images"
DEFAULT_OUTPUT = DEFAULT_MODEL_DIR / "results" / "doclaynet_stage1_omnidocbench_first10.json"


@dataclass
class Detection:
    label: str
    score: float
    bbox_xyxy: Sequence[float]
    bbox_xywh: Sequence[float]


@dataclass
class PageResult:
    image_name: str
    image_path: str
    width: int
    height: int
    latency_sec: float
    detections: List[Detection]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DocLayNet Deformable DETR inference on OmniDocBench images.")
    parser.add_argument(
        "--model_path",
        type=Path,
        default=DEFAULT_MODEL_DIR,
        help="Path to local clone of Aryn/deformable-detr-DocLayNet.",
    )
    parser.add_argument(
        "--image_dir",
        type=Path,
        default=DEFAULT_IMAGE_DIR,
        help="Directory containing OmniDocBench page images.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of images to process (default: 10).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Confidence threshold for detections (default: 0.5).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write JSON results.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to run inference on (default: auto).",
    )
    parser.add_argument(
        "--skip_warmup",
        action="store_true",
        help="If set, do not run a warm-up inference before timed runs.",
    )
    return parser.parse_args()


def _select_device(preference: str) -> torch.device:
    pref = preference.lower()
    if pref == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available.")
        return torch.device("cuda")
    if pref == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("MPS requested but not available.")
        return torch.device("mps")
    if pref == "cpu":
        return torch.device("cpu")

    # auto
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _sorted_image_paths(image_dir: Path) -> List[Path]:
    supported = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    return sorted([p for p in image_dir.iterdir() if p.suffix.lower() in supported], key=lambda x: x.name)


def _to_xywh(box_xyxy: Sequence[float]) -> Sequence[float]:
    x0, y0, x1, y1 = box_xyxy
    w = max(0.0, x1 - x0)
    h = max(0.0, y1 - y0)
    return [x0, y0, w, h]


def _load_model(model_dir: Path, device: torch.device):
    processor = AutoImageProcessor.from_pretrained(model_dir)
    model = DeformableDetrForObjectDetection.from_pretrained(model_dir)
    model.to(device)
    model.eval()
    return processor, model


def _run_inference(
    processor: AutoImageProcessor,
    model: DeformableDetrForObjectDetection,
    image_path: Path,
    device: torch.device,
    threshold: float,
) -> PageResult:
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        width, height = image.size

        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.inference_mode():
            start = time.perf_counter()
            outputs = model(**inputs)
            latency = time.perf_counter() - start

        target_sizes = torch.tensor([[height, width]], device=device)
        post_process = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=threshold)[0]

        detections = []
        for score, label_id, bbox in zip(post_process["scores"], post_process["labels"], post_process["boxes"]):
            bbox_xyxy = [round(float(x), 2) for x in bbox.tolist()]
            detections.append(
                Detection(
                    label=model.config.id2label[label_id.item()],
                    score=round(float(score.item()), 4),
                    bbox_xyxy=bbox_xyxy,
                    bbox_xywh=[round(v, 2) for v in _to_xywh(bbox_xyxy)],
                )
            )

    return PageResult(
        image_name=image_path.name,
        image_path=str(image_path),
        width=width,
        height=height,
        latency_sec=latency,
        detections=detections,
    )


def main() -> None:
    args = parse_args()

    if not args.model_path.exists():
        raise FileNotFoundError(f"Model path not found: {args.model_path}")
    if not args.image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {args.image_dir}")

    device = _select_device(args.device)
    processor, model = _load_model(args.model_path, device)

    image_paths = _sorted_image_paths(args.image_dir)
    if not image_paths:
        raise RuntimeError(f"No supported images found in {args.image_dir}")

    image_paths = image_paths[: args.limit]
    total_images = len(image_paths)
    print(
        f"DocLayNet DETR inference on {total_images} images "
        f"(threshold={args.threshold}, device={device.type})."
    )

    if not args.skip_warmup:
        _ = _run_inference(processor, model, image_paths[0], device, args.threshold)
        print("Warm-up inference completed.")

    results: List[PageResult] = []
    total_time = 0.0
    for idx, image_path in enumerate(image_paths, start=1):
        page_result = _run_inference(processor, model, image_path, device, args.threshold)
        results.append(page_result)
        total_time += page_result.latency_sec
        print(f"[{idx:02d}/{total_images:02d}] {page_result.image_name}: {page_result.latency_sec:.3f}s "
              f"({len(page_result.detections)} detections)")

    avg_latency = total_time / total_images if total_images else 0.0
    print(f"Completed {total_images} images in {total_time:.3f}s; avg latency {avg_latency:.3f}s.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump([asdict(res) for res in results], f, indent=2)
    print(f"Saved detailed detections to {args.output}")


if __name__ == "__main__":
    main()
