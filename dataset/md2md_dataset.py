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

@DATASET_REGISTRY.register("md2md_dataset")
class Md2MdDataset():
    def __init__(self, cfg_task):
        gt_folder = cfg_task['dataset']['ground_truth']['data_path']
        pred_folder = cfg_task['dataset']['prediction']['data_path']
        self.match_method = cfg_task['dataset'].get('match_method', 'simple_match')

        self.samples = self.get_matched_elements(gt_folder, pred_folder)
        
    def __getitem__(self, cat_name, idx):
        return self.samples[cat_name][idx]

    def get_order_paired(self, order_match_s, img_name):
        matched = [(item['gt_position'], item['pred_position']) for item in order_match_s if (item['gt_position'] != [""] and item['pred_position'] != "")]
        gt_idx_all = [item['gt_position'] for item in order_match_s if (item['gt_position'] != [""])]
        read_order_pred = [i[0] for i in sorted(matched, key=lambda x: x[1])]  # Sort by pred idx to get Pred ordered GT_idx
        read_order_gt = sum(gt_idx_all, []) # Convert to 1D list
        read_order_gt = [x for x in read_order_gt if x]  # During truncation merging, some discarded classes may be merged in. Remove them when calculating edit distance
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

    def get_matched_elements(self, gt_folder, pred_folder):
        plain_text_match = []
        display_formula_match = []
        html_table_match = []
        latex_table_match = []
        order_match = []

        for sample_name in tqdm(os.listdir(gt_folder)):
            if not sample_name.endswith('.md'):
                continue
            
            img_name = sample_name[:-3] + '.jpg'

            gt_content = read_md_file(os.path.join(gt_folder, sample_name))

            pred_path = os.path.join(pred_folder, sample_name)
            if not os.path.exists(pred_path):
                print(f'!!!WARNING: No prediction for {sample_name}')
                continue
            else:
                pred_content = read_md_file(pred_path)
            
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

            gt_dataset = md_tex_filter(gt_content)
            pred_dataset = md_tex_filter(pred_content)   

            display_formula_match_s = []
            plain_text_match_clean = []
            if gt_dataset['text_all']:
                plain_text_match_s = match_gt2pred(gt_dataset['text_all'], pred_dataset['text_all'], 'text', img_name)  
                # No ignore logic for text categories in markdown
                plain_text_match_clean = plain_text_match_s              
                plain_text_match.extend(plain_text_match_s)
                
            # if gt_page_elements.get('title'):
            #     gt_title_list = self.get_sorted_text_list(gt_page_elements['title'])
            #     # print('gt_title_list: ', gt_title_list)
            #     title_match_s = match_gt2pred(gt_title_list, pred_title_list, 'text', img_name)
            #     title_match.extend(title_match_s)
                # print('title_match_s: ', title_match_s)
                # print('-'*10)
            if gt_dataset.get('equation_isolated'):
                display_formula_match_s = match_gt2pred(gt_dataset['equation_isolated'], pred_dataset['equation_isolated'], 'formula', img_name)
                display_formula_match_s = [x for x in display_formula_match_s if x['gt_idx'] != [""] and x['gt_category_type'] != 'equation_inline']  # Remove extra preds since inline formulas are also included for matching, and remove GT that are inline formulas
                display_formula_match.extend(display_formula_match_s)
            if gt_dataset.get('latex_table') and pred_dataset.get('latex_table'): # By default the model won't randomly output both latex and html, but choose one; Note that table format in GT markdown needs to match Pred
                # print('gt_table_list', gt_table_list)
                table_match_s = match_gt2pred(gt_dataset['latex_table'], pred_dataset['latex_table'], 'latex_table', img_name)
                table_match_s = [x for x in table_match_s if x['gt_idx'] != [""]]  # Remove extra preds
                latex_table_match.extend(table_match_s)
            elif gt_dataset.get('html_table') and pred_dataset.get('html_table'):   
                table_match_s = match_gt2pred(gt_dataset['html_table'], pred_dataset['html_table'], 'html_table', img_name)
                table_match_s = [x for x in table_match_s if x['gt_idx'] != [""]]  # Remove extra preds
                html_table_match.extend(table_match_s)
                # print('table_match_s: ', table_match_s)
                # print('-'*10)
            else:
                if gt_dataset.get('latex_table') or gt_dataset.get('html_table'):
                    print('GT table is not empty. But pred is empty or its format is different from gt.')
                if pred_dataset.get('latex_table') or pred_dataset.get('html_table'):
                    print('Pred table is not empty. But gt is empty or its format is different from pred.')

            # Process reading order
            # order_match_s = []
            # for mateches in [plain_text_match_clean, display_formula_match_s]:
            #     if mateches:
            #         order_match_s.extend(mateches)
            order_match_s = self.get_order_paired(plain_text_match_clean, img_name)
            if order_match_s:
                order_match.append(order_match_s)

        if latex_table_match: # By default the model won't randomly output both latex and html, but choose one
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