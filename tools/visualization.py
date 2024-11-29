from PIL import Image, ImageDraw, ImageFont
import random
import os
import json

img_folder = '../demo_data/omnidocbench_demo/images'
    
def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox


def get_color():
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)
    return (blue, green, red)

color_map = {
    'table': 'orange',
    'figure': 'green',
    'text_block': 'blue',
    'text_span': '#07689f',
    'equation_inline': '#590d82',
    'equation_ignore': '#769fcd'
}

with open('../demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r') as f:
    samples = json.load(f)

for i, sample in enumerate(samples):
    img_path = sample['page_info']["image_path"]

    if not img_path == 'jiaocaineedrop_chem-323236.pdf_183.jpg':  # chose one image
        continue

    img_path = sample['page_info']["image_path"]
    print(i)
    img=Image.open(os.path.join(img_folder, img_path))
    # print(img.size)
    draw = ImageDraw.Draw(img)

    for anno in sample['layout_dets']:
        if 'mask' in anno['category_type'] or anno['category_type'] == 'abandon' or (anno['category_type'] == 'table' and anno['attribute']['include_photo']):
            continue
        bbox = poly2bbox(anno['poly'])
        if not color_map.get(anno['category_type']):
            color = get_color()
            color_map[anno['category_type']] = color
        draw.rectangle(bbox, outline=color_map[anno['category_type']], width=3)
        # draw.text((bbox[0]-10, bbox[1]),str(anno.get('order')),(0,255,255))
        
        if not anno.get('line_with_spans'):
            continue
        for span in anno['line_with_spans']:
            bbox = poly2bbox(span['poly'])
            if not color_map.get(span['category_type']):
                color = get_color()
                color_map[span['category_type']] = color
            draw.rectangle(bbox, outline=color_map[span['category_type']], width=3)
    # display(img)
    img.save('./jiaocaineedrop.jpg')
    break