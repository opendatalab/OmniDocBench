#!/usr/bin/env python3
"""
Run MonkeyOCR-pro-1.2B inference on a batch of images and record per-image latency.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
MONKEYOCR_ROOT = REPO_ROOT / "MonkeyOCR"
sys.path.insert(0, str(MONKEYOCR_ROOT))

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

from magic_pdf.model.custom_model import MonkeyOCR  # noqa: E402
from parse import parse_file  # noqa: E402

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf"}


@dataclass
class InferenceRecord:
    image_name: str
    image_path: str
    output_path: str
    latency_sec: float


def sorted_image_paths(image_dir: Path, limit: int | None = None) -> List[Path]:
    candidates = sorted(
        [p for p in image_dir.iterdir() if p.suffix.lower() in SUPPORTED_SUFFIXES],
        key=lambda p: p.name,
    )
    if limit is not None:
        candidates = candidates[:limit]
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch inference with MonkeyOCR-pro-1.2B.")
    parser.add_argument(
        "--config",
        type=Path,
        default=MONKEYOCR_ROOT / "model_configs_local.yaml",
        help="Path to MonkeyOCR configuration file.",
    )
    parser.add_argument(
        "--image_dir",
        type=Path,
        default=REPO_ROOT / "dataset",
        help="Directory containing input images or PDFs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of files to process (default: 10).",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=MONKEYOCR_ROOT / "output_dataset_first10",
        help="Directory where MonkeyOCR outputs will be written.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=MONKEYOCR_ROOT / "results" / "monkeyocr_dataset_first10_summary.json",
        help="Path to store JSON summary with per-file latency.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {args.image_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading MonkeyOCR with config: {args.config}")
    model = MonkeyOCR(str(args.config))

    image_paths = sorted_image_paths(args.image_dir, args.limit)
    if not image_paths:
        raise RuntimeError(f"No supported files found in {args.image_dir}")

    records: List[InferenceRecord] = []
    total_time = 0.0

    for idx, image_path in enumerate(image_paths, start=1):
        start = time.perf_counter()
        result_path = parse_file(str(image_path), str(args.output_dir), model)
        latency = time.perf_counter() - start
        total_time += latency
        print(f"[{idx:02d}/{len(image_paths):02d}] {image_path.name}: {latency:.3f}s → {result_path}")
        records.append(
            InferenceRecord(
                image_name=image_path.name,
                image_path=str(image_path),
                output_path=str(result_path),
                latency_sec=latency,
            )
        )

    avg_latency = total_time / len(records)
    print(f"Completed {len(records)} files in {total_time:.2f}s (avg {avg_latency:.3f}s).")

    with args.summary.open("w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2)
    print(f"Summary saved to {args.summary}")


if __name__ == "__main__":
    main()

