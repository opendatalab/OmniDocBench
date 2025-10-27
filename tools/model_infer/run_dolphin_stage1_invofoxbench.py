#!/usr/bin/env python3
"""
Utility script to run Dolphin stage-1 layout inference on InvofoxBench images.

This script loads the Dolphin model (stage-1) and processes images from the
InvofoxBench dataset, recording latency per page and saving the bounding boxes
plus labels returned by the model.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
import sys
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence, Tuple

import torch
from PIL import Image
from transformers import AutoProcessor, VisionEncoderDecoderModel

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
sys.path.insert(0, str(REPO_ROOT / "Dolphin"))

from utils.utils import parse_layout_string

LAYOUT_PROMPT = "Parse the reading order of this document."


class DolphinHFStage1:
    """Minimal HF-based Dolphin wrapper with CPU-friendly inference."""

    def __init__(self, model_path: str, device_preference: str = "auto") -> None:
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_path)
        preference = device_preference.lower()
        if preference not in {"auto", "cpu", "cuda", "mps"}:
            raise ValueError(f"Unsupported device preference: {device_preference}")

        if preference == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA requested but not available.")
            self.device = "cuda"
        elif preference == "mps":
            if not torch.backends.mps.is_available():
                raise RuntimeError("MPS requested but not available.")
            self.device = "mps"
        elif preference == "cpu":
            self.device = "cpu"
        else:  # auto
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

        self.model.to(self.device)
        if self.device == "cuda":
            self.model = self.model.half()
        else:
            self.model = self.model.float()
        self.tokenizer = self.processor.tokenizer

    def chat(self, prompt, image):
        is_batch = isinstance(image, list)

        if not is_batch:
            images = [image]
            prompts = [prompt]
        else:
            images = image
            prompts = prompt if isinstance(prompt, list) else [prompt] * len(images)

        batch_inputs = self.processor(images, return_tensors="pt", padding=True)
        if self.device == "cuda":
            batch_pixel_values = batch_inputs.pixel_values.to(self.device, dtype=torch.float16)
        else:
            batch_pixel_values = batch_inputs.pixel_values.to(self.device, dtype=torch.float32)

        formatted_prompts = []
        for p in prompts:
            text = p
            if not text.startswith("<s>"):
                text = "<s>" + text
            if "<Answer/>" not in text:
                text = text + " <Answer/>"
            formatted_prompts.append(text)

        batch_prompt_inputs = self.tokenizer(
            formatted_prompts,
            add_special_tokens=False,
            return_tensors="pt",
            padding=True,
        )

        batch_prompt_ids = batch_prompt_inputs.input_ids.to(self.device)
        batch_attention_mask = batch_prompt_inputs.attention_mask.to(self.device)

        with torch.inference_mode():
            outputs = self.model.generate(
                pixel_values=batch_pixel_values,
                decoder_input_ids=batch_prompt_ids,
                decoder_attention_mask=batch_attention_mask,
                min_length=1,
                max_length=4096,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
                do_sample=False,
                num_beams=1,
                repetition_penalty=1.1,
                temperature=1.0,
            )

        sequences = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)

        results = []
        for prompt_text, sequence in zip(formatted_prompts, sequences):
            cleaned = sequence.replace(prompt_text, "").replace("<pad>", "").replace("</s>", "").strip()
            results.append(cleaned)

        if not is_batch:
            return results[0]
        return results


@dataclass
class Stage1Element:
    label: str
    bbox_norm: Tuple[float, float, float, float]
    bbox_abs: Tuple[int, int, int, int]


@dataclass
class Stage1Result:
    image_name: str
    image_path: str
    width: int
    height: int
    latency_sec: float
    layout_raw: str
    elements: List[Stage1Element]


def _sorted_image_paths(image_dir: Path) -> List[Path]:
    supported_suffixes = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    candidates = [p for p in image_dir.iterdir() if p.suffix.lower() in supported_suffixes]
    return sorted(candidates, key=lambda p: p.name)


def _norm_to_abs(coords: Sequence[float], width: int, height: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = coords
    abs_coords = (
        int(round(max(0.0, min(1.0, x1)) * width)),
        int(round(max(0.0, min(1.0, y1)) * height)),
        int(round(max(0.0, min(1.0, x2)) * width)),
        int(round(max(0.0, min(1.0, y2)) * height)),
    )

    # Ensure boxes have positive area
    x1_abs, y1_abs, x2_abs, y2_abs = abs_coords
    if x2_abs <= x1_abs:
        x2_abs = min(width, x1_abs + 1)
    if y2_abs <= y1_abs:
        y2_abs = min(height, y1_abs + 1)

    return x1_abs, y1_abs, x2_abs, y2_abs


def _warm_up(model: DolphinHFStage1, image: Image.Image) -> None:
    _ = model.chat(LAYOUT_PROMPT, image)


def _chunked(sequence: Sequence[Path], chunk_size: int) -> Iterator[List[Path]]:
    for idx in range(0, len(sequence), chunk_size):
        yield list(sequence[idx : idx + chunk_size])


def _run_stage1_batch(model: DolphinHFStage1, batch_paths: List[Path]) -> Tuple[List[Stage1Result], float]:
    """Run stage-1 layout inference on a batch of images."""
    images: List[Image.Image] = []
    dimensions: List[Tuple[int, int]] = []
    for path in batch_paths:
        image = Image.open(path).convert("RGB")
        images.append(image)
        dimensions.append(image.size)

    prompts = [LAYOUT_PROMPT] * len(images)
    t0 = time.perf_counter()
    layout_outputs = model.chat(prompts, images)
    batch_latency = time.perf_counter() - t0

    for image in images:
        image.close()

    per_image_latency = batch_latency / len(batch_paths)
    batch_results: List[Stage1Result] = []
    for path, layout_raw, dims in zip(batch_paths, layout_outputs, dimensions):
        width, height = dims
        parsed_layout = parse_layout_string(layout_raw)
        elements = [
            Stage1Element(
                label=label,
                bbox_norm=tuple(coords),
                bbox_abs=_norm_to_abs(coords, width, height),
            )
            for coords, label in parsed_layout
        ]
        batch_results.append(
            Stage1Result(
                image_name=path.name,
                image_path=str(path),
                width=width,
                height=height,
                latency_sec=per_image_latency,
                layout_raw=layout_raw,
                elements=elements,
            )
        )
        print(f"processed {len(batch_results)}/{len(images)}")

    return batch_results, batch_latency


def _save_results(results: Iterable[Stage1Result], output_path: Path) -> None:
    serialisable = [asdict(result) for result in results]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Dolphin stage-1 inference on InvofoxBench images.")
    parser.add_argument(
        "--model_path",
        type=Path,
        default=REPO_ROOT / "Dolphin" / "hf_model",
        help="Path to the local Hugging Face Dolphin weights (directory).",
    )
    parser.add_argument(
        "--image_dir",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "images",
        help="Directory containing InvofoxBench page images.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to process (default: all).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "Dolphin" / "results" / "dolphin_stage1_invofoxbench_full.json",
        help="Where to save the JSON results.",
    )
    parser.add_argument(
        "--skip_warmup",
        action="store_true",
        help="If set, do not run an additional warm-up pass before timing.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Number of images to process per forward pass (default: 1).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device selection (default: auto).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {args.image_dir}")
    if not args.model_path.exists():
        raise FileNotFoundError(f"Model path not found: {args.model_path}")

    model = DolphinHFStage1(str(args.model_path), device_preference=args.device)
    batch_size = max(1, args.batch_size)

    image_paths = _sorted_image_paths(args.image_dir)
    if not image_paths:
        raise RuntimeError(f"No supported images found under {args.image_dir}")

    if args.limit is not None:
        image_paths = image_paths[: args.limit]

    total_images = len(image_paths)
    if total_images == 0:
        raise RuntimeError("No images selected for processing.")

    print(f"Running Dolphin stage-1 on {total_images} images (batch size {batch_size}, device {model.device}).")

    if not args.skip_warmup:
        with Image.open(image_paths[0]) as warm_image:
            _warm_up(model, warm_image.convert("RGB"))

    results = []
    total_time = 0.0
    processed = 0
    total_batches = (total_images + batch_size - 1) // batch_size

    for batch_idx, batch_paths in enumerate(_chunked(image_paths, batch_size), start=1):
        batch_results, batch_latency = _run_stage1_batch(model, batch_paths)
        results.extend(batch_results)
        total_time += batch_latency
        processed += len(batch_results)

        per_image_latency = batch_latency / len(batch_results)
        start_idx = processed - len(batch_results) + 1
        end_idx = processed
        print(
            f"Batch {batch_idx:03d}/{total_batches:03d}: images {start_idx}-{end_idx} "
            f"in {batch_latency:.3f}s (avg {per_image_latency:.3f}s)"
        )
        for global_idx, res in zip(range(start_idx, end_idx + 1), batch_results):
            print(f"  [{global_idx:04d}/{total_images:04d}] {res.image_name}: {res.latency_sec:.3f}s (batch_avg)")

    avg_latency = sum(r.latency_sec for r in results) / len(results)
    print(f"Completed {len(results)} images in {total_time:.3f}s; average latency {avg_latency:.3f}s.")

    _save_results(results, args.output)
    print(f"Saved detailed results to {args.output}")


if __name__ == "__main__":
    main()

