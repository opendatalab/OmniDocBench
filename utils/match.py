from scipy.optimize import linear_sum_assignment
# from rapidfuzz.distance import Levenshtein
import Levenshtein
import numpy as np
import re
from utils.extract import inline_filter


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


def match_gt2pred(gt_items, pred_lines, line_type, img_name):
    norm_gt_lines = []
    gt_cat_list = []
    for item in gt_items:
        gt_cat_list.append(item['category_type'])
        if item.get('text'):
            norm_gt_lines.append(str(item['text']))
        elif item.get('html'):
            norm_gt_lines.append(str(item['html']))
        elif item.get('latex'):
            if 'formula' in item['category_type']:
                norm_gt_lines.append(normalized_formula(str(item['latex'])))
    
    if line_type == 'formula':
        # norm_gt_lines = [normalized_formula(str(line)) for line in gt_lines]
        norm_pred_lines = [normalized_formula(str(line)) for line in pred_lines]
    else:
        # norm_gt_lines = [str(line) for line in gt_lines]
        norm_pred_lines = [str(line) for line in pred_lines]
    
    cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, norm_pred_lines)

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    match_list = []
    for gt_idx in range(len(norm_gt_lines)):
        gt_line = norm_gt_lines[gt_idx]
        # print('gt_idx', gt_idx)
        # print('new gt: ', gt_line)

        if gt_idx in row_ind:
            row_i = list(row_ind).index(gt_idx)
            pred_idx = int(col_ind[row_i])
            pred_line = norm_pred_lines[pred_idx]
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
        match_list.append({
            'gt_idx': gt_idx,
            'gt': gt_line,
            'category_type': gt_cat_list[gt_idx],
            'pred_idx': pred_idx,
            'pred': pred_line,
            'edit': edit,
            'img_id': img_name
        })
        # print('-'*10)
    
    return match_list


def match_gt2pred_textblock(gt_items, pred_lines, img_name):
    text_inline_match_s = match_gt2pred(gt_items, pred_lines, 'text', img_name)
    plain_text_match = []
    inline_formula_match = []
    for item in text_inline_match_s:
        plaintext_gt, inline_gt_list = inline_filter(item['gt'])  # TODO:这个后续最好是直接从span里提取出来
        plaintext_pred, inline_pred_list = inline_filter(item['pred'])
        # print('inline_pred_list', inline_pred_list)
        # print('plaintext_pred: ', plaintext_pred)
        plaintext_gt = plaintext_gt.replace(' ', '')
        plaintext_pred = plaintext_pred.replace(' ', '')
        if plaintext_gt or plaintext_pred:
            edit = Levenshtein.distance(plaintext_gt, plaintext_pred)/max(len(plaintext_pred), len(plaintext_gt))
            plain_text_match.append({
                'gt_idx': item['gt_idx'],
                'gt': plaintext_gt,
                'category_type': item['category_type'],
                'pred_idx': item['pred_idx'],
                'pred': plaintext_pred,
                'edit': edit,
                'img_id': img_name
            })

        if inline_gt_list:
            inline_gt_items = [{'category_type': 'equation_inline', 'latex': line} for line in inline_gt_list]
            inline_formula_match_s = match_gt2pred(inline_gt_items, inline_pred_list, 'formula', img_name)
            inline_formula_match.extend(inline_formula_match_s)

    
    return plain_text_match, inline_formula_match
    