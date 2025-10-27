#!/usr/bin/env python3
"""
Batch DocTags inference for Docling-Granite models on OmniDocBench images.

This script walks an OmniDocBench manifest, runs `python -m mlx_vlm.generate`
for each page image, and stores the generated DocTags output as a `.txt` file
mirroring the image path. Progress and per-image runtime are logged to stdout
to help track long-running jobs.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_PROMPT = "Convert this page to docling."


@dataclass
class PageItem:
    image_path: Path
    page_index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Docling DocTags inference over OmniDocBench images."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to OmniDocBench manifest JSON.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        required=True,
        help="Directory containing page images referenced by the manifest.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Where to store DocTags outputs (.txt files).",
    )
    parser.add_argument(
        "--model",
        default="ibm-granite/granite-docling-258M-mlx",
        help="Model identifier passed to mlx_vlm.generate.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum generated tokens for mlx_vlm.generate.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for mlx_vlm.generate.",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Prompt passed to the model.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of pages to process. Omit for full dataset.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images whose DocTags output already exists.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def load_manifest(manifest_path: Path) -> List[PageItem]:
    raw = json.loads(manifest_path.read_text())
    pages: List[PageItem] = []
    for idx, entry in enumerate(raw):
        page_info = entry.get("page_info") or {}
        image_path = page_info.get("image_path")
        if not image_path:
            logging.warning("Skipping entry %s without image_path", idx)
            continue
        pages.append(PageItem(image_path=Path(image_path), page_index=idx))
    return pages


def build_command(
    model: str,
    max_tokens: int,
    temperature: float,
    prompt: str,
    image_path: Path,
) -> Sequence[str]:
    return [
        "python",
        "-m",
        "mlx_vlm.generate",
        "--model",
        model,
        "--max-tokens",
        str(max_tokens),
        "--temperature",
        str(temperature),
        "--prompt",
        prompt,
        "--image",
        str(image_path),
    ]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run_inference(
    page: PageItem,
    images_dir: Path,
    output_dir: Path,
    command_args: Sequence[str],
    skip_existing: bool,
) -> float:
    image_path = images_dir / page.image_path
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    output_path = output_dir / page.image_path.with_suffix(".txt")
    if skip_existing and output_path.exists():
        logging.info("Skipping %s (already exists)", page.image_path)
        return 0.0

    ensure_parent(output_path)
    logging.info("Running DocTags inference for %s", page.image_path)
    start = time.perf_counter()
    proc = subprocess.run(
        command_args,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start

    if proc.returncode != 0:
        logging.error(
            "Inference failed for %s (rc=%s). stderr:\n%s",
            page.image_path,
            proc.returncode,
            proc.stderr,
        )
        raise RuntimeError(f"DocTags inference failed for {page.image_path}")

    output_path.write_text(proc.stdout)
    logging.info("Finished %s in %.2fs", page.image_path, elapsed)
    return elapsed


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    pages = load_manifest(args.manifest)
    if args.limit is not None and args.limit > 0:
        pages = pages[: args.limit]

    logging.info(
        "Starting DocTags inference for %d pages using model %s",
        len(pages),
        args.model,
    )

    durations: List[float] = []
    for idx, page in enumerate(pages, start=1):
        cmd = build_command(
            model=args.model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            prompt=args.prompt,
            image_path=args.images_dir / page.image_path,
        )
        logging.debug("Command: %s", " ".join(cmd))
        try:
            elapsed = run_inference(
                page=page,
                images_dir=args.images_dir,
                output_dir=args.output_dir,
                command_args=cmd,
                skip_existing=args.skip_existing,
            )
        except Exception:
            logging.exception("Error while processing %s", page.image_path)
            raise
        durations.append(elapsed)
        logging.info(
            "Processed %d/%d pages (latest %.2fs, avg %.2fs)",
            idx,
            len(pages),
            elapsed,
            sum(durations) / len(durations) if durations else 0.0,
        )

    if durations:
        total = sum(durations)
        logging.info(
            "All done: %d pages, total %.2fs, avg %.2fs",
            len(durations),
            total,
            total / len(durations),
        )
    else:
        logging.info("Nothing was processed.")


if __name__ == "__main__":
    main()
