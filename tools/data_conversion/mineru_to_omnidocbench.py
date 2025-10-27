import argparse
import json
from pathlib import Path

def bbox_norm_to_xyxy(bbox_norm, width, height):
    x1, y1, x2, y2 = bbox_norm
    return [
        x1 * width,
        y1 * height,
        x2 * width,
        y2 * height,
    ]


def xyxy_to_poly(x1, y1, x2, y2):
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def load_ground_truth(gt_path):
    with open(gt_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Convert MinerU inference results to OmniDocBench format.')
    parser.add_argument('--mineru-json', required=True, help='Path to MinerU inference JSON.')
    parser.add_argument('--gt', required=True, help='Path to OmniDocBench ground truth JSON for metadata.')
    parser.add_argument('--images-dir', required=True, help='Directory containing OmniDocBench images.')
    parser.add_argument('--output', required=True, help='Output JSON path in OmniDocBench format.')
    args = parser.parse_args()

    mineru_data = json.loads(Path(args.mineru_json).read_text())
    gt_data = load_ground_truth(args.gt)
    images_dir = Path(args.images_dir)

    formatted = []
    missing = []

    for idx, item in enumerate(gt_data):
        image_name = item['page_info']['image_path']
        width = item['page_info']['width']
        height = item['page_info']['height']
        key = Path(image_name).name
        if key not in mineru_data:
            missing.append(key)
            layout_items = []
        else:
            layout_items = []
            for det in mineru_data[key]:
                if isinstance(det, str):
                    if det != 'processing_error':
                        print(f'Warning: unexpected string entry for {key}: {det}')
                    continue
                category = det.get('type')
                if category is None:
                    continue
                bbox_norm = det.get('bbox')
                if not bbox_norm or len(bbox_norm) != 4:
                    continue
                x1, y1, x2, y2 = bbox_norm_to_xyxy(bbox_norm, width, height)
                poly = xyxy_to_poly(x1, y1, x2, y2)
                score = det.get('score', 1.0)
                content = det.get('content')
                layout_items.append({
                    'category_type': category,
                    'block_type': category,
                    'poly': poly,
                    'bbox': [x1, y1, x2, y2],
                    'score': float(score),
                    'ignore': False,
                    'order': len(layout_items) + 1,
                    'anno_id': len(layout_items) + 1,
                    'line_with_spans': [],
                    'content': content or '',
                })
        formatted.append({
            'layout_dets': layout_items,
            'extra': {},
            'page_info': item['page_info'],
        })

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w') as f:
        json.dump(formatted, f, ensure_ascii=False)

    if missing:
        print(f'Missing {len(missing)} pages in MinerU results, example: {missing[:5]}')
    else:
        print('All pages found in MinerU results.')


if __name__ == '__main__':
    main()
