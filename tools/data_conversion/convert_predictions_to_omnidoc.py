import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"


@dataclass
class NormalizedPrediction:
    label: str
    score: float
    bbox: List[float]


def load_gt(gt_path: Path) -> List[dict]:
    with gt_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_poly(x1: float, y1: float, x2: float, y2: float) -> List[float]:
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def clamp_box(bbox: Iterable[float], width: float, height: float) -> List[float]:
    x1, y1, x2, y2 = bbox
    x1 = max(0.0, min(float(width), float(x1)))
    y1 = max(0.0, min(float(height), float(y1)))
    x2 = max(0.0, min(float(width), float(x2)))
    y2 = max(0.0, min(float(height), float(y2)))
    return [x1, y1, x2, y2]


def build_gt_lookup(gt_data: List[dict]) -> Dict[str, dict]:
    lookup = {}
    for item in gt_data:
        image_path = Path(item["page_info"]["image_path"])
        lookup[image_path.name] = item
        lookup[image_path.stem] = item
    return lookup


def load_ppstructure_predictions(pred_path: Path) -> Dict[str, List[NormalizedPrediction]]:
    with pred_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result: Dict[str, List[NormalizedPrediction]] = {}
    for entry in data:
        preds = []
        for box in entry.get("boxes", []):
            coord = box.get("coordinate") or []
            if len(coord) != 4:
                continue
            preds.append(
                NormalizedPrediction(
                    label=box.get("label", "").strip(),
                    score=float(box.get("score", 1.0)),
                    bbox=[float(coord[0]), float(coord[1]), float(coord[2]), float(coord[3])],
                )
            )
        result[entry.get("image_name", "")] = preds
    return result


def load_dotsocr_predictions(pred_path: Path) -> Dict[str, List[NormalizedPrediction]]:
    with pred_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result: Dict[str, List[NormalizedPrediction]] = {}
    for entry in data.get("results", []):
        image_name = Path(entry.get("image_path", "")).name
        preds: List[NormalizedPrediction] = []
        raw_output = entry.get("output") or ""
        raw_output = raw_output.strip()
        if not raw_output or raw_output in {"[]", "null"} or raw_output.startswith("[BATCH ERROR]"):
            result[image_name] = preds
            continue
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            result[image_name] = preds
            continue
        for det in parsed:
            bbox = det.get("bbox") or []
            if len(bbox) != 4:
                continue
            preds.append(
                NormalizedPrediction(
                    label=det.get("category", "").strip(),
                    score=1.0,
                    bbox=[float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                )
            )
        result[image_name] = preds
    return result


def load_dolphin_predictions(pred_path: Path) -> Dict[str, List[NormalizedPrediction]]:
    with pred_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result: Dict[str, List[NormalizedPrediction]] = {}
    for entry in data:
        image_name = entry.get("image_name") or Path(entry.get("image_path", "")).name
        preds = []
        for det in entry.get("elements", []):
            bbox = det.get("bbox_abs") or []
            if len(bbox) != 4:
                continue
            preds.append(
                NormalizedPrediction(
                    label=det.get("label", "").strip(),
                    score=float(det.get("score", 1.0)),
                    bbox=[float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                )
            )
        result[image_name] = preds
    return result


def load_doclaynet_predictions(pred_path: Path) -> Dict[str, List[NormalizedPrediction]]:
    with pred_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result: Dict[str, List[NormalizedPrediction]] = {}
    for entry in data:
        image_name = entry.get("image_name") or Path(entry.get("image_path", "")).name
        preds = []
        for det in entry.get("detections", []):
            bbox = det.get("bbox_xyxy") or det.get("bbox_xywh") or []
            if len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            if det.get("bbox_xywh"):
                x, y, w, h = bbox
                x1, y1 = x, y
                x2, y2 = x + w, y + h
            preds.append(
                NormalizedPrediction(
                    label=det.get("label", "").strip(),
                    score=float(det.get("score", 1.0)),
                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                )
            )
        result[image_name] = preds
    return result


def map_label(raw_label: str, label_mapping: Dict[str, Optional[str]]) -> Optional[str]:
    if raw_label in label_mapping:
        return label_mapping[raw_label]
    return label_mapping.get("__default__")


def convert_predictions(
    gt_data: List[dict],
    pred_lookup: Dict[str, List[NormalizedPrediction]],
    label_mapping: Dict[str, Optional[str]],
) -> List[dict]:
    gt_lookup = build_gt_lookup(gt_data)
    converted = []
    for gt_item in gt_data:
        image_path = Path(gt_item["page_info"]["image_path"])
        preds = pred_lookup.get(image_path.name)
        if preds is None:
            preds = pred_lookup.get(image_path.stem, [])
        width = gt_item["page_info"]["width"]
        height = gt_item["page_info"]["height"]
        layout_items = []
        for idx, pred in enumerate(preds):
            target_label = map_label(pred.label, label_mapping)
            if not target_label:
                continue
            x1, y1, x2, y2 = clamp_box(pred.bbox, width, height)
            if x2 <= x1 or y2 <= y1:
                continue
            layout_items.append(
                {
                    "category_type": target_label,
                    "poly": format_poly(x1, y1, x2, y2),
                    "score": float(pred.score),
                    "ignore": False,
                    "order": None,
                    "anno_id": idx,
                    "line_with_spans": [],
                }
            )
        converted.append(
            {
                "layout_dets": layout_items,
                "extra": {},
                "page_info": gt_item["page_info"],
            }
        )
    unused_predictions = set(pred_lookup.keys()) - gt_lookup.keys()
    if unused_predictions:
        print(f"Warning: {len(unused_predictions)} prediction entries did not match GT pages.")
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert heterogeneous layout predictions to OmniDocBench format.")
    parser.add_argument("--pred-type", choices=[
        "pp_doclayout_s",
        "pp_doclayout_plus_l",
        "rt_detr_h",
        "dotsocr",
        "dolphin",
        "doclaynet_detr",
    ], required=True)
    parser.add_argument("--input", required=True, type=Path, help="Path to raw predictions.")
    parser.add_argument("--output", required=True, type=Path, help="Path to save converted predictions.")
    parser.add_argument(
        "--gt",
        default=DATA_ROOT / "OmniDocBench_data" / "OmniDocBench.json",
        type=Path,
        help="Ground truth JSON containing page metadata (default: data/OmniDocBench_data/OmniDocBench.json).",
    )
    args = parser.parse_args()

    gt_data = load_gt(args.gt)

    label_mappings: Dict[str, Dict[str, Optional[str]]] = {
        "pp_doclayout_s": {
            "doc_title": "title",
            "paragraph_title": "title",
            "title": "title",
            "abstract": "text",
            "aside_text": "text",
            "content": "text",
            "reference": "text",
            "text": "text",
            "figure_title": "figure_caption",
            "chart_title": "figure_caption",
            "table_title": "table_caption",
            "chart": "figure",
            "image": "figure",
            "header_image": "figure",
            "footer_image": "figure",
            "seal": "figure",
            "formula": "isolate_formula",
            "formula_number": "abandon",
            "number": "abandon",
            "header": "abandon",
            "footer": "abandon",
            "footnote": "abandon",
            "aside": "text",
            "table": "table",
            "__default__": None,
        },
        "pp_doclayout_plus_l": {
            "doc_title": "title",
            "paragraph_title": "title",
            "title": "title",
            "section_header": "title",
            "section": "title",
            "abstract": "text",
            "aside_text": "text",
            "content": "text",
            "reference": "text",
            "reference_content": "text",
            "text": "text",
            "algorithm": "text",
            "figure_title": "figure_caption",
            "chart": "figure",
            "image": "figure",
            "seal": "figure",
            "formula": "isolate_formula",
            "formula_number": "abandon",
            "number": "abandon",
            "header": "abandon",
            "footer": "abandon",
            "footnote": "abandon",
            "table": "table",
            "__default__": None,
        },
        "rt_detr_h": {
            "image": "figure",
            "table": "table",
            "seal": "figure",
            "__default__": None,
        },
        "dotsocr": {
            "Title": "title",
            "Section-header": "title",
            "Text": "text",
            "List-item": "text",
            "Caption": "figure_caption",
            "Picture": "figure",
            "Table": "table",
            "Formula": "isolate_formula",
            "Page-header": "abandon",
            "Page-footer": "abandon",
            "Footnote": "abandon",
            "__default__": None,
        },
        "dolphin": {
            "title": "title",
            "sec": "title",
            "sub_sec": "title",
            "sub_sub_sec": "title",
            "Text": "text",
            "text": "text",
            "para": "text",
            "list": "text",
            "author": "text",
            "code": "text",
            "anno": "abandon",
            "header": "abandon",
            "foot": "abandon",
            "fnote": "abandon",
            "watermark": "abandon",
            "Equation": "isolate_formula",
            "equ": "isolate_formula",
            "fig": "figure",
            "tab": "table",
            "cap": "figure_caption",
            "__default__": None,
        },
        "doclaynet_detr": {
            "Title": "title",
            "Section-header": "title",
            "Text": "text",
            "List-item": "text",
            "Caption": "figure_caption",
            "Picture": "figure",
            "Table": "table",
            "Formula": "isolate_formula",
            "Page-header": "abandon",
            "Page-footer": "abandon",
            "Footnote": "abandon",
            "__default__": None,
        },
    }

    loaders = {
        "pp_doclayout_s": load_ppstructure_predictions,
        "pp_doclayout_plus_l": load_ppstructure_predictions,
        "rt_detr_h": load_ppstructure_predictions,
        "dotsocr": load_dotsocr_predictions,
        "dolphin": load_dolphin_predictions,
        "doclaynet_detr": load_doclaynet_predictions,
    }

    pred_lookup = loaders[args.pred_type](args.input)
    converted = convert_predictions(gt_data, pred_lookup, label_mappings[args.pred_type])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False)
    print(f"Saved {len(converted)} converted pages to {args.output}")


if __name__ == "__main__":
    main()
