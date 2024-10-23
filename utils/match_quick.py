from scipy.optimize import linear_sum_assignment
# from rapidfuzz.distance import Levenshtein
import Levenshtein
import numpy as np
import re
from modules.extract import inline_filter
import os
import json
from collections import defaultdict, Counter
import copy
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


def match_gt2pred(gt_lines, pred_lines, line_type):
    print('--------------------------------------------------------------------------------------------------------------------')
    
    if line_type == 'formula':
        norm_gt_lines = [normalized_formula(str(line)) for line in gt_lines]
        norm_pred_lines = [normalized_formula(str(line)) for line in pred_lines]

    else:
        norm_gt_lines = [str(line) for line in gt_lines]
        norm_pred_lines = [str(line) for line in pred_lines]
    if not norm_gt_lines :
        print("One of the lists is empty. Returning an empty result.")
        return [{
                'gt_idx': 0,
                'gt': None,
                'pred_idx': str([0]),
                'pred': norm_pred_lines[0],
                'edit': 1
            }]
    elif not norm_pred_lines:
        print("One of the lists is empty. Returning an empty result.")
        return [{
                'gt_idx': 0,
                'gt': norm_gt_lines[0],
                'pred_idx': str([0]),
                'pred': None,
                'edit': 1
            }]
    elif len(norm_gt_lines) == 1 and len(norm_pred_lines) == 1:
        edit_distance = Levenshtein.distance(norm_gt_lines[0], norm_pred_lines[0])
        normalized_edit_distance = edit_distance / max(len(norm_gt_lines[0]), len(norm_pred_lines[0]))
        print("Both lists have only one element. Matching them directly.")
        return [ {
                'gt_idx': 0,
                'gt': norm_gt_lines[0],
                'pred_idx': str([0]),
                'pred': norm_pred_lines[0],
                'edit': normalized_edit_distance
            }]
    cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, norm_pred_lines)
    matched_col_idx, row_ind, cost_list = cal_final_match(cost_matrix, norm_gt_lines, norm_pred_lines)
    
    gt_lens_dict, pred_lens_dict = initialize_indices(norm_gt_lines, norm_pred_lines)

    matches, unmatched_gt_indices, unmatched_pred_indices = process_matches(matched_col_idx, row_ind, cost_list, norm_gt_lines, norm_pred_lines, pred_lines)

    matching_dict = fuzzy_match_unmatched_items(unmatched_gt_indices, norm_gt_lines, norm_pred_lines)

    final_matches = merge_matches(matches, matching_dict)

    recalculate_edit_distances(final_matches, gt_lens_dict, norm_gt_lines, norm_pred_lines)
    
    converted_final_matches = convert_final_matches(final_matches, norm_gt_lines, norm_pred_lines)
    for entry in converted_final_matches:
        print(entry)

    # row_ind, col_ind = linear_sum_assignment(cost_matrix)

    
    
    # match_list = []
    # for gt_idx in range(len(norm_gt_lines)):
    #     gt_line = norm_gt_lines[gt_idx]
    #     # print('gt_idx', gt_idx)
    #     # print('new gt: ', gt_line)

    #     if gt_idx in row_ind:
    #         row_i = list(row_ind).index(gt_idx)
    #         pred_idx = col_ind[row_i]
    #         pred_line = norm_pred_lines[pred_idx]
    #         edit = cost_matrix[gt_idx][pred_idx]
    #         # print('edit_dist', edit)
    #         # if edit > 0.7:
    #         #     print('! Not match')
    #     else:
    #         # print('No match pred')
    #         pred_idx = -1
    #         pred_line = ""
    #         edit = 1
            
    #     match_list.append({
    #         'gt_idx': gt_idx,
    #         'gt': gt_line,
    #         'pred_idx': pred_idx,
    #         'pred': pred_line,
    #         'edit': edit
    #     })
    #     print('-'*10)

    return converted_final_matches

def formula_format(formula_matches, img_name):
    formated_list = []
    for i, item in enumerate(formula_matches):
        formated_list.append({
            "gt": item["gt"],
            "pred": item["pred"],
            "img_id": img_name + '_' + str(i)
        })
    return formated_list

def match_gt2pred_textblock(gt_lines, pred_lines):
    text_inline_match_s = match_gt2pred(gt_lines, pred_lines, 'text')
    plain_text_match = []
    inline_formula_match = []
    for item in text_inline_match_s:
        plaintext_gt, inline_gt_list = inline_filter(item['gt'])  # 这个后续最好是直接从span里提取出来
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
                'pred_idx': item['pred_idx'],
                'pred': plaintext_pred,
                'edit': edit
            })

        if inline_gt_list:
            inline_formula_match_s = match_gt2pred(inline_gt_list, inline_pred_list, 'formula')
            inline_formula_match.extend(inline_formula_match_s)
            
    
    return plain_text_match, inline_formula_match

def merge_lists_with_sublists(main_list, sub_lists):
    # 返回包含merge的idx list，比如[0, 1, [2, 3], 4, [5, 6], 7, 8]
    main_list_final = list(copy.deepcopy(main_list))
    # 遍历子列表
    for sub_list in sub_lists:
        # 找到sub_list的开始idx
        pop_idx = main_list_final.index(sub_list[0])
        for _ in sub_list:  # pop的次数为subset的长度
            main_list_final.pop(pop_idx)
        main_list_final.insert(pop_idx, sub_list)  # 把subset插回去
    return main_list_final   

def sub_pred_fuzzy_matching(gt, pred):
    
    min_d = float('inf')
    pos = -1

    gt_len = len(gt)
    pred_len = len(pred)

    if gt_len >= pred_len and pred_len > 0:
        for i in range(gt_len - pred_len + 1):
            sub = gt[i:i + pred_len]
            dist = Levenshtein.distance(sub, pred)/pred_len
            if dist < min_d:
                min_d = dist
                pos = i

        return min_d
    else:
        return False
def sub_gt_fuzzy_matching(pred, gt):  
    
    min_d = float('inf')  
    pos = -1  
    matched_sub = ""  
  
    gt_len = len(gt)  
    pred_len = len(pred)  
  
    if pred_len >= gt_len and gt_len > 0:  
        for i in range(pred_len - gt_len + 1):  
            sub = pred[i:i + gt_len]  
            dist = Levenshtein.distance(sub, gt)  /gt_len
            if dist < min_d:  
                min_d = dist  
                pos = i  
                matched_sub = sub  # 保存匹配到的子串  
  
        # 返回最小距离、匹配的位置、gt的长度和匹配的字段  
        return min_d, pos, gt_len, matched_sub  
    else:  
        # 如果没有找到匹配，返回相应的信息  
        return 1, -1, gt_len, "" 
def get_final_subset(subset_certain, subset_certain_cost):
    if not subset_certain or not subset_certain_cost:
        return []  

    # 将子集和成本配对，并按子集的第一个元素排序
    subset_turple = sorted([(a, b) for a, b in zip(subset_certain, subset_certain_cost)], key=lambda x: x[0][0])

    # 初始化分组列表
    group_list = defaultdict(list)
    group_idx = 0
    group_list[group_idx].append(subset_turple[0])

    # 分组处理重叠的子集
    for item in subset_turple[1:]:
        overlap_flag = False
        for subset in group_list[group_idx]:
            for idx in item[0]:
                if idx in subset[0]:
                    overlap_flag = True
                    break
            if overlap_flag:
                break
        if overlap_flag:
            group_list[group_idx].append(item)
        else:
            group_idx += 1
            group_list[group_idx].append(item)

    final_subset = []
    for _, group in group_list.items():
        if len(group) == 1:  # 如果子集没有冲突则直接保留
            final_subset.append(group[0][0])
        else:
            # 如果有冲突，则找到所有的通路
            path_dict = defaultdict(list)
            path_idx = 0
            path_dict[path_idx].append(group[0])
            
            for subset in group[1:]:
                new_path = True
                for path_idx_s, path_items in path_dict.items():
                    is_dup = False
                    is_same = False
                    for path_item in path_items:
                        if path_item[0] == subset[0]:
                            is_dup = True
                            is_same = True
                            if path_item[1] > subset[1]:
                                path_dict[path_idx_s].pop(path_dict[path_idx_s].index(path_item))
                                path_dict[path_idx_s].append(subset)
                        else:
                            for num_1 in path_item[0]:
                                for num_2 in subset[0]:
                                    if num_1 == num_2:
                                        is_dup = True
                    if not is_dup:
                        path_dict[path_idx_s].append(subset)
                        new_path = False
                    if is_same:
                        new_path = False
                if new_path:
                    path_idx = len(path_dict.keys())
                    path_dict[path_idx].append(subset)

            # 保留下通路选项里成本平均值最小的一个
            saved_cost = float('inf')
            saved_subset = []  # 初始化 saved_subset 为空列表
            for path_idx, path in path_dict.items():
                avg_cost = sum([i[1] for i in path]) / len(path)
                if avg_cost < saved_cost:
                    saved_subset = [i[0] for i in path]
                    saved_cost = avg_cost

            final_subset.extend(saved_subset)

    return final_subset

def judge_pred_merge(gt_list, pred_list):
    
    threshold = 0.6
    merged_pred_flag = False
    continue_flag = False

    if len(pred_list) == 1:
        return merged_pred_flag, continue_flag
    
    cur_pred = ' '.join(pred_list[:-1])
    merged_pred = ' '.join(pred_list)
    cur_dist = Levenshtein.distance(gt_list[0], cur_pred)/max(len(gt_list[0]), len(cur_pred))
    merged_dist = Levenshtein.distance(gt_list[0], merged_pred)/max(len(gt_list[0]), len(merged_pred))
    if merged_dist > cur_dist:
        return merged_pred_flag, continue_flag
    
    else:
        for cur in pred_list[:-1]:
            cur_fuzzy_dist = sub_pred_fuzzy_matching(gt_list[0], cur_pred)
            # print('cur_fuzzy_dist:', cur_fuzzy_dist)
            if cur_fuzzy_dist is False:
                return merged_pred_flag, continue_flag
            if cur_fuzzy_dist > threshold:
                return merged_pred_flag, continue_flag
        
        add_fuzzy_dist = sub_pred_fuzzy_matching(gt_list[0], pred_list[-1])
        # print("add fuzzy dist:", add_fuzzy_dist)
        if add_fuzzy_dist is False:
            return merged_pred_flag, continue_flag
        if add_fuzzy_dist < threshold:
            merged_pred_flag = True
        if len(merged_pred) <= len(gt_list[0]):
            continue_flag = True
        
        return merged_pred_flag, continue_flag
    
def deal_with_truncated(cost_matrix, norm_gt_lines, norm_pred_lines):
    import numpy as np
    from Levenshtein import distance

    # 找到 cost_matrix 中小于阈值 0.25 的索引
    matched_first = np.argwhere(cost_matrix < 0.25)
    masked_gt_idx = [i[0] for i in matched_first]
    unmasked_gt_idx = [i for i in range(cost_matrix.shape[0]) if i not in masked_gt_idx]
    masked_pred_idx = [i[1] for i in matched_first]
    unmasked_pred_idx = [i for i in range(cost_matrix.shape[1]) if i not in masked_pred_idx]

    merges_gt_dict = {}
    merges_pred_dict = {}
    merged_gt_subsets = []

    for gt_idx in unmasked_gt_idx:
        check_merge_subset = []
        merged_dist = []

        for pred_idx in unmasked_pred_idx:  # 只考虑 pred 合并
            step = 1
            merged_pred = [norm_pred_lines[pred_idx]]

            while True:
                if pred_idx + step in masked_pred_idx or pred_idx + step >= len(norm_pred_lines):
                    break
                else:
                    merged_pred.append(norm_pred_lines[pred_idx + step])
                    merged_pred_flag, continue_flag = judge_pred_merge([norm_gt_lines[gt_idx]], merged_pred)  # 判断是否需要 trunc
                    if not merged_pred_flag:
                        break
                    else:
                        step += 1
                    if not continue_flag:
                        break

            check_merge_subset.append(list(range(pred_idx, pred_idx + step)))
            matched_line = ' '.join([norm_pred_lines[i] for i in range(pred_idx, pred_idx + step)])
            dist = distance(norm_gt_lines[gt_idx], matched_line) / max(len(matched_line), len(norm_gt_lines[gt_idx]))
            merged_dist.append(dist)

        # 如果 merged_dist 为空，则跳过当前 gt_idx 或设置一个高成本值
        if not merged_dist:
            subset_certain = []
            min_cost_idx = -1
            min_cost = float('inf')
        else:
            min_cost = min(merged_dist)
            min_cost_idx = merged_dist.index(min_cost)
            subset_certain = check_merge_subset[min_cost_idx]

        merges_gt_dict[gt_idx] = {
            'merge_subset': check_merge_subset,
            'merged_cost': merged_dist,
            'min_cost_idx': min_cost_idx,
            'subset_certain': subset_certain,
            'min_cost': min_cost
        }

    # 获取所有确定可以选出的 subset 和对应的 cost
    subset_certain = [merges_gt_dict[gt_idx]['subset_certain'] for gt_idx in unmasked_gt_idx if merges_gt_dict[gt_idx]['subset_certain']]
    subset_certain_cost = [merges_gt_dict[gt_idx]['min_cost'] for gt_idx in unmasked_gt_idx if merges_gt_dict[gt_idx]['subset_certain']]

    # 处理合并的子集
    subset_certain_final = get_final_subset(subset_certain, subset_certain_cost)

    if not subset_certain_final:   # 如果没有 merge 的话，就直接返回原来的内容
        return cost_matrix, norm_pred_lines, range(len(norm_pred_lines))

    final_pred_idx_list = merge_lists_with_sublists(range(len(norm_pred_lines)), subset_certain_final)
    final_norm_pred_lines = [' '.join(norm_pred_lines[idx_list[0]:idx_list[-1]+1]) if isinstance(idx_list, list) else norm_pred_lines[idx_list] for idx_list in final_pred_idx_list]

    new_cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, final_norm_pred_lines)

    return new_cost_matrix, final_norm_pred_lines, final_pred_idx_list
def cal_move_dist(gt, pred):
    # 计算阅读顺序移动距离
    assert len(gt) == len(pred), 'Not right length'
    step = 0
    for i, gt_c in enumerate(gt):
        if gt_c != pred[i]:
            step += abs(i - pred.index(gt_c))
            pred.pop(pred.index(gt_c))
            pred.insert(i, gt_c)
    return step / len(gt)

def cal_final_match(cost_matrix, norm_gt_lines, norm_pred_lines):
    min_indice = cost_matrix.argmax(axis=1)
    # if len(set(min_indice)) == len(min_indice): # 说明没有重复
    #     sorted_indice = sorted(min_indice)
    #     move_dist = cal_move_dist(sorted_indice, min_indice)  # 计算公式顺序移动距离
    #     if move_dist > 0.6:  # 设定一个公式顺序的编辑距离阈值，以免匹配得非常混乱的情况发生
    #         print('The matching order is a mess, please check.')
    #     else:
    #         return min_indice,
    # else:
        #print('Start merging')
    new_cost_matrix, final_norm_pred_lines, final_pred_idx_list = deal_with_truncated(cost_matrix, norm_gt_lines, norm_pred_lines) # deal_with_chunck
    row_ind, col_ind = linear_sum_assignment(new_cost_matrix)
    cost_list = []
    for r, c in zip(row_ind, col_ind):
        cost_list.append(new_cost_matrix[r][c])
    matched_col_idx = [final_pred_idx_list[i] for i in col_ind]
        # cost_list = [new_cost_matrix[i][col_ind[i]] for i in range(len(row_ind))]
    return matched_col_idx, row_ind, cost_list

def initialize_indices(norm_gt_lines, norm_pred_lines):
    gt_lens_dict = {idx: len(gt_line) for idx, gt_line in enumerate(norm_gt_lines)}
    pred_lens_dict = {idx: len(pred_line) for idx, pred_line in enumerate(norm_pred_lines)}
    return gt_lens_dict, pred_lens_dict

def process_matches(matched_col_idx, row_ind, cost_list, norm_gt_lines, norm_pred_lines, pred_lines):
    matches = {}
    unmatched_gt_indices = []
    unmatched_pred_indices = []

    for i in range(len(norm_gt_lines)):
        if i in row_ind:
            idx = list(row_ind).index(i)
            pred_idx = matched_col_idx[idx]

            if pred_idx is None or (isinstance(pred_idx, list) and None in pred_idx):
                unmatched_pred_indices.append(pred_idx)
                continue

            if isinstance(pred_idx, list):
                pred_line = ' | '.join(norm_pred_lines[pred_idx[0]:pred_idx[-1]+1])
                ori_pred_line = ' | '.join(pred_lines[pred_idx[0]:pred_idx[-1]+1])
                matched_pred_indices_range = list(range(pred_idx[0], pred_idx[-1]+1))
            else:
                pred_line = norm_pred_lines[pred_idx]
                ori_pred_line = pred_lines[pred_idx]
                matched_pred_indices_range = [pred_idx]

            edit = cost_list[idx]

            if edit > 0.7:
                unmatched_pred_indices.extend(matched_pred_indices_range)
                unmatched_gt_indices.append(i)
            else:
                matches[i] = {
                    'pred_indices': matched_pred_indices_range,
                    'edit_distance': edit,
                }
                for matched_pred_idx in matched_pred_indices_range:
                    if matched_pred_idx in unmatched_pred_indices:
                        unmatched_pred_indices.remove(matched_pred_idx)
        else:
            unmatched_gt_indices.append(i)

    return matches, unmatched_gt_indices, unmatched_pred_indices

def fuzzy_match_unmatched_items(unmatched_gt_indices, norm_gt_lines, norm_pred_lines):
    matching_dict = {}

    for pred_idx, pred_content in enumerate(norm_pred_lines):
        if isinstance(pred_idx, list):
            continue

        matching_indices = []

        for unmatched_gt_idx in unmatched_gt_indices:
            gt_content = norm_gt_lines[unmatched_gt_idx]
            cur_fuzzy_dist_unmatch, cur_pos, gt_lens, matched_field = sub_gt_fuzzy_matching(pred_content, gt_content)
            if cur_fuzzy_dist_unmatch < 0.3:
                matching_indices.append(unmatched_gt_idx)

        if matching_indices:
            matching_dict[pred_idx] = matching_indices

    return matching_dict

def merge_matches(matches, matching_dict):
    final_matches = {}

    for gt_idx, match_info in matches.items():
        pred_indices = match_info['pred_indices']
        edit_distance = match_info['edit_distance']

        pred_key = tuple(sorted(pred_indices))

        if pred_key in final_matches:
            final_matches[pred_key]['gt_indices'].append(gt_idx)
        else:
            final_matches[pred_key] = {
                'gt_indices': [gt_idx],
                'edit_distance': edit_distance
            }

    for pred_idx, gt_indices in matching_dict.items():
        pred_key = (pred_idx,) if not isinstance(pred_idx, (list, tuple)) else tuple(sorted(pred_idx))

        if pred_key in final_matches:
            final_matches[pred_key]['gt_indices'].extend(gt_indices)
        else:
            final_matches[pred_key] = {
                'gt_indices': gt_indices,
                'edit_distance': None
            }

    return final_matches

# def recalculate_edit_distances(final_matches, gt_lens_dict, norm_gt_lines, norm_pred_lines):
#     for pred_key, info in final_matches.items():
#         gt_indices = sorted(set(info['gt_indices']))

#         if len(gt_indices) > 1:
#             gt_lens = [gt_lens_dict[gt_idx] for gt_idx in gt_indices]
#             gt_content = [norm_gt_lines[gt_idx] for gt_idx in gt_indices]
#             pred_content = norm_pred_lines[pred_key[0]] if isinstance(pred_key[0], int) else None
#             total_length = sum(gt_lens)
#             segmented_pred_contents = [pred_content[i:i+gt_len] for i, gt_len in enumerate(gt_lens[:-1], start=0)]
#             segmented_pred_contents.append(pred_content[sum(gt_lens[:-1]):total_length])

#             recalculated_edit_distances = []
#             for segmented_pred, gt_idx in zip(segmented_pred_contents, gt_indices):
#                 edit_distance = Levenshtein.distance(segmented_pred, norm_gt_lines[gt_idx])  
#                 normalized_edit_distance = edit_distance / max(len(segmented_pred), len(norm_gt_lines[gt_idx]))
#                 recalculated_edit_distances.append(normalized_edit_distance)

#             info['edit_distance'] = sum(recalculated_edit_distances)
            
def recalculate_edit_distances(final_matches, gt_lens_dict, norm_gt_lines, norm_pred_lines):
    for pred_key, info in final_matches.items():
        gt_indices = sorted(set(info['gt_indices']))

        if len(gt_indices) > 1:
            # 合并所有的gt内容到一个字符串
            merged_gt_content = ''.join(norm_gt_lines[gt_idx] for gt_idx in gt_indices)
            # 获取预测的内容
            pred_content = norm_pred_lines[pred_key[0]] if isinstance(pred_key[0], int) else None

            # 计算合并后gt内容与预测内容之间的编辑距离
            edit_distance = Levenshtein.distance(merged_gt_content, pred_content)
            # 归一化编辑距离
            normalized_edit_distance = edit_distance / max(len(merged_gt_content), len(pred_content))

            # 更新信息中的编辑距离
            info['edit_distance'] = normalized_edit_distance
        else:
            # 如果只有一个gt索引，则保持原样
            gt_idx = gt_indices[0]
            pred_content = norm_pred_lines[pred_key[0]] if isinstance(pred_key[0], int) else None
            edit_distance = Levenshtein.distance(norm_gt_lines[gt_idx], pred_content)
            normalized_edit_distance = edit_distance / max(len(norm_gt_lines[gt_idx]), len(pred_content))
            info['edit_distance'] = normalized_edit_distance
            
def print_final_results(final_matches):
    print("Final Matches:")
    for pred_key, info in final_matches.items():
        pred_indices_str = ', '.join(map(str, pred_key))

        if len(info['gt_indices']) > 1 and len(pred_key) > 1:
            unique_gt_indices = sorted(set(info['gt_indices']))
            gt_indices_str = ', '.join(map(str, unique_gt_indices))
            print(f"Merged Prediction: [{pred_indices_str}] -> Unique GT Indices: {gt_indices_str}, Edit Distance: {info['edit_distance']} (Merged)")
        else:
            gt_indices_str = ', '.join(map(str, info['gt_indices']))
            print(f"Prediction: [{pred_indices_str}] -> GT Indices: {gt_indices_str}, Edit Distance: {info['edit_distance']}")
            
def convert_final_matches(final_matches, norm_gt_lines, norm_pred_lines):
    converted_results = []
    for pred_key, info in final_matches.items():
        # 获取预测的内容
        pred_content = norm_pred_lines[pred_key[0]] if isinstance(pred_key[0], int) else None
        
        # 对于每一个ground truth索引
        for gt_idx in sorted(set(info['gt_indices'])):
            # 创建一个新的条目
            result_entry = {
                'gt_idx': int(gt_idx),
                'gt': norm_gt_lines[gt_idx],
                'pred_idx': str(pred_key),
                'pred': pred_content,
                'edit': info['edit_distance']
            }
            # 添加到结果列表
            converted_results.append(result_entry)
    
    return converted_results

if __name__ == "__main__":
    file_name='merge_split_example.txt'
    with open(f"/mnt/petrelfs/zhujiawei/Projects/pdf_validation-add_fuzzy_match3/test_match/match_gt/{file_name}") as f:
        gts = f.readlines()
    with open(f"/mnt/petrelfs/zhujiawei/Projects/pdf_validation-add_fuzzy_match3/test_match/match_pred/{file_name}") as f:
        predications = f.readlines()
    norm_gt_lines = [normalized_formula(line) for line in gts]  
    norm_pred_lines = [normalized_formula(line) for line in predications]  
    cost_matrix = compute_edit_distance_matrix_new(norm_gt_lines, norm_pred_lines)
    
    matched_col_idx, row_ind, cost_list = cal_final_match(cost_matrix, norm_gt_lines, norm_pred_lines)  
    #print('cost_matrix',cost_matrix)
    gt_lens_dict, pred_lens_dict = initialize_indices(norm_gt_lines, norm_pred_lines)
    matches, unmatched_gt_indices, unmatched_pred_indices = process_matches(
        matched_col_idx, row_ind, cost_list, norm_gt_lines, norm_pred_lines, predications)
    matching_dict = fuzzy_match_unmatched_items(unmatched_gt_indices, norm_gt_lines, norm_pred_lines)
    final_matches = merge_matches(matches, matching_dict)
    recalculate_edit_distances(final_matches, gt_lens_dict, norm_gt_lines, norm_pred_lines)
    
    # print_final_results(final_matches)
    converted_final_matches = convert_final_matches(final_matches, norm_gt_lines, norm_pred_lines)
    # for entry in converted_final_matches:
    #     print(entry)