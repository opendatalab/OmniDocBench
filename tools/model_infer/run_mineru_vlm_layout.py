import argparse
import json
from pathlib import Path

from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from PIL import Image
from mineru_vl_utils import MinerUClient
import sys

# Restore stdout in case mineru_vl_utils modified it
sys.stdout = sys.__stdout__

CATEGORIES = {
    'title': 0,
    'plain text': 1,
    'abandon': 2,
    'figure': 3,
    'figure caption': 4,
    'table': 5,
    'table caption': 6,
    'table footnote': 7,
    'isolate formula': 8,
    'formula caption': 9,
}

TYPE_TO_CATEGORY = {
    'text': 'plain text',
    'title': 'title',
    'list': 'plain text',
    'header': 'plain text',
    'footer': 'plain text',
    'page_number': 'plain text',
    'page_footnote': 'plain text',
    'aside_text': 'plain text',
    'ref_text': 'plain text',
    'phonetic': 'plain text',
    'code': 'plain text',
    'code_caption': 'plain text',
    'algorithm': 'plain text',
    'image': 'figure',
    'image_caption': 'figure caption',
    'image_footnote': 'figure caption',
    'table': 'table',
    'table_caption': 'table caption',
    'table_footnote': 'table footnote',
    'equation': 'isolate formula',
    'equation_block': 'isolate formula',
    'unknown': 'abandon',
}


def get_block_value(block, *attr_names):
    for attr in attr_names:
        if hasattr(block, attr):
            value = getattr(block, attr)
            if value is not None:
                return value
        if isinstance(block, dict) and attr in block and block[attr] is not None:
            return block[attr]
    return None


def bbox_to_poly(bbox, width, height):
    if not bbox or len(bbox) != 4:
        return None
    x1, y1, x2, y2 = [float(coord) for coord in bbox]
    if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.0:
        x1 *= width
        x2 *= width
        y1 *= height
        y2 *= height
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def ensure_model(local_model_dir: Path):
    if not local_model_dir.exists():
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id='opendatalab/MinerU2.5-2509-1.2B',
            repo_type='model',
            local_dir=local_model_dir,
            local_dir_use_symlinks=False,
        )

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        local_model_dir,
        dtype='auto',
        device_map='auto',
    )
    processor = AutoProcessor.from_pretrained(local_model_dir, use_fast=True)
    client = MinerUClient(
        backend='transformers',
        model=model,
        processor=processor,
    )
    sys.stdout = sys.__stdout__
    return client


def run_inference(client, image_paths, log_handle=None):
    results = []
    total = len(image_paths)
    for idx, image_path in enumerate(image_paths, start=1):
        image = Image.open(image_path)
        blocks = client.layout_detect(image)
        layout_items = []
        width, height = image.size
        for block in blocks:
            raw_category = get_block_value(block, 'category', 'category_name', 'type')
            bbox = get_block_value(block, 'bbox')
            score = get_block_value(block, 'score', 'confidence')
            if raw_category is None or bbox is None:
                continue
            if isinstance(raw_category, int):
                category_name = next((name for name, cid in CATEGORIES.items() if cid == raw_category), None)
            else:
                raw_category = str(raw_category).lower()
                category_name = TYPE_TO_CATEGORY.get(raw_category, raw_category)
            if category_name not in CATEGORIES:
                continue
            poly = bbox_to_poly(bbox, width, height)
            if poly is None:
                continue
            layout_items.append({
                    'category_type': category_name,
                    'poly': poly,
                    'score': float(score) if score is not None else 1.0,
                    'ignore': False,
                    'order': None,
                    'anno_id': len(layout_items),
                    'line_with_spans': [],
                })
        results.append((image_path.name, layout_items, width, height))
        log_line = f"[{idx}/{total}] processed {image_path.name} -> {len(layout_items)} boxes\n"
        (log_handle or sys.stdout).write(log_line)
        if log_handle:
            log_handle.flush()
        else:
            sys.stdout.flush()
    return results


def save_results(results, output_path):
    formatted = []
    for idx, (image_name, layout_items, width, height) in enumerate(results):
        page_info = {
            'page_attribute': {},
            'page_no': idx,
            'height': height,
            'width': width,
            'image_path': image_name,
        }
        formatted.append({
            'layout_dets': layout_items,
            'extra': {},
            'page_info': page_info,
        })
    with open(output_path, 'w') as f:
        json.dump(formatted, f, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='Run MinerU2.5 layout detection on images and save predictions.')
    parser.add_argument('--images', required=True, help='Directory with images to process (OmniDocBench images).')
    parser.add_argument('--gt', required=True, help='Ground truth JSON to align page order.')
    parser.add_argument('--output', required=True, help='Output prediction JSON path.')
    parser.add_argument('--log', help='Optional log file to track progress (default: output with .log).')
    parser.add_argument('--model-dir', default='models/MinerU2.5-2509-1.2B', help='Local directory for MinerU model weights.')
    parser.add_argument('--limit', type=int, default=None, help='Optional number of images to process.')
    args = parser.parse_args()

    images_dir = Path(args.images)
    gt_data = json.loads(Path(args.gt).read_text())
    total = len(gt_data) if args.limit is None else min(args.limit, len(gt_data))

    image_paths = []
    for item in gt_data[:total]:
        image_path = images_dir / item['page_info']['image_path']
        if not image_path.exists():
            raise FileNotFoundError(f'Image not found: {image_path}')
        image_paths.append(image_path)

    client = ensure_model(Path(args.model_dir))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log) if args.log else output_path.with_suffix('.log')
    with open(log_path, 'w') as log_handle:
        print(f'Logging progress to {log_path}')
        results = run_inference(client, image_paths, log_handle)
    save_results(results, output_path)


if __name__ == '__main__':
    main()
