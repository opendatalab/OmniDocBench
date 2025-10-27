#!/usr/bin/env python3
"""Split per-page OCR results into individual JSON files.

The script scans every subdirectory inside the given base path, expecting each
directory to contain an ``ocr_result.json`` file with a list of page-level OCR
records. Each list entry is written out to ``{document_id}_{page_no}.json`` in
the output directory, where ``page_no`` is zero-based.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"


def split_ocr_results(base_dir: Path, output_dir: Path) -> int:
    """Split each ``ocr_result.json`` in ``base_dir`` into per-page files."""
    created_files = 0

    for document_dir in sorted(_iter_document_dirs(base_dir)):
        document_id = document_dir.name
        ocr_file = document_dir / "ocr_result.json"

        try:
            with ocr_file.open("r", encoding="utf-8") as handle:
                pages = json.load(handle)
        except FileNotFoundError:
            print(f"[WARN] Missing ocr_result.json in {document_dir}")
            continue

        if not isinstance(pages, list):
            print(f"[WARN] Unexpected format in {ocr_file}; expected list.")
            continue

        for index, page_data in enumerate(pages):
            page_number = _derive_zero_based_page(page_data, index)
            output_path = output_dir / f"{document_id}_{page_number}.json"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as handle:
                json.dump(page_data, handle, ensure_ascii=False, indent=2)

            created_files += 1

    return created_files


def _iter_document_dirs(base_dir: Path) -> Iterable[Path]:
    for candidate in base_dir.iterdir():
        if candidate.is_dir():
            yield candidate


def _derive_zero_based_page(page_data: dict, fallback_index: int) -> int:
    """Return the target zero-based page number for a page payload."""
    page_value = page_data.get("page")
    try:
        zero_based = int(page_value) - 1
    except (TypeError, ValueError):
        zero_based = fallback_index

    if zero_based < 0:
        zero_based = fallback_index

    return zero_based


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "ocrs",
        help="Directory that contains OCR result subfolders (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_ROOT / "InvofoxBench_data" / "ocrs",
        help="Directory to write per-page OCR files (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    created = split_ocr_results(args.base, args.output)
    print(f"[INFO] Generated {created} per-page OCR files in {args.output}")


if __name__ == "__main__":
    main()
