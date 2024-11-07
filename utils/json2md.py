from PIL import Image
from tqdm import tqdm
import json
import os
from collections import defaultdict
import langid
def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox


table_format = 'latex'

save_path = r'D:\pdf-bench\正式标注任务\1112md'
save_path_imgs = os.path.join(save_path, 'imgs')

os.makedirs(save_path, exist_ok=True)
os.makedirs(save_path_imgs, exist_ok=True)

# with open('/mnt/petrelfs/ouyanglinke/CDM_match/demo_data_v2/demo_val_dataset.json', 'r') as f:
with open(r'D:\pdf-bench\正式标注任务\ocr-main-1105-update\export\ocr-main-1105-update.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)

def text_norm(text):
    return text.replace('/t', '\t').replace('/n', '\n')

def remove_unencodable_characters(s, encoding):
    return s.encode(encoding, errors='ignore').decode(encoding)
for sample in samples:
    annos = []
    for x in sample['layout_dets']:
        if x.get('order'):
            annos.append(x)
        # elif x["category_type"] == 'merge':   # merge现在有order和text了
            # if not x.get('merge_list'):
            #     print('Empty merge list: ', sample['page_info'])
            # elif not x['merge_list'][0].get('order'):
            #     print('Merge_list no order: ', sample['page_info'])
            # else:
            #     x['order'] = x['merge_list'][0]['order']
            #     annos.append(x)

    # 处理truncated
    saved_element_dict = defaultdict(list)
    related_truncated = []
    truncated_all = {}
    for relation in sample["extra"]["relation"]:   # 解决被截断的文本的问题
        if relation["relation_type"] == 'truncated':
            truncated_all[relation["source_anno_id"]] = ""
            truncated_all[relation["target_anno_id"]] = ""
            exist_flag = False
            for merge_list in related_truncated:
                if relation["source_anno_id"] in merge_list or relation["target_anno_id"] in merge_list:  # 考虑到有可能有三个text block合并的情况
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
            "category_type": sorted_block[0]["category_type"], # 这里直接占据了第一个block的各种信息
            "order": sorted_block[0]["order"],
            "anno_id": sorted_block[0]["anno_id"],   
            "text": text,
            "merge_list": sorted_block
        }
        merged_annos.append(merged_block)
        print('Merged truncated')

    annos = sorted(merged_annos, key=lambda x: x['order'])
    img_name = os.path.basename(sample['page_info']['image_path'])
    # img_path = os.path.join('/mnt/petrelfs/ouyanglinke/CDM_match/demo_data_v2/new_demo_images', img_name)
    img_path = os.path.join(r'D:\pdf-bench\正式标注任务\image', img_name)
    img = Image.open(img_path)

    # md_path = os.path.join('/mnt/petrelfs/ouyanglinke/CDM_match/demo_data_v2/md_old', os.path.basename(sample['page_info']['image_path'])[:-4] + '.md')
    md_path = os.path.join(save_path, os.path.basename(sample['page_info']['image_path'])[:-4] + '.md')


    with open(md_path, 'w', encoding='utf-8') as f:
        for i, anno in enumerate(annos):
            if anno["category_type"] == 'figure':
                bbox = poly2bbox(anno['poly'])
                im = img.crop(bbox).convert('RGB')
                anno_id = anno["anno_id"]
                # crop_img_path = os.path.join('/mnt/petrelfs/ouyanglinke/CDM_match/demo_data_v2/md_old/imgs', f"{img_name[:-4]}_{anno_id}.jpg")
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
                if item["category_type"] == 'title':
                    f.write('# ' + text_norm(item['text'].strip('#').strip()))
                    f.write(sep)
                if item["category_type"] == "equation_caption":
                    pass
                else:
                    #print ("==err==", item["text"])
                    f.write(text_norm(item['text']))
                    f.write(sep)  
            elif item.get('html'):
                f.write(item['html'])
                f.write(sep)
            elif item.get('latex'):
                f.write(item['latex'])
                f.write(sep)
        f.close()