#!/usr/bin/env python3
"""
Submit images to the Marker OCR API and persist the final outputs.

Example
-------
python tools/model_infer/run_marker_api.py \
    --input-dir data/publicBench_data/images \
    --output-dir data/publicBench_data/predictions/raw/marker
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

API_URL = "https://www.datalab.to/api/v1/marker"
DEFAULT_API_KEY = "pyGdTRWw0-RokN3eUbI_os2gZ032l8wjXBSn_cCcmUc"
DEFAULT_PAYLOAD = {
    "file_url": "",
    "max_pages": "123",
    "page_range": "",
    "langs": "",
    "force_ocr": "false",
    "format_lines": "false",
    "paginate": "false",
    "strip_existing_ocr": "false",
    "disable_image_extraction": "false",
    "disable_ocr_math": "false",
    "use_llm": "true",
    "mode": "fast",
    "output_format": "json,markdown,html",
    "skip_cache": "false",
    "save_checkpoint": "false",
    "block_correction_prompt": "",
    "page_schema": "",
    "segmentation_schema": "",
    "additional_config": "",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Marker OCR over a directory of images.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing images to process.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where OCR results will be written.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=3.0,
        help="Seconds to wait between status checks.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Maximum seconds to wait for a single document before failing.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-run requests even if output files already exist.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of concurrent submissions to send before waiting for results.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optionally limit how many files to process (useful for quick experiments).",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("MARKER_API_KEY", DEFAULT_API_KEY),
        help="API key used to authenticate against the Marker endpoint.",
    )
    return parser.parse_args()


def load_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
    images = sorted(p for p in input_dir.iterdir() if p.is_file())
    if not images:
        raise ValueError(f"No files found under {input_dir}")
    return images


def submit_job(image_path: Path, session: requests.Session) -> str:
    content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    with image_path.open("rb") as file_handle:
        files = {"file": (image_path.name, file_handle, content_type)}
        response = session.post(API_URL, data=DEFAULT_PAYLOAD, files=files, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        error = payload.get("error") or "Unknown error"
        raise RuntimeError(f"Marker submission failed for {image_path}: {error}")
    request_url = payload.get("request_check_url")
    if not request_url:
        raise RuntimeError(f"Missing request_check_url in response for {image_path}")
    return request_url


def write_outputs(result: Dict[str, Any], image_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = image_path.stem

    json_path = output_dir / f"{stem}.json"

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=2)

def chunked(items: List[Path], batch_size: int) -> Iterable[List[Path]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def process_batch(
    batch: List[Path],
    *,
    output_dir: Path,
    session: requests.Session,
    poll_interval: float,
    timeout: float,
    overwrite: bool,
) -> int:
    pending: Dict[Path, Dict[str, Any]] = {}
    completed = 0

    for image_path in batch:
        json_output = output_dir / f"{image_path.stem}.json"
        if json_output.exists() and not overwrite:
            print(f"[SKIP] {image_path.name} -> output already exists.")
            completed += 1
            continue
        try:
            print(f"[SUBMIT] {image_path.name}")
            request_url = submit_job(image_path, session)
            pending[image_path] = {
                "url": request_url,
                "start_time": time.time(),
                "last_error": None,
            }
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Submitting {image_path.name}: {exc}", file=sys.stderr)

    while pending:
        now = time.time()
        for image_path in list(pending):
            meta = pending[image_path]
            if now - meta["start_time"] > timeout:
                print(
                    f"[ERROR] Timeout waiting for {image_path.name} after {timeout:.0f}s",
                    file=sys.stderr,
                )
                pending.pop(image_path)
                continue

            try:
                response = session.get(meta["url"], timeout=60)
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:  # noqa: BLE001
                meta["last_error"] = str(exc)
                continue

            status = payload.get("status")
            if status == "complete":
                if payload.get("success") is False:
                    error = payload.get("error") or "Unknown error"
                    print(f"[ERROR] Marker failure for {image_path.name}: {error}", file=sys.stderr)
                else:
                    write_outputs(payload, image_path, output_dir)
                    print(f"[DONE] {image_path.name}")
                    completed += 1
                pending.pop(image_path)
            elif status in {"failed", "error"}:
                error = payload.get("error") or "Unknown error"
                print(f"[ERROR] Marker failure for {image_path.name}: {error}", file=sys.stderr)
                pending.pop(image_path)

        if pending:
            time.sleep(poll_interval)

    return completed


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print("Missing API key. Set MARKER_API_KEY or use --api-key.", file=sys.stderr)
        return 1

    session = requests.Session()
    session.headers.update({"X-API-Key": args.api_key})

    try:
        images = load_images(args.input_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Error discovering input files: {exc}", file=sys.stderr)
        return 1

    if args.limit is not None:
        images = images[: args.limit]

    if args.batch_size < 1:
        print("Batch size must be >= 1.", file=sys.stderr)
        return 1

    total_start = time.time()
    total_completed = 0

    for batch_index, batch in enumerate(chunked(images, args.batch_size), start=1):
        print(f"[BATCH] {batch_index} submitting {len(batch)} files.")
        total_completed += process_batch(
            batch,
            output_dir=args.output_dir,
            session=session,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            overwrite=args.overwrite,
        )

    elapsed = time.time() - total_start
    print(f"[SUMMARY] Processed {total_completed} file(s) in {elapsed:.2f}s.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
