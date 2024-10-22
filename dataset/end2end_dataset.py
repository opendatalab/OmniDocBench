import json
import os
from collections import defaultdict
from utils.extract import md_tex_filter
from utils.match import match_gt2pred, match_gt2pred_textblock
from utils.read_files import read_md_file
from registry.registry import DATASET_REGISTRY
from dataset.recog_dataset import *

@DATASET_REGISTRY.register("end2end_dataset")
class End2EndDataset():
    def __init__(self, cfg_task):
        gt_path = cfg_task['dataset']['ground_truth']['data_path']
        pred_folder = cfg_task['dataset']['prediction']['data_path']
        with open(gt_path, 'r') as f:
            gt_samples = json.load(f)

        self.samples = self.get_matched_elements(gt_samples, pred_folder)
        


    def __getitem__(self, cat_name, idx):
        return self.samples[cat_name][idx]
    
    # def get_with_image_name(self, image_name):
    #     return self.samples_dict[image_name]
    
    def get_page_elements(self, selected_annos):
        saved_element_dict = defaultdict(list)
        for item in selected_annos['layout_dets']:
            saved_element_dict[item["category_type"]].append(item)
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
            if item['category_type'] not in ignore_category_list:
                filted_items.append(item)
        return filted_items

    def get_order_paired(self, order_match_s, img_name):
        matched = [(item['gt_idx'], item['pred_idx']) for item in order_match_s]
        read_order_gt = [i[0] for i in sorted(matched, key=lambda x: x[0])]   # 以GT的idx来sort，获取GT排序的GT_idx
        read_order_pred = [i[0] for i in sorted(matched, key=lambda x: x[1])]  # 以pred的idx来sort，获取Pred排序的GT_idx
        return {
            'gt': read_order_gt,
            'pred': read_order_pred,
            'img_id': img_name
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
        inline_formula_match = []
        title_match = []
        display_formula_match = []
        table_match = []
        order_match = []

        for sample in gt_samples:
            img_name = os.path.basename(sample["page_info"]["image_path"])
            
            # # test english content only
            # if img_name.startswith('yanbao') or img_name.startswith('jiaocai_2013_AMC_12A.pdf_9'):
            #     continue

            # print('Process: ', img_name)
            pred_path = os.path.join(pred_folder, img_name[:-4] + '.md')
            if not os.path.exists(pred_path):
                print(f'!!!WARNING: No prediction for {img_name}')
                continue
            else:
                pred_content = read_md_file(pred_path)
            pred_text_list, pred_display_list, pred_table_list, pred_title_list = md_tex_filter(pred_content)
            # print('pred_text_list: ', pred_text_list)
            # print('pred_display_list: ', pred_display_list)
            # print('pred_table_list', pred_table_list)
            # print('pred_title_list: ', pred_title_list)

            gt_page_elements = self.get_page_elements(sample)
            # print('gt_page_elements: ', gt_page_elements)
            
            # 文本相关的所有element，不涉及的类别有figure, table, table_mask, equation_isolated, equation_caption, equation_ignore, equation_inline, footnote_mark, page_number, abandon, list, text_mask, need_mask
            text_all = self.get_page_elements_list(gt_page_elements, ['text_block', 'title', 'code_txt', 'code_txt_caption', 'list_merge', 'reference',
                                                    'figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption'
                                                    'header', 'footer', 'page_footnote'])           
            formated_display_formula = []
            plain_text_match_clean = []
            if text_all:
                gt_text_list = self.get_sorted_text_list(text_all)
                # print('gt_text_list: ', gt_text_list)
                plain_text_match_s, inline_formula_match_s = match_gt2pred_textblock(gt_text_list, pred_text_list, img_name)
                # print('plain_text_match_s: ', plain_text_match_s)
                # print('-'*10)
                # print('inline_formula_match_s', inline_formula_match_s)
                # print('-'*10)
                # 文本类需要ignore的类别
                plain_text_match_clean = self.filtered_out_ignore(plain_text_match_s, ['figure_caption', 'figure_footnote', 'table_caption', 'table_footnote', 'code_algorithm', 'code_algorithm_caption', 'header', 'footer', 'page_footnote'])
                
                plain_text_match.extend(plain_text_match_clean)

                formated_inline_formula = self.formula_format(inline_formula_match_s, img_name)
                inline_formula_match.extend(formated_inline_formula)
                # print('inline_formula_match_s: ', inline_formula_match_s)
                # print('-'*10)
                
            if gt_page_elements.get('title'):
                gt_title_list = self.get_sorted_text_list(gt_page_elements['title'])
                # print('gt_title_list: ', gt_title_list)
                title_match_s = match_gt2pred(gt_title_list, pred_title_list, 'text', img_name)
                title_match.extend(title_match_s)
                # print('title_match_s: ', title_match_s)
                # print('-'*10)
            if gt_page_elements.get('isolate_formula'):
                gt_display_list = self.get_sorted_text_list(gt_page_elements['isolate_formula'])
                # print('gt_display_list: ', gt_display_list)
                display_formula_match_s = match_gt2pred(gt_display_list, pred_display_list, 'formula', img_name)
                formated_display_formula = self.formula_format(display_formula_match_s, img_name)
                # print('display_formula_match_s: ', display_formula_match_s)
                # print('-'*10)
                display_formula_match.extend(formated_display_formula)
            if gt_page_elements.get('table'):
                gt_table_list = self.get_sorted_text_list(gt_page_elements['table'])
                # print('gt_table_list', gt_table_list)
                table_match_s = match_gt2pred(gt_table_list, pred_table_list, 'table', img_name)
                # print('table_match_s: ', table_match_s)
                # print('-'*10)
                table_match.extend(table_match_s)

            # 阅读顺序的处理
            order_match_s = []
            for mateches in [plain_text_match_clean, formated_display_formula]:
                if mateches:
                    order_match_s.extend(mateches)
            if order_match_s:
                order_match.append(self.get_order_paired(order_match_s, img_name))

        ## 提取匹配数据检查
        # with open('/mnt/petrelfs/ouyanglinke/PDF-Extract-Kit-v2/validation/result/plain_text_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(plain_text_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/PDF-Extract-Kit-v2/validation/result/title_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(title_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/PDF-Extract-Kit-v2/validation/result/table_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(table_match, f, indent=4, ensure_ascii=False)
        # with open('/mnt/petrelfs/ouyanglinke/PDF-Extract-Kit-v2/validation/result/order_match.json', 'w', encoding='utf-8') as f:
        #     json.dump(order_match, f, indent=4, ensure_ascii=False)

        matched_samples_all = {
            'text_block': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(plain_text_match),
            'title': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(title_match), 
            'inline_formula': DATASET_REGISTRY.get('recogition_end2end_formula_dataset')(inline_formula_match), 
            'display_formula':  DATASET_REGISTRY.get('recogition_end2end_formula_dataset')(display_formula_match), 
            'table': DATASET_REGISTRY.get('recogition_end2end_table_dataset')(table_match),
            'reading_order': DATASET_REGISTRY.get('recogition_end2end_base_dataset')(order_match)
        }
        
        return matched_samples_all
    

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
    
@DATASET_REGISTRY.register("recogition_end2end_formula_dataset")
class RecognitionEnd2EndFormulaDataset(RecognitionFormulaDataset):
    def __init__(self, samples):
        self.samples = []
        img_id = 0
        for sample in samples:
            gt = self.normalize_text(sample['gt'])
            pred = self.normalize_text(sample['pred'])
            self.samples.append({
                'gt': gt,
                'pred': pred,
                'img_id': sample['img_id'] if sample.get('img_id') else img_id
            })
            img_id += 1
    
@DATASET_REGISTRY.register("recogition_end2end_table_dataset")
class RecognitionEnd2EndTableDataset(RecognitionTableDataset):
    def __init__(self, samples):
        self.samples = self.normalize_data(samples)

    def normalize_data(self, samples):
        norm_samples = []
        img_id = 0
        for sample in samples:
            p = sample['pred']
            r = sample['gt']
            _, p = self.process_table(p)
            _, r = self.process_table(r)
            norm_samples.append({
                'gt': self.strcut_clean(self.clean_table(r)),
                'pred': self.strcut_clean(p),
                'img_id': sample['img_id'] if sample.get('img_id') else img_id
            })
            img_id += 1
        return norm_samples