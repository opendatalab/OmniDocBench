import json
import os
from collections import defaultdict
from utils.extract import md_tex_filter
from utils.match import match_gt2pred_simple, match_gt2pred_no_split
from utils.match_quick import match_gt2pred_quick
# from utils.match_full import match_gt2pred_full, match_gt2pred_textblock_full
from utils.read_files import read_md_file
from registry.registry import DATASET_REGISTRY
from dataset.recog_dataset import *
import pdb
import Levenshtein
from tqdm import tqdm
# from utils.data_preprocess import timed_function, timed_function_single
from func_timeout import FunctionTimedOut, func_timeout
from loguru import logger
import time

@DATASET_REGISTRY.register("end2end_dataset")
class End2EndDataset():
    def __init__(self, cfg_task):
        gt_path = cfg_task['dataset']['ground_truth']['data_path']
        pred_folder = cfg_task['dataset']['prediction']['data_path']
        self.match_method = cfg_task['dataset'].get('match_method', 'quick_match')
        filtered_types = cfg_task['dataset'].get('filter')

        with open(gt_path, 'r') as f:
            gt_samples = json.load(f)

        # specific_files=['yanbaopptmerge_yanbaoPPT_1090.jpg']  # 单个文件debug
        # gt_samples = [sample for sample in gt_samples if os.path.basename(sample["page_info"]["image_path"]) in specific_files]

        filtered_gt_samples = []
        if filtered_types:
            for gt_sample in gt_samples:
                select_flag = True
                for k, v in filtered_types.items():
                    if gt_sample["page_info"]["page_attribute"][k] != v:
                        select_flag = False
                if select_flag:
                    filtered_gt_samples.append(gt_sample)
        else:
            filtered_gt_samples = gt_samples

        self.samples = self.get_matched_elements(filtered_gt_samples, pred_folder)
        
    def __getitem__(self, cat_name, idx):
        return self.samples[cat_name][idx]
    
    # def get_with_image_name(self, image_name):
    #     return self.samples_dict[image_name]
    
    def get_page_elements(self, selected_annos):
        saved_element_dict = defaultdict(list)
        related_truncated = []
        truncated_all = {}
        for relation in selected_annos["extra"]["relation"]:   # 解决被截断的文本的问题
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
        
        for item in selected_annos['layout_dets']:
            if item['anno_id'] not in truncated_all.keys():
                saved_element_dict[item["category_type"]].append(item)
            else:
                truncated_all[item['anno_id']] = item
        
        for merge_list in related_truncated:
            text_block_list = [truncated_all[key] for key in merge_list]
            # if text_block_a['category_type'] != text_block_b['category_type']:
            #     print('')    # !!check
            sorted_block = sorted(text_block_list, key=lambda x: x['order'])
            text = ""
            for block in sorted_block:
                text += block['text']
            merged_block = {
                "category_type": sorted_block[0]["category_type"], # 这里直接占据了第一个block的各种信息
                "order": sorted_block[0]["order"],
                "anno_id": sorted_block[0]["anno_id"],   
                "text": text,
                "merge_list": sorted_block
            }
            saved_element_dict[sorted_block[0]["category_type"]].append(merged_block)
            # print('Merged truncated')

        return saved_element_dict
    
    def get_page_elements_list(self, gt_page_elements, category_list):
        element_list = []
        for category_type in category_list:
            if gt_page_elements.get(category_type):
                element_list.extend(gt_page_elements[category_type])
        return element_list

    def get_sorted_text_list(self, selected_annos):
        # txt_type: text, latex, html
        text_list = []
        for item in selected_annos:
            if item.get('order'):
                order = item['order']
            else:
                order = 0
            # if item.get(txt_type):
            #     txt = item[txt_type]
            # else:
            #     txt = ""
                # print(f'Cannot find GT text for {item}')
            text_list.append((order, item))
        sorted_text_list = sorted(text_list, key=lambda x: x[0])
        return [_[1] for _ in sorted_text_list]
    
    def filtered_out_ignore(self, items, ignore_category_list):
        filted_items = []
        for item in items:
            if item['gt_category_type'] not in ignore_category_list:
                filted_items.append(item)
        return filted_items

    def get_order_paired(self, order_match_s, img_name):
        matched = [(item['gt_position'], item['pred_position']) for item in order_match_s if (item['gt_position'][0] != -1 and item['pred_position'] != -1)]
        # read_order_gt = [i[0] for i in sorted(matched, key=lambda x: x[0])]   # 以GT的idx来sort，获取GT排序的GT_idx
        # print(matched)
        read_order_pred = [i[0] for i in sorted(matched, key=lambda x: x[1])]  # 以pred的idx来sort，获取Pred排序的GT_idx
        read_order_gt = sorted(read_order_pred) # 以GT的idx来sort，获取GT排序的GT_idx
        gt = sum(read_order_gt, []) # 转成一个一维list
        pred = sum(read_order_pred, [])
        if len(pred) > 0 or len(gt) > 0:
            edit = Levenshtein.distance(gt, pred)/ max(len(pred), len(gt))
        else:
            edit = 0
        return {
            'gt': gt,  
            'pred': pred,
            'img_id': img_name,
            'edit': edit
        }

    def formula_format(self, formula_matches, img_name):
        # formated_list = []
        for i, item in enumerate(formula_matches):
            item["img_id"] = img_name + '_' + str(i)
            # formated_list.append({
            #     "gt": item["gt"],
            #     "pred": item["pred"],
            #     "img_id": img_name + '_' + str(i)
            # })
        return formula_matches

    def get_matched_elements(self, gt_samples, pred_folder):
        plain_text_match = []
        display_formula_match = []
        html_table_match = []
        latex_table_match = []
        order_match = []
        save_time = time.time()

        process_bar = tqdm(gt_samples, ascii=True, ncols=140)
        for sample in process_bar:
            img_name = os.path.basename(sample["page_info"]["image_path"])
            # print('Process: ', img_name)
            pred_path = os.path.join(pred_folder, img_name[:-4] + '.md')
            if not os.path.exists(pred_path):
                pred_path = os.path.join(pred_folder, img_name[:-4].replace('.pdf', "") + '.mmd')  # nougat
                if not os.path.exists(pred_path):
                    pred_path = os.path.join(pred_folder, img_name[:-4].replace('.pdf', "") + '.md')  # marker
                    if not os.path.exists(pred_path):
                        pred_path = os.path.join(pred_folder, img_name + '.md')
                        if not os.path.exists(pred_path):  # mineru
                            print(f'!!!WARNING: No prediction for {img_name}')
                            continue

            process_bar.set_description(f'Processing {os.path.basename(pred_path)}')
            pred_content = read_md_file(pred_path)

            # result = self.process_get_matched_elements(sample, pred_content, img_name, save_time)
            # result = timed_function_single(self.process_get_matched_elements, sample, pred_content, img_name, timeout=25)
            try:
                result = func_timeout(
                    300, self.process_get_matched_elements, args=(sample, pred_content, img_name, save_time)
                )
            except FunctionTimedOut as e1:
                logger.exception(e1)
                print(f'Time out for {os.path.basename(pred_path)}, it will be skipped.')
                with open(f'page_timeout_{save_time}.log', 'a') as f:
                    f.write(str(e1))
                    f.write('\n')
                continue
            except Exception as e:
                print(str(e))
                continue
            # if result:
            [plain_text_match_clean, formated_display_formula, latex_table_match_s, html_table_match_s, order_match_single] = result
            # else:
            #     print(f'Process time out for {img_name}. It will be skipped.')
            #     continue

            if order_match_single:
                order_match.append(order_match_single)
            if plain_text_match_clean:
                plain_text_match.extend(plain_text_match_clean)
            if formated_display_formula:
                display_formula_match.extend(formated_display_formula)
            if latex_table_match_s:
                latex_table_match.extend(latex_table_match_s)
            if html_table_match_s:
                html_table_match.extend(html_table_match_s)

        if len(latex_table_match) > len(html_table_match): # 这里默认模型不会同时随机输出latex或html，而是二选一
            table_match = latex_table_match
            table_format = 'latex'
        else:
            table_match = html_table_match
            table_format = 'html'

        # 提取匹配数据检查
        # if not os.path.exists('./result'):
        #     os.makedirs('./result')
        # with open('./result/plain_text_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(plain_text_match, f, indent=4, ensure_ascii=False)
        # with open('./result/table_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(table_match, f, indent=4, ensure_ascii=False)
        # with open('./result/order_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(order_match, f, indent=4, ensure_ascii=False)
        # with open('./result/display_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(display_formula_match, f, indent=4, ensure_ascii=False)

        matched_samples_all = {
            'text_block': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(plain_text_match),
            # 'inline_formula': DATASET_REGISTRY.get('recogition_end2end_formula_dataset')(inline_formula_match), 
            'display_formula':  DATASET_REGISTRY.get('recogition_end2end_base_dataset')(display_formula_match), 
            'table': DATASET_REGISTRY.get('recogition_end2end_table_dataset')(table_match, table_format),
            'reading_order': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(order_match)
        }
        
        return matched_samples_all


    def process_get_matched_elements(self, sample, pred_content, img_name, save_time):
        if self.match_method == 'simple_match':   # add match choice
            match_gt2pred = match_gt2pred_simple
            # match_gt2pred_textblock = match_gt2pred_textblock_simple
        elif self.match_method == 'quick_match':
            match_gt2pred = match_gt2pred_quick
            # match_gt2pred_textblock = match_gt2pred_textblock_quick
        elif self.match_method == 'no_split':
            match_gt2pred = match_gt2pred_no_split
        else:
            print('Invalid match method name. The quick_match will be used.')
            match_gt2pred = match_gt2pred_quick

        pred_dataset = md_tex_filter(pred_content)
        # print('pred_text_list: ', pred_text_list)
        # print('pred_display_list: ', pred_display_list)
        # print('pred_latex_table_list', pred_latex_table_list)
        # print('pred_html_table_list', pred_html_table_list)
        # print('pred_title_list: ', pred_title_list)

        gt_page_elements = self.get_page_elements(sample)
        # print('-----------gt_page_elements: ', gt_page_elements['text_block'])
        
        # 文本相关的所有element，不涉及的类别有figure, table, table_mask, equation_isolated, equation_caption, equation_ignore, equation_inline, footnote_mark, page_number, abandon, list, text_mask, need_mask
        text_all = self.get_page_elements_list(gt_page_elements, ['text_block', 'title', 'code_txt', 'code_txt_caption', 'list_merge', 'reference',
                                                'figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption'
                                                'header', 'footer', 'page_footnote'])

        # print('-------------!!text_all: ', text_all)
        display_formula_match_s = []
        plain_text_match_clean = []
        latex_table_match_s = []
        html_table_match_s = []
        order_match_single = []
        if text_all:
            gt_text_list = self.get_sorted_text_list(text_all)
            # print('gt_text_list: ', gt_text_list)
            # plain_text_match_s, inline_formula_match_s = match_gt2pred_textblock(gt_text_list, pred_dataset['text_all'], img_name)
            # plain_text_match_s = match_gt2pred(gt_text_list, pred_dataset['text_all'], 'text', img_name)
            # plain_text_match_s = timed_function(match_gt2pred, match_gt2pred_no_split, gt_text_list, pred_dataset['text_all'], 'text', img_name, timeout=15, print_msg=img_name)
            try:
                plain_text_match_s = func_timeout(
                    300, match_gt2pred, args=(gt_text_list, pred_dataset['text_all'], 'text', img_name)
                )
            except FunctionTimedOut as e1:
                logger.exception(e1)
                with open(f'timeout_{save_time}.log', 'a') as f:
                    f.write(str(e1))
                    f.write('\n')
                plain_text_match_s = match_gt2pred_simple(gt_text_list, pred_dataset['text_all'], 'text', img_name)
            except Exception as e:
                # print(str(e))
                print(f'Time out for plain text match of {img_name}, match_gt2pred_simple will be used.')

            if not plain_text_match_s:
                # print(f'Time out for text match of {img_name}. The plain text match will be empty.')
                print(f'No text match of {img_name}. The plain text match will be empty.')
            else:
                # print('plain_text_match_s: ', plain_text_match_s)
                # print('-'*10)
                # print('inline_formula_match_s', inline_formula_match_s)
                # print('-'*10)
                # 文本类需要ignore的类别
                plain_text_match_clean = self.filtered_out_ignore(plain_text_match_s, ['figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption', 'header', 'footer', 'page_footnote'])
                
            # formated_inline_formula = self.formula_format(inline_formula_match_s, img_name)
            # inline_formula_match.extend(formated_inline_formula)
            # print('inline_formula_match_s: ', inline_formula_match_s)
            # print('-'*10)
            
        # if gt_page_elements.get('title'):
        #     gt_title_list = self.get_sorted_text_list(gt_page_elements['title'])
        #     # print('gt_title_list: ', gt_title_list)
        #     title_match_s = match_gt2pred(gt_title_list, pred_title_list, 'text', img_name)
        #     title_match.extend(title_match_s)
            # print('title_match_s: ', title_match_s)
            # print('-'*10)
        if gt_page_elements.get('equation_isolated'):
            gt_display_list = self.get_sorted_text_list(gt_page_elements['equation_isolated'])
            # print('gt_display_list: ', gt_display_list)
            display_formula_match_s = match_gt2pred(gt_display_list, pred_dataset['equation_isolated'], 'formula', img_name)
            # display_formula_match_s = timed_function(match_gt2pred, match_gt2pred_no_split, gt_display_list, pred_dataset['equation_isolated'], 'formula', img_name, timeout=15, print_msg=img_name)
            if not display_formula_match_s:
                # print(f'Time out for display_formula_match of {img_name}. The display_formula_match will be empty.')
                print(f'No display_formula_match of {img_name}. The display_formula_match will be empty.')
            # else:
                # formated_display_formula = self.formula_format(display_formula_match_s, img_name)
                # print('display_formula_match_s: ', display_formula_match_s)
                # print('-'*10)
      
        if gt_page_elements.get('table'):
            gt_table_list = self.get_sorted_text_list(gt_page_elements['table'])
            # print('gt_table_list', gt_table_list)
            if pred_dataset['latex_table']:
                latex_table_match_s = match_gt2pred_simple(gt_table_list, pred_dataset['latex_table'], 'latex_table', img_name) # Table不考虑截断合并
                # latex_table_match_s = timed_function(match_gt2pred, match_gt2pred_no_split, gt_table_list, pred_dataset['latex_table'], 'latex_table', img_name, timeout=15, print_msg=img_name)
                # if not latex_table_match_s:
                #     print(f'Time out for table_match_s of {img_name}. The table_match_s will be empty.') 
            if pred_dataset['html_table']:   # 这里默认模型不会同时随机输出latex或html，而是二选一
                html_table_match_s = match_gt2pred_simple(gt_table_list, pred_dataset['html_table'], 'html_table', img_name) # Table不考虑截断合并
                # html_table_match_s = timed_function(match_gt2pred, match_gt2pred_no_split, gt_table_list, pred_dataset['html_table'], 'html_table', img_name, timeout=15, print_msg=img_name)
                # if not html_table_match_s:
                #     print(f'Time out for table_match_s of {img_name}. The table_match_s will be empty.')
            # else:
            #     print(f'Empty table pred for {img_name}')
            # print('table_match_s: ', table_match_s)
            # print('-'*10)

        # 阅读顺序的处理
        order_match_s = []
        for mateches in [plain_text_match_clean, display_formula_match_s]:
            if mateches:
                order_match_s.extend(mateches)
        if order_match_s:
            order_match_single = self.get_order_paired(order_match_s, img_name)
            
        return [plain_text_match_clean, display_formula_match_s, latex_table_match_s, html_table_match_s, order_match_single]       
    

@DATASET_REGISTRY.register("recogition_end2end_base_dataset")
class RecognitionEnd2EndBaseDataset():
    def __init__(self, samples):
        img_id = 0
        for sample in samples:
            if not sample.get('img_id'):
                sample['img_id'] = img_id
            img_id += 1
        self.samples = samples
    def __getitem__(self, idx):
        return self.samples[idx]
    
# @DATASET_REGISTRY.register("recogition_end2end_formula_dataset")
# class RecognitionEnd2EndFormulaDataset(RecognitionFormulaDataset):
#     def __init__(self, samples):
#         self.samples = []
#         img_id = 0
#         for sample in samples:
#             gt = self.normalize_text(sample['gt'])
#             pred = self.normalize_text(sample['pred'])
#             self.samples.append({
#                 'gt': gt,
#                 'pred': pred,
#                 'img_id': sample['img_id'] if sample.get('img_id') else img_id
#             })
#             img_id += 1

@DATASET_REGISTRY.register("recogition_end2end_table_dataset")
class RecognitionEnd2EndTableDataset(RecognitionTableDataset):
    def __init__(self, samples, table_format):
        self.pred_table_format = table_format
        self.samples = self.normalize_data(samples)

    def normalize_data(self, samples):
        img_id = 0
        
        if self.pred_table_format == 'latex':
            os.makedirs('./temp', exist_ok=True)

        for sample in samples:
            p = sample['pred']
            r = sample['gt']
            if self.pred_table_format == 'latex':
                if p:
                    p = self.convert_latex_to_html(p, cache_dir='./temp')
                # if r:
                #     r = self.convert_latex_to_html(r)
            _, p = self.process_table_html(p)
            _, r = self.process_table_html(r)
            # print('p:\n', p)
            # print('r:\n', r)
            sample['gt'] = self.strcut_clean(self.clean_table(r))
            sample['pred'] = self.strcut_clean(p)
            sample['img_id'] = sample['img_id'] if sample.get('img_id') else img_id
            img_id += 1

        if self.pred_table_format == 'latex':
            shutil.rmtree('./temp')

        return samples
    
# @DATASET_REGISTRY.register("recogition_end2end_table_dataset")
# class RecognitionEnd2EndTableDataset(RecognitionTableDataset):
#     def __init__(self, samples, table_format, table_latex2html):
#         self.pred_table_format = table_format
#         self.samples = self.normalize_data(samples, table_latex2html)

#     def normalize_data(self, samples, table_latex2html):
#         norm_samples = []
#         img_id = 0
        
#         if not table_latex2html:
#             for sample in samples:
#                 norm_samples.append({
#                     'gt': sample['norm_gt'],
#                     'pred': sample['norm_pred'],
#                     'img_id': sample['img_id'] if sample.get('img_id') else img_id
#                 })
#                 img_id += 1
#         else:
#             if self.pred_table_format == 'latex':
#                 os.makedirs('./temp', exist_ok=True)

#             for sample in samples:
#                 p = sample['pred']
#                 r = sample['gt']
#                 if self.pred_table_format == 'latex':
#                     if p:
#                         p = self.convert_latex_to_html(p, cache_dir='./temp')
#                     # if r:
#                     #     r = self.convert_latex_to_html(r)
#                 _, p = self.process_table(p)
#                 _, r = self.process_table(r)
#                 # print('p:\n', p)
#                 # print('r:\n', r)
#                 norm_samples.append({
#                     'gt': self.strcut_clean(self.clean_table(r)),
#                     'pred': self.strcut_clean(p),
#                     'img_id': sample['img_id'] if sample.get('img_id') else img_id
#                 })
#                 img_id += 1

#             if self.pred_table_format == 'latex':
#                 shutil.rmtree('./temp')

#         return norm_samples
