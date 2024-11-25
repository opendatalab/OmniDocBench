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
    
    # def get_with_image_name(self, image_name):
    #     return self.samples_dict[image_name]

    def get_order_paired(self, order_match_s, img_name):
        matched = [(item['gt_position'], item['pred_position']) for item in order_match_s if (item['gt_position'] != [""] and item['pred_position'] != "")]
        gt_idx_all = [item['gt_position'] for item in order_match_s if (item['gt_position'] != [""])]
        # read_order_gt = [i[0] for i in sorted(matched, key=lambda x: x[0])]   # 以GT的idx来sort，获取GT排序的GT_idx
        # print(matched)
        read_order_pred = [i[0] for i in sorted(matched, key=lambda x: x[1])]  # 以pred的idx来sort，获取Pred排序的GT_idx
        # read_order_gt = sorted(read_order_pred) # 以GT的idx来sort，获取GT排序的GT_idx
        read_order_gt = sum(gt_idx_all, []) # 转成一个一维list
        read_order_gt = [x for x in read_order_gt if x]  # 在截断合并中，有可能会合并进来一些舍弃类，这些在计算编辑距离的时候把它直接去掉
        gt = sorted(read_order_gt) # 以所有GT的idx来sort，获取GT排序的GT_idx
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
            return {}  # 如果页面GT和pred都是空的，就返回空

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
            # # test english content only
            # if img_name.startswith('yanbao') or img_name.startswith('jiaocai_2013_AMC_12A.pdf_9'):
            #     continue

            # print('Process: ', img_name)
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
            # print('pred_text_list: ', pred_text_list)
            # print('pred_display_list: ', pred_display_list)
            # print('pred_latex_table_list', pred_latex_table_list)
            # print('pred_html_table_list', pred_html_table_list)
            # print('pred_title_list: ', pred_title_list)      

            # print('-------------!!text_all: ', text_all)
            display_formula_match_s = []
            plain_text_match_clean = []
            if gt_dataset['text_all']:
                # print('gt_text_list: ', gt_text_list)
                # plain_text_match_s, inline_formula_match_s = match_gt2pred_textblock(gt_dataset['text_all'], pred_dataset['text_all'], img_name)
                plain_text_match_s = match_gt2pred(gt_dataset['text_all'], pred_dataset['text_all'], 'text', img_name)
                # print('plain_text_match_s: ', plain_text_match_s)
                # print('-'*10)
                # print('inline_formula_match_s', inline_formula_match_s)
                # print('-'*10)
                
                # 文本类需要ignore的类别在markdown里没有ignore逻辑
                plain_text_match_clean = plain_text_match_s
                
                plain_text_match.extend(plain_text_match_s)

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
            if gt_dataset.get('equation_isolated'):
                # print('gt_display_list: ', gt_display_list)
                display_formula_match_s = match_gt2pred(gt_dataset['equation_isolated'], pred_dataset['equation_isolated'], 'formula', img_name)
                # formated_display_formula = self.formula_format(display_formula_match_s, img_name)
                # print('display_formula_match_s: ', display_formula_match_s)
                # print('-'*10)
                display_formula_match_s = [x for x in display_formula_match_s if x['gt_idx'] != [""] and x['gt_category_type'] != 'equation_inline']  # 把多余的pred直接去掉，因为pred里把行内公式也放进来一起匹配了，并且把GT为行内公式的也去掉
                display_formula_match.extend(display_formula_match_s)
            if gt_dataset.get('latex_table') and pred_dataset.get('latex_table'): # 这里默认模型不会同时随机输出latex或html，而是二选一; 注意，GT的markdown里的table格式需要跟Pred一致
                # print('gt_table_list', gt_table_list)
                table_match_s = match_gt2pred(gt_dataset['latex_table'], pred_dataset['latex_table'], 'latex_table', img_name)
                table_match_s = [x for x in table_match_s if x['gt_idx'] != [""]]  # 把多余的pred直接去掉  
                latex_table_match.extend(table_match_s)
            elif gt_dataset.get('html_table') and pred_dataset.get('html_table'):   
                table_match_s = match_gt2pred(gt_dataset['html_table'], pred_dataset['html_table'], 'html_table', img_name)
                table_match_s = [x for x in table_match_s if x['gt_idx'] != [""]]  # 把多余的pred直接去掉
                html_table_match.extend(table_match_s)
                # print('table_match_s: ', table_match_s)
                # print('-'*10)
            else:
                if gt_dataset.get('latex_table') or gt_dataset.get('html_table'):
                    print('GT table is not empty. But pred is empty or its format is different from gt.')
                if pred_dataset.get('latex_table') or pred_dataset.get('html_table'):
                    print('Pred table is not empty. But gt is empty or its format is different from pred.')

            # 阅读顺序的处理
            # order_match_s = []
            # for mateches in [plain_text_match_clean, display_formula_match_s]:
            #     if mateches:
            #         order_match_s.extend(mateches)
            order_match_s = self.get_order_paired(plain_text_match_clean, img_name)
            if order_match_s:
                order_match.append(order_match_s)

        if latex_table_match: # 这里默认模型不会同时随机输出latex或html，而是二选一
            table_match = latex_table_match
            table_format = 'latex'
        else:
            table_match = html_table_match
            table_format = 'html'

        # # 提取匹配数据检查
        # with open('/mnt/petrelfs/ouyanglinke/DocParseEval/result/plain_text_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(plain_text_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/DocParseEval/result/table_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(table_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/DocParseEval/result/order_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(order_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/DocParseEval/result/display_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(display_formula_match, f, indent=4, ensure_ascii=False)

        matched_samples_all = {
            'text_block': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(plain_text_match),
            # 'inline_formula': DATASET_REGISTRY.get('recogition_end2end_formula_dataset')(inline_formula_match), 
            'display_formula':  DATASET_REGISTRY.get('recogition_end2end_base_dataset')(display_formula_match), 
            'table': DATASET_REGISTRY.get('recogition_end2end_table_dataset')(table_match, table_format),
            'reading_order': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(order_match)
        }
        
        return matched_samples_all