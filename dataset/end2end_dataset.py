import json
import os
from collections import defaultdict
from utils.extract import md_tex_filter
from utils.match import match_gt2pred_simple, match_gt2pred_no_split
from utils.match_quick import match_gt2pred_quick
# from utils.match_full import match_gt2pred_full, match_gt2pred_textblock_full
from utils.read_files import read_md_file
from utils.data_preprocess import normalized_table
from registry.registry import DATASET_REGISTRY
from dataset.recog_dataset import *
import pdb
import Levenshtein
from tqdm import tqdm
from func_timeout import FunctionTimedOut, func_timeout
from loguru import logger
import time
import sys

@DATASET_REGISTRY.register("end2end_dataset")
class End2EndDataset():
    def __init__(self, cfg_task):
        gt_path = cfg_task['dataset']['ground_truth']['data_path']
        pred_folder = cfg_task['dataset']['prediction']['data_path']
        self.match_method = cfg_task['dataset'].get('match_method', 'quick_match')
        filtered_types = cfg_task['dataset'].get('filter')

        with open(gt_path, 'r') as f:
            gt_samples = json.load(f)

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
    
    def get_page_elements(self, selected_annos):
        saved_element_dict = defaultdict(list)
        related_truncated = []
        truncated_all = {}
        for relation in selected_annos["extra"]["relation"]:   # Handle truncated text issues
            if relation["relation_type"] == 'truncated':
                truncated_all[relation["source_anno_id"]] = ""
                truncated_all[relation["target_anno_id"]] = ""
                exist_flag = False
                for merge_list in related_truncated:
                    if relation["source_anno_id"] in merge_list or relation["target_anno_id"] in merge_list:  # Consider cases where three text blocks may need to be merged
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
            sorted_block = sorted(text_block_list, key=lambda x: x['order'])
            text = ""
            for block in sorted_block:
                text += block['text']
            merged_block = {
                "category_type": sorted_block[0]["category_type"], # Directly use information from the first block
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
        matched = [(item['gt_position'], item['pred_position']) for item in order_match_s if (item['gt_position'] != [""] and item['pred_position'] != "")]
        gt_idx_all = [item['gt_position'] for item in order_match_s if (item['gt_position'] != [""])]
        read_order_pred = [i[0] for i in sorted(matched, key=lambda x: x[1])]  # Sort by pred idx to get Pred ordered GT_idx
        read_order_gt = sum(gt_idx_all, []) # Convert to one-dimensional list
        read_order_gt = [x for x in read_order_gt if x]  # For truncated merges, some discarded classes may be merged in, remove them when calculating edit distance
        gt = sorted(read_order_gt) # Sort by all GT idx to get GT ordered GT_idx
        pred = sum(read_order_pred, [])
        pred = [x for x in pred if x]
        if len(pred) > 0 or len(gt) > 0:
            edit = Levenshtein.distance(gt, pred)/ max(len(pred), len(gt))
            return {
                'gt': gt,  
                'pred': pred,
                'img_id': img_name,
                'edit': edit
            }
        else:
            return {}  # If both GT and pred are empty for the page, return empty

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

            result = self.process_get_matched_elements(sample, pred_content, img_name, save_time) # Don't use timeout logic
            # try:   # Skip if timeout
            #     result = func_timeout(
            #         300, self.process_get_matched_elements, args=(sample, pred_content, img_name, save_time)
            #     )
            # except FunctionTimedOut as e1:
            #     logger.exception(e1)
            #     print(f'Time out for {os.path.basename(pred_path)}, it will be skipped.')
            #     with open(f'page_timeout_{save_time}.log', 'a') as f:
            #         f.write(str(e1))
            #         f.write('\n')
            #     continue
            # except Exception as e:
            #     print(str(e))
            #     continue

            [plain_text_match_clean, formated_display_formula, latex_table_match_s, html_table_match_s, order_match_single] = result


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

        if len(latex_table_match) > len(html_table_match): # Assume model won't randomly output both latex and html, but will choose one
            table_match = latex_table_match
            table_format = 'latex'
        else:
            table_match = html_table_match
            table_format = 'html'

        matched_samples_all = {
            'text_block': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(plain_text_match),
            'display_formula':  DATASET_REGISTRY.get('recogition_end2end_base_dataset')(display_formula_match), 
            'table': DATASET_REGISTRY.get('recogition_end2end_table_dataset')(table_match, table_format),
            'reading_order': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(order_match)
        }
        
        return matched_samples_all


    def process_get_matched_elements(self, sample, pred_content, img_name, save_time):
        if self.match_method == 'simple_match':   # add match choice
            match_gt2pred = match_gt2pred_simple
        elif self.match_method == 'quick_match':
            match_gt2pred = match_gt2pred_quick
        elif self.match_method == 'no_split':
            match_gt2pred = match_gt2pred_no_split
        else:
            print('Invalid match method name. The quick_match will be used.')
            match_gt2pred = match_gt2pred_quick

        pred_dataset = md_tex_filter(pred_content)

        gt_page_elements = self.get_page_elements(sample)
        
        # All text-related elements, excluding categories: figure, table, table_mask, equation_isolated, equation_caption, equation_ignore, equation_inline, footnote_mark, page_number, abandon, list, text_mask, need_mask
        text_all = self.get_page_elements_list(gt_page_elements, ['text_block', 'title', 'code_txt', 'code_txt_caption', 'reference', 'equation_caption',
                                                'figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption',
                                                'header', 'footer', 'page_footnote', 'page_number'])

        # print('-------------!!text_all: ', text_all)
        display_formula_match_s = []
        plain_text_match_clean = []
        latex_table_match_s = []
        html_table_match_s = []
        order_match_single = []
        if text_all:
            gt_text_list = self.get_sorted_text_list(text_all)
            # plain_text_match_s = match_gt2pred(gt_text_list, pred_dataset['text_all'], 'text', img_name)  # Don't use timeout logic
            try:
                plain_text_match_s = func_timeout(
                    30, match_gt2pred, args=(gt_text_list, pred_dataset['text_all'], 'text', img_name)
                )
            except FunctionTimedOut as e1:
                # logger.exception(e1)
                # with open(f'timeout_{save_time}.log', 'a') as f:
                #     f.write(str(e1))
                #     f.write('\n')
                print(f'Time out for plain text match of {img_name}, match_gt2pred_simple will be used.')
                plain_text_match_s = match_gt2pred_simple(gt_text_list, pred_dataset['text_all'], 'text', img_name)
            except Exception as e:
                print(str(e))
                sys.exit()     

            if not plain_text_match_s:
                # print(f'Time out for text match of {img_name}. The plain text match will be empty.')
                print(f'No text match of {img_name}. The plain text match will be empty.')
            else:
                # Categories that need to be ignored for text
                plain_text_match_clean = self.filtered_out_ignore(plain_text_match_s, ['figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption', 'header', 'footer', 'page_footnote', 'page_number', 'equation_caption'])
            
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
            display_formula_match_s = [x for x in display_formula_match_s if x['gt_idx'] != [""]]  # Remove extra preds since inline formulas were also included for matching
            if not display_formula_match_s:
                print(f'No display_formula_match of {img_name}. The display_formula_match will be empty.')
      
        if gt_page_elements.get('table'):
            gt_table_list = self.get_sorted_text_list(gt_page_elements['table'])
            # print('gt_table_list', gt_table_list)
            if pred_dataset['latex_table']:
                latex_table_match_s = match_gt2pred_simple(gt_table_list, pred_dataset['latex_table'], 'latex_table', img_name) # Don't consider truncated merging for tables
                latex_table_match_s = [x for x in latex_table_match_s if x['gt_idx'] != [""]]  # Remove extra preds
            if pred_dataset['html_table']:   # Assume model won't randomly output both latex and html, but will choose one
                html_table_match_s = match_gt2pred_simple(gt_table_list, pred_dataset['html_table'], 'html_table', img_name) # Don't consider truncated merging for tables
                html_table_match_s = [x for x in html_table_match_s if x['gt_idx'] != [""]]  # Remove extra preds
            else:
                html_table_match_s = match_gt2pred_simple(gt_table_list, [], 'html_table', img_name) # Don't consider truncated merging for tables
                html_table_match_s = [x for x in html_table_match_s if x['gt_idx'] != [""]]  # Remove extra preds

        # Handle reading order
        # order_match_s = []
        # for mateches in [plain_text_match_clean, display_formula_match_s]:
        #     if mateches:
        #         order_match_s.extend(mateches)
        order_match_s = plain_text_match_clean
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

@DATASET_REGISTRY.register("recogition_end2end_table_dataset")
class RecognitionEnd2EndTableDataset(RecognitionTableDataset):
    def __init__(self, samples, table_format):
        self.pred_table_format = table_format
        self.samples = self.normalize_data(samples)

    def normalize_data(self, samples):
        img_id = 0

        for sample in samples:
            p = sample['pred']
            r = sample['gt']
            p = normalized_table(p, self.pred_table_format)
            r = normalized_table(r)
            # print('p:\n', p)
            # print('r:\n', r)
            sample['norm_gt'] = r
            sample['norm_pred'] = p
            sample['img_id'] = sample['img_id'] if sample.get('img_id') else img_id
            img_id += 1

        return samples
