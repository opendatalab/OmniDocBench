from PIL import Image
from tqdm import tqdm
import json
import os
from collections import defaultdict
import langid
import re

def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox


table_format = 'html'   # table format in markdown. optional: latex

save_path = r'../demo_data/omnidocbench_demo/mds'
save_path_imgs = os.path.join(save_path, 'imgs')

os.makedirs(save_path, exist_ok=True)
os.makedirs(save_path_imgs, exist_ok=True)

with open(r'../demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)

def text_norm(text):
    after_text = replace_repeated_chars(text)
    return after_text.replace('/t', '\t').replace('/n', '\n')

# 标准化所有连续的字符
def replace_repeated_chars(input_str):
    input_str = re.sub(r'_{4,}', '____', input_str) # Replace more than 4 consecutive underscores with 4 underscores
    input_str = re.sub(r' {4,}', '    ', input_str)   # Replace more than 4 consecutive spaces with 4 spaces
    return re.sub(r'([^a-zA-Z0-9])\1{10,}', r'\1\1\1\1', input_str) # For other consecutive symbols (except numbers and letters), replace more than 10 occurrences with 4
def remove_unencodable_characters(s, encoding):
    return s.encode(encoding, errors='ignore').decode(encoding)
for sample in samples:
    annos = []
    for x in sample['layout_dets']:
        if x.get('order'):
            annos.append(x)

    # deal with truncated
    saved_element_dict = defaultdict(list)
    related_truncated = []
    truncated_all = {}
    for relation in sample["extra"]["relation"]:   # Handle truncated text blocks
        if relation["relation_type"] == 'truncated':
            truncated_all[relation["source_anno_id"]] = ""
            truncated_all[relation["target_anno_id"]] = ""
            exist_flag = False
            for merge_list in related_truncated:
                if relation["source_anno_id"] in merge_list or relation["target_anno_id"] in merge_list:  # Consider cases where three text blocks might need to be merged
                    merge_list.append(relation["source_anno_id"])
                    merge_list.append(relation["target_anno_id"])
                    exist_flag = True
            if not exist_flag:
                related_truncated.append([relation["source_anno_id"], relation["target_anno_id"]])       
    # print('related_truncated: ', related_truncated)
    merged_annos = []
    for item in annos:
        if item['anno_id'] not in truncated_all.keys():
            merged_annos.append(item)
        else:
            truncated_all[item['anno_id']] = item
    # print('truncated_all: ', truncated_all)
    for merge_list in related_truncated:
        text_block_list = [truncated_all[key] for key in merge_list]
        # if text_block_a['category_type'] != text_block_b['category_type']:
        #     print('')    # !!check
        sorted_block = sorted(text_block_list, key=lambda x: x['order'])
        text = ""
        for block in sorted_block:
            line_content = block['text']
            if langid.classify(line_content)[0] == 'en' and line_content[-1] != "-":

                text += f" {line_content}"
            elif langid.classify(line_content)[0] == 'en' and line_content[-1] == "-":
                text = text[:-1] + f"{line_content}"
            else:
                text += f"{line_content}"
        merged_block = {
            "category_type": sorted_block[0]["category_type"], # use the info of the first block
            "order": sorted_block[0]["order"],
            "anno_id": sorted_block[0]["anno_id"],   
            "text": text,
            "merge_list": sorted_block
        }
        merged_annos.append(merged_block)
        print('Merged truncated')

    annos = sorted(merged_annos, key=lambda x: x['order'])
    img_name = os.path.basename(sample['page_info']['image_path'])
    img_path = os.path.join(r'../demo_data/omnidocbench_demo/images', img_name)
    img = Image.open(img_path)

    md_path = os.path.join(save_path, os.path.basename(sample['page_info']['image_path'])[:-4] + '.md')

    with open(md_path, 'w', encoding='utf-8') as f:
        for i, anno in enumerate(annos):
            if anno["category_type"] == 'figure':
                bbox = poly2bbox(anno['poly'])
                im = img.crop(bbox).convert('RGB')
                anno_id = anno["anno_id"]
                crop_img_path = os.path.join(save_path_imgs, f"{img_name[:-4]}_{anno_id}.jpg")
                im.save(crop_img_path)
                f.write(f'![](./imgs/{img_name[:-4]}_{anno_id}.jpg)')
                f.write('\n\n')
            sep = '\n\n'
            item = anno
            if anno["category_type"] == 'table':
                f.write(item[table_format])
                f.write(sep)
            elif item.get('text'):
                print (item["category_type"])
                if item["category_type"] == 'title':
                    print ("title", item['text'])
                    f.write('# ' + text_norm(item['text'].strip('#').strip()))
                    f.write(sep)
                else:
                    print ("==err==", item["text"])
                    f.write(text_norm(item['text']))
                    f.write(sep)  
            elif item.get('html'):
                f.write(item['html'])
                f.write(sep)
            elif item.get('latex'):
                f.write(item['latex'])
                f.write(sep)
        f.close()