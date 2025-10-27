#!/usr/bin/env python3
"""Utility to print consolidated detection metrics tables."""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[2]
MODEL_ORDER: Sequence[str] = (
    "landingai",
    "dotsocr_pdf",
    "dotsocr",
    "dotsocr_dpi",
    "marker",
    "reducto",
    "minerU",
    "monkey_pro_3B",
    "deepseek",
    "pp",
    "yolo",
)


def load_aggregate(base_dir: Path, model: str) -> Dict:
    path = base_dir / model / "detection_eval" / f"{model}_aggregate_metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"Aggregate metrics not found for '{model}' at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_table(headers: Sequence[str], rows: List[List[str]], align_right: Iterable[int]) -> str:
    align_right = set(align_right)
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    lines = []
    header_row = " | ".join(
        header.ljust(widths[idx]) if idx not in align_right else header.rjust(widths[idx])
        for idx, header in enumerate(headers)
    )
    separator = "-+-".join("-" * width for width in widths)
    lines.append(header_row)
    lines.append(separator)
    for row in rows:
        formatted = []
        for idx, value in enumerate(row):
            if idx in align_right:
                formatted.append(value.rjust(widths[idx]))
            else:
                formatted.append(value.ljust(widths[idx]))
        lines.append(" | ".join(formatted))
    return "\n".join(lines)


def build_metric_rows(base_dir: Path, models: Sequence[str]) -> List[List[str]]:
    rows: List[List[str]] = []
    for model in models:
        data = load_aggregate(base_dir, model)
        per_class = data.get("per_class", {})
        def failure_pct(cls: str) -> str:
            entry = per_class.get(cls)
            if not entry:
                return "---"
            rate = entry.get("failure_rate")
            if rate is None:
                return "---"
            return f"{rate * 100:.1f}"

        rows.append(
            [
                model,
                f"{data.get('mean_iou', 0.0):.3f}",
                f"{int(data.get('total_matches', 0))}",
                f"{int(data.get('total_false_negatives', 0))}",
                f"{int(data.get('total_false_positives', 0))}",
                failure_pct("text"),
                failure_pct("table"),
                failure_pct("figure"),
            ]
        )
    return rows


def build_confusion_rows(base_dir: Path, models: Sequence[str]) -> List[List[str]]:
    rows: List[List[str]] = []
    for model in models:
        data = load_aggregate(base_dir, model)
        per_class = data.get("per_class", {})
        confusion = data.get("confusion", {})

        def pct(src: str, dst: str) -> str:
            info = per_class.get(src)
            total = info.get("gt_total") if info else 0.0
            value = confusion.get(src, {}).get(dst, 0.0)
            if not total:
                return "---"
            return f"{(value / total) * 100:.1f}"

        rows.append(
            [
                model,
                pct("text", "table"),
                pct("text", "missing"),
                pct("text", "figure"),
                pct("table", "text"),
                pct("table", "missing"),
                pct("table", "figure"),
                pct("figure", "text"),
                pct("figure", "missing"),
                pct("figure", "table"),
            ]
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Print detection metric summary tables.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=ROOT / "data" / "publicBench_data" / "results" / "new_metrics",
        help="Root directory containing per-model detection_eval folders.",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=list(MODEL_ORDER),
        help="Override model order. Defaults to predefined ordering.",
    )
    args = parser.parse_args()
    base_dir: Path = args.base_dir
    models: Sequence[str] = args.models or MODEL_ORDER

    metric_table = format_table(
        headers=[
            "Model",
            "Mean IoU",
            "Matches",
            "FN",
            "FP",
            "Text fail %",
            "Table fail %",
            "Figure fail %",
        ],
        rows=build_metric_rows(base_dir, models),
        align_right={1, 2, 3, 4, 5, 6, 7},
    )
    confusion_table = format_table(
        headers=[
            "Model",
            "Text→Table %",
            "Text→Missing %",
            "Text→Figure %",
            "Table→Text %",
            "Table→Missing %",
            "Table→Figure %",
            "Figure→Text %",
            "Figure→Missing %",
            "Figure→Table %",
        ],
        rows=build_confusion_rows(base_dir, models),
        align_right={1, 2, 3, 4, 5, 6, 7, 8, 9},
    )
    print(metric_table)
    print()
    print(confusion_table)


if __name__ == "__main__":
    main()
