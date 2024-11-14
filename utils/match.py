from scipy.optimize import linear_sum_assignment
import Levenshtein
import numpy as np
import re
import sys
import pdb
from utils.data_preprocess import textblock_with_norm_formula, normalized_formula, textblock2unicode, clean_string

# def get_norm_text_lines(lines):
#     norm_lines = []
#     for line in lines:
#         # 调用函数并设置超时时间
#         result = timed_function(textblock2unicode, textblock_with_norm_formula, line, timeout=10, print_msg=line)
#         if result:
#             norm_lines.append(result)
#         else:
#             norm_lines.append(line)
#     return norm_lines

def get_pred_category_type(pred_idx, pred_items):
        if pred_idx != -1:
            if pred_items[pred_idx].get('fine_category_type'):
                pred_pred_category_type = pred_items[pred_idx]['fine_category_type']
            else:
                pred_pred_category_type = pred_items[pred_idx]['category_type']
        else:
            pred_pred_category_type = ""
        return pred_pred_category_type

# def compute_edit_distance_matrix_new(gt_lines, matched_lines):
#     distance_matrix = np.zeros((len(gt_lines), len(matched_lines)))
#     # print('gt len: ', len(gt_lines))
#     # print('pred_len: ', len(matched_lines))
#     # print('norm_gt_lines: ', gt_lines)
#     # print('norm_pred_lines: ', matched_lines)
#     for i, gt_line in enumerate(gt_lines):
#         for j, matched_line in enumerate(matched_lines):
#             distance_matrix[i][j] = Levenshtein.distance(gt_line, matched_line)/max(len(matched_line), len(gt_line))
#     return distance_matrix

def compute_edit_distance_matrix_new(gt_lines, matched_lines):
    try:
        distance_matrix = np.zeros((len(gt_lines), len(matched_lines)))
        for i, gt_line in enumerate(gt_lines):
            for j, matched_line in enumerate(matched_lines):
                if len(gt_line) == 0 and len(matched_line) == 0:
                    distance_matrix[i][j] = 0  
                else:
                    distance_matrix[i][j] = Levenshtein.distance(gt_line, matched_line) / max(len(matched_line), len(gt_line))
        return distance_matrix
    except ZeroDivisionError:
        #print("ZeroDivisionError occurred. Outputting norm_gt_lines and norm_pred_lines:")
        # print("norm_gt_lines:", gt_lines)
        # print("norm_pred_lines:", matched_lines)
        raise  

def get_gt_pred_lines(gt_items, pred_items, line_type):
    norm_html_lines = []
    gt_lines = []
    gt_cat_list = []
    for item in gt_items:
        gt_cat_list.append(item['category_type'])
        if item.get('content'):
            gt_lines.append(str(item['content']))
            norm_html_lines.append(str(item['content']))
        elif line_type == 'text':
            gt_lines.append(str(item['text']))
        elif line_type == 'html_table':
            gt_lines.append(str(item['html']))
        elif line_type == 'formula':
            gt_lines.append(str(item['latex']))
        elif line_type == 'latex_table':
            gt_lines.append(str(item['latex']))
            norm_html_lines.append(str(item['html']))
        
    pred_lines = [str(item['content']) for item in pred_items]

    if line_type == 'formula':
        norm_gt_lines = [normalized_formula(_) for _ in gt_lines]
        norm_pred_lines = [normalized_formula(_) for _ in pred_lines]
    elif line_type == 'text':
        # norm_gt_lines = [textblock_with_norm_formula(_) for _ in gt_lines]
        # norm_pred_lines = [textblock_with_norm_formula(_) for _ in pred_lines]
        norm_gt_lines = [clean_string(textblock2unicode(_)) for _ in gt_lines]
        norm_pred_lines = [clean_string(textblock2unicode(_)) for _ in pred_lines]
        # norm_gt_lines = get_norm_text_lines(gt_lines)
        # norm_pred_lines = get_norm_text_lines(pred_lines)
    else:
        norm_gt_lines = gt_lines
        norm_pred_lines = pred_lines
    
    if line_type == 'latex_table':
        gt_lines = norm_html_lines

    
    return gt_lines, norm_gt_lines, gt_cat_list, pred_lines, norm_pred_lines


def match_gt2pred_simple(gt_items, pred_items, line_type, img_name):

    gt_lines, norm_gt_lines, gt_cat_list, pred_lines, norm_pred_lines = get_gt_pred_lines(gt_items, pred_items, line_type)
    
    match_list = []
    if not norm_gt_lines:
        # print("One of the lists is empty. Returning an empty gt result.")
        for pred_idx in range(len(norm_pred_lines)):
            match_list.append({
                'gt_idx': [-1],
                'gt': "",
                'pred_idx': [pred_idx],
                'pred': pred_lines[pred_idx],
                'gt_position': -1,
                'pred_position': pred_items[pred_idx]['position'][0],
                'norm_gt': "",
                'norm_pred': norm_pred_lines[pred_idx],
                'gt_category_type': "",
                'pred_category_type': get_pred_category_type(pred_idx, pred_items),
                'gt_attribute': [{}],
                'edit': 1,
                'img_id': img_name
            })
        return match_list
    elif not norm_pred_lines:
        # print("One of the lists is empty. Returning an empty pred result.")
        for gt_idx in range(len(norm_gt_lines)):
            match_list.append({
                'gt_idx': [gt_idx],
                'gt': gt_lines[gt_idx],
                'pred_idx': [-1],
                'pred': "",
                'gt_position': [gt_items[gt_idx].get('order') if gt_items[gt_idx].get('order') else gt_items[gt_idx].get('position', [-1])[0]],
                'pred_position': -1,
                'norm_gt': norm_gt_lines[gt_idx],
                'norm_pred': "",
                'gt_category_type': gt_cat_list[gt_idx],
                'pred_category_type': "",
                'gt_attribute': [gt_items[gt_idx].get("attribute", {})],
                'edit': 1,
                'img_id': img_name
            })
        return match_list
    
    cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, norm_pred_lines)

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    
    for gt_idx in range(len(norm_gt_lines)):
        if gt_idx in row_ind:
            row_i = list(row_ind).index(gt_idx)
            pred_idx = int(col_ind[row_i])
            pred_line = pred_lines[pred_idx]
            norm_pred_line = norm_pred_lines[pred_idx]
            edit = cost_matrix[gt_idx][pred_idx]
            # print('edit_dist', edit)
            # if edit > 0.7:
            #     print('! Not match')
        else:
            # print('No match pred')
            pred_idx = -1
            pred_line = ""
            norm_pred_line = ""
            edit = 1
        
        # print(type(gt_idx))
        # print(type(pred_idx))
        if pred_idx != -1:
            if pred_items[pred_idx].get('fine_category_type'):
                pred_pred_category_type = pred_items[pred_idx]['fine_category_type']
            else:
                pred_pred_category_type = pred_items[pred_idx]['category_type']
        else:
            pred_pred_category_type = ""
        match_list.append({
            'gt_idx': [gt_idx],
            'gt': gt_lines[gt_idx],
            'norm_gt': norm_gt_lines[gt_idx],
            'gt_category_type': gt_cat_list[gt_idx],
            'gt_position': [gt_items[gt_idx].get('order') if gt_items[gt_idx].get('order') else gt_items[gt_idx].get('position', [-1])[0]],
            'gt_attribute': [gt_items[gt_idx].get("attribute", {})],
            'pred_idx': [pred_idx],
            'pred': pred_line,
            'norm_pred': norm_pred_line,
            'pred_category_type': pred_pred_category_type,
            'pred_position': pred_items[pred_idx]['position'][0] if pred_idx != -1 else -1,
            'edit': edit,
            'img_id': img_name
        })
        # print('-'*10)
        # [([0,1], 0),(2, 1), (1,2)] --> [0,2,1]/[0,1,2]
    
    for pred_idx in range(len(norm_pred_lines)):  # 把没有任何匹配的pred也加上计算
        if pred_idx in col_ind:
            continue
        # print('gt_idx', gt_idx)
        # print('new gt: ', gt_line)
        if pred_items[pred_idx].get('fine_category_type'):
            pred_pred_category_type = pred_items[pred_idx]['fine_category_type']
        else:
            pred_pred_category_type = pred_items[pred_idx]['category_type']
        match_list.append({
            'gt_idx': [-1],
            'gt': "",
            'norm_gt': "",
            'gt_category_type': "",
            'gt_position': [-1],
            'gt_attribute': [{}],
            'pred_idx': [pred_idx],
            'pred': pred_lines[pred_idx],
            'norm_pred': norm_pred_lines[pred_idx],
            'pred_category_type': pred_pred_category_type,
            'pred_position': pred_items[pred_idx]['position'][0],
            'edit': 1,
            'img_id': img_name
        })
    return match_list


def match_gt2pred_no_split(gt_items, pred_items, line_type, img_name):
    # 直接把gt和pred按position拼接成一个整体计算
    gt_lines, norm_gt_lines, gt_cat_list, pred_lines, norm_pred_lines = get_gt_pred_lines(gt_items, pred_items, line_type)
    gt_line_with_position = []
    for gt_line, norm_gt_line, gt_item in zip(gt_lines, norm_gt_lines, gt_items):
        gt_position = gt_item['order'] if gt_item.get('order') else gt_item.get('position', [-1])[0]
        gt_line_with_position.append((gt_position, gt_line, norm_gt_line))
    sorted_gt_lines = sorted(gt_line_with_position, key=lambda x: x[0])
    gt = '\n\n'.join([_[1] for _ in sorted_gt_lines])
    norm_gt = '\n\n'.join([_[2] for _ in sorted_gt_lines])
    pred_line_with_position = [(pred_item['position'], pred_line, pred_norm_line) for pred_line, pred_norm_line, pred_item in zip(pred_lines, norm_pred_lines, pred_items)]
    sorted_pred_lines = sorted(pred_line_with_position, key=lambda x: x[0])
    pred = '\n\n'.join([_[1] for _ in sorted_pred_lines])
    norm_pred = '\n\n'.join([_[2] for _ in sorted_pred_lines])
    # edit = Levenshtein.distance(norm_gt, norm_pred)/max(len(norm_gt), len(norm_pred))
    return [{
            'gt_idx': [-1],
            'gt': gt,
            'norm_gt': norm_gt,
            'gt_category_type': "text_merge",
            'gt_position': [-1],
            'gt_attribute': [{}],
            'pred_idx': [-1],
            'pred': pred,
            'norm_pred': norm_pred,
            'pred_category_type': "text_merge",
            'pred_position': -1,
            # 'edit': edit,
            'img_id': img_name
        }]

# def match_gt2pred_textblock_simple(gt_items, pred_lines, img_name):   # 仅存档，不再单独提取inline formula
#     text_inline_match_s = match_gt2pred_simple(gt_items, pred_lines, 'text', img_name)
#     plain_text_match = []
#     inline_formula_match = []
#     for item in text_inline_match_s:
#         # print('GT')
#         # plaintext_gt, inline_gt_items = inline_filter_unicode(item['gt'])  # TODO:这个后续最好是直接从span里提取出来
#         plaintext_gt, inline_gt_items = inline_filter(item['gt'])  # TODO:这个后续最好是直接从span里提取出来
#         #print('----------inline_gt_items--------------',inline_gt_items)
#         # print('Pred')
#         # print(item['pred'])
#         # plaintext_pred, inline_pred_items = inline_filter_unicode(item['pred'])
#         plaintext_pred, inline_pred_items = inline_filter(item['pred'])
#         #print('----------inline_gt_items--------------',inline_pred_items)
#         # print('inline_pred_list', inline_pred_list)
#         # print('plaintext_pred: ', plaintext_pred)
#         # plaintext_gt = plaintext_gt.replace(' ', '')
#         # plaintext_pred = plaintext_pred.replace(' ', '')
#         if plaintext_gt or plaintext_pred:
#             edit = Levenshtein.distance(plaintext_gt, plaintext_pred)/max(len(plaintext_pred), len(plaintext_gt))
#             if item['gt_idx'][0] == -1:
#                 gt_position = [-1]
#             else:
#                 gt_idx = item['gt_idx'][0]
#                 gt_position = [gt_items[gt_idx].get('order') if gt_items[gt_idx].get('order') else gt_items[gt_idx].get('position', [-1])[0]]
#             plain_text_match.append({
#                 'gt_idx': item['gt_idx'],
#                 'gt': plaintext_gt,
#                 'norm_gt': plaintext_gt,
#                 'gt_category_type': item['gt_category_type'],
#                 'gt_position': gt_position,
#                 'pred_idx': item['pred_idx'],
#                 'pred': plaintext_pred,
#                 'norm_pred': plaintext_pred,
#                 'pred_category_type': item['pred_category_type'],
#                 'pred_position': item['pred_position'],
#                 'edit': edit,
#                 'img_id': img_name
#             })

#         if inline_gt_items or inline_pred_items:
#             # inline_gt_items = [{'category_type': 'equation_inline', 'latex': line} for line in inline_gt_list]
#             # inline_pred_items = [{'category_type': 'equation_inline', 'content': line} for line in inline_pred_list]
#             # print('inline_gt_items: ', inline_gt_items)
#             # print('inline_pred_items: ', inline_pred_items)
#             inline_formula_match_s = match_gt2pred_simple(inline_gt_items, inline_pred_items, 'formula', img_name)
#             inline_formula_match.extend(inline_formula_match_s)

    
#     return plain_text_match, inline_formula_match
    
