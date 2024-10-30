from scipy.optimize import linear_sum_assignment
# from rapidfuzz.distance import Levenshtein
import Levenshtein
import numpy as np
import re
from utils.extract import inline_filter,inline_filter_unicode
import sys
import pdb
from pylatexenc.latex2text import LatexNodes2Text

def compute_edit_distance_matrix_new(gt_lines, matched_lines):
    distance_matrix = np.zeros((len(gt_lines), len(matched_lines)))
    # print('gt len: ', len(gt_lines))
    # print('pred_len: ', len(matched_lines))
    # print('norm_gt_lines: ', gt_lines)
    # print('norm_pred_lines: ', matched_lines)
    for i, gt_line in enumerate(gt_lines):
        for j, matched_line in enumerate(matched_lines):
            distance_matrix[i][j] = Levenshtein.distance(gt_line, matched_line)/max(len(matched_line), len(gt_line))
    return distance_matrix


def normalized_formula(text):
    # 把数学公式做一下norm
    filter_list = ['\\mathbf', '\\mathrm', '\\mathnormal', '\\mathit', '\\mathbb', '\\mathcal', '\\mathscr', '\\mathfrak', '\\mathsf', '\\mathtt', 
                   '\\textbf', '\\text', '\\boldmath', '\\boldsymbol', '\\operatorname', '\\bm',
                   '\\symbfit', '\\mathbfcal', '\\symbf', '\\scriptscriptstyle', '\\notag',
                   '\\setlength', '\\coloneqq', '\\space', '\\thickspace', '\\thinspace', '\\medspace', '\\nobreakspace', '\\negmedspace',
                   '\\quad', '\\qquad', '\\enspace', '\\substackw',
                   '\\left', '\\right', '{', '}', ' ']
    
    # delimiter_filter
    pattern = re.compile(r"\\\[(.+?)(?<!\\)\\\]")
    match = pattern.search(text)

    if match:
        text = match.group(1).strip()
    
    tag_pattern = re.compile(r"\\tag\{.*?\}")
    text = tag_pattern.sub('', text)
    hspace_pattern = re.compile(r"\\hspace\{.*?\}")
    text = hspace_pattern.sub('', text)
    begin_pattern = re.compile(r"\\begin\{.*?\}")
    text = begin_pattern.sub('', text)
    end_pattern = re.compile(r"\\end\{.*?\}")
    text = end_pattern.sub('', text)
    col_sep = re.compile(r"\\arraycolsep.*?\}")
    text = col_sep.sub('', text)
    text = text.strip('.')
    
    for filter_text in filter_list:
        text = text.replace(filter_text, '')
        
    # text = normalize_text(delimiter_filter(text))
    # text = delimiter_filter(text)
    text = text.lower()
    return text


def match_gt2pred_simple(gt_items, pred_items, line_type, img_name):

    norm_html_lines = []
    gt_lines = []
    gt_cat_list = []
    for item in gt_items:
        gt_cat_list.append(item['category_type'])
        if item.get('content'):
            gt_lines.append(str(item['content']))
        elif line_type == 'text' or line_type == 'formula':   # TODO: 要把formula换成latex
            gt_lines.append(str(item['text']))
        elif line_type == 'html_table':
            gt_lines.append(str(item['html']))
        elif line_type == 'latex_table':
            gt_lines.append(str(item['latex']))
            norm_html_lines.append(str(item['html']))
        
    if line_type == 'formula':
        norm_gt_lines = [normalized_formula(_) for _ in gt_lines]
    else:
        norm_gt_lines = gt_lines
    
    pred_lines = [str(item['content']) for item in pred_items]
    if line_type == 'formula':
        norm_pred_lines = [normalized_formula(_) for _ in pred_lines]
    else:
        norm_pred_lines = pred_lines
    
    cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, norm_pred_lines)
    if line_type == 'latex_table':
        gt_lines = norm_html_lines

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    match_list = []
    for gt_idx in range(len(norm_gt_lines)):
        gt_line = gt_lines[gt_idx]
        # print('gt_idx', gt_idx)
        # print('new gt: ', gt_line)

        if gt_idx in row_ind:
            row_i = list(row_ind).index(gt_idx)
            pred_idx = int(col_ind[row_i])
            pred_line = pred_lines[pred_idx]
            edit = cost_matrix[gt_idx][pred_idx]
            # print('edit_dist', edit)
            # if edit > 0.7:
            #     print('! Not match')
        else:
            # print('No match pred')
            pred_idx = -1
            pred_line = ""
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
            'gt': gt_line,
            'gt_category_type': gt_cat_list[gt_idx],
            'gt_position': [gt_items[gt_idx].get('order') if gt_items[gt_idx].get('order') else gt_items[gt_idx].get('position', [-1])[0]],
            'pred_idx': [pred_idx],
            'pred': pred_line,
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
        pred_line = pred_lines[pred_idx]
        # print('gt_idx', gt_idx)
        # print('new gt: ', gt_line)
        if pred_items[pred_idx].get('fine_category_type'):
            pred_pred_category_type = pred_items[pred_idx]['fine_category_type']
        else:
            pred_pred_category_type = pred_items[pred_idx]['category_type']
        match_list.append({
            'gt_idx': [-1],
            'gt': "",
            'gt_category_type': "",
            'gt_position': [-1],
            'pred_idx': [pred_idx],
            'pred': pred_line,
            'pred_category_type': pred_pred_category_type,
            'pred_position': pred_items[pred_idx]['position'][0],
            'edit': 1,
            'img_id': img_name
        })
    
    return match_list


def match_gt2pred_textblock_simple(gt_items, pred_lines, img_name):
    text_inline_match_s = match_gt2pred_simple(gt_items, pred_lines, 'text', img_name)
    plain_text_match = []
    inline_formula_match = []
    for item in text_inline_match_s:
        # print('GT')
        plaintext_gt, inline_gt_items = inline_filter_unicode(item['gt'])  # TODO:这个后续最好是直接从span里提取出来
        #print('----------inline_gt_items--------------',inline_gt_items)
        # print('Pred')
        # print(item['pred'])
        plaintext_pred, inline_pred_items = inline_filter_unicode(item['pred'])
        #print('----------inline_gt_items--------------',inline_pred_items)
        # print('inline_pred_list', inline_pred_list)
        # print('plaintext_pred: ', plaintext_pred)
        # plaintext_gt = plaintext_gt.replace(' ', '')
        # plaintext_pred = plaintext_pred.replace(' ', '')
        if plaintext_gt or plaintext_pred:
            edit = Levenshtein.distance(plaintext_gt, plaintext_pred)/max(len(plaintext_pred), len(plaintext_gt))
            if item['gt_idx'][0] == -1:
                gt_position = [-1]
            else:
                gt_idx = item['gt_idx'][0]
                gt_position = [gt_items[gt_idx].get('order') if gt_items[gt_idx].get('order') else gt_items[gt_idx].get('position', [-1])[0]]
            plain_text_match.append({
                'gt_idx': item['gt_idx'],
                'gt': plaintext_gt,
                'gt_category_type': item['gt_category_type'],
                'gt_position': gt_position,
                'pred_idx': item['pred_idx'],
                'pred': plaintext_pred,
                'pred_category_type': item['pred_category_type'],
                'pred_position': item['pred_position'],
                'edit': edit,
                'img_id': img_name
            })

        if inline_gt_items or inline_pred_items:
            # inline_gt_items = [{'category_type': 'equation_inline', 'latex': line} for line in inline_gt_list]
            # inline_pred_items = [{'category_type': 'equation_inline', 'content': line} for line in inline_pred_list]
            # print('inline_gt_items: ', inline_gt_items)
            # print('inline_pred_items: ', inline_pred_items)
            inline_formula_match_s = match_gt2pred_simple(inline_gt_items, inline_pred_items, 'formula', img_name)
            inline_formula_match.extend(inline_formula_match_s)

    
    return plain_text_match, inline_formula_match
    
