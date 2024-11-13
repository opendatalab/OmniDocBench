from collections import defaultdict
from tabulate import tabulate

def show_result(results):
    for metric_name in results.keys():
        print(f'{metric_name}:')
        score_table = [[k,v] for k,v in results[metric_name].items()]
        print(tabulate(score_table))
        print('='*100)

def sort_nested_dict(d):
    # 如果是字典，则递归排序
    if isinstance(d, dict):
        # 对当前字典进行排序
        sorted_dict = {k: sort_nested_dict(v) for k, v in sorted(d.items())}
        return sorted_dict
    # 如果不是字典，直接返回
    return d

def get_full_labels_results(samples):
    if not samples:
        return {}
    label_group_dict = defaultdict(lambda: defaultdict(list))
    for sample in samples:
        label_list = []
        if not sample.get("gt_attribute"):
            continue
        for anno in sample["gt_attribute"]:
            for k,v in anno.items():
                label_list.append(k+": "+str(v))
        for label_name in list(set(label_list)):  # 目前如果有合并的情况的话，按合并后涉及到的所有label的set来算
            for metric, score in sample['metric'].items():
                label_group_dict[label_name][metric].append(score)

    print('----Anno Attribute---------------')
    result = {}
    result['sample_count'] = {}
    for attribute in label_group_dict.keys():
        for metric, scores in label_group_dict[attribute].items():
            mean_score = sum(scores) / len(scores)
            if not result.get(metric):
                result[metric] = {}
            result[metric][attribute] = mean_score
            result['sample_count'][attribute] = len(scores)
    result = sort_nested_dict(result)
    show_result(result)
    return result

def get_page_split(samples, page_info):
    if not page_info:
        return {}
    page_split_dict = defaultdict(lambda: defaultdict(list)) 
    for sample in samples:
        img_name = sample['img_id'] if sample['img_id'].endswith('.jpg') else '_'.join(sample['img_id'].split('_')[:-1])
        page_info_s = page_info[img_name]
        if not sample.get('metric'):
            continue
        for metric, score in sample['metric'].items():
            for k,v in page_info_s.items():
                if isinstance(v, list): # special issue
                    for special_issue in v:
                        if 'table' not in special_issue:  # Table相关的特殊字段有重复
                            page_split_dict[metric][special_issue].append(score)
                else:
                    page_split_dict[metric][k+": "+str(v)].append(score)
    
    print('----Page Attribute---------------')
    result = {}
    result['sample_count'] = {}
    for metric in page_split_dict.keys():
        for attribute, scores in page_split_dict[metric].items():
            mean_score = sum(scores) / len(scores)
            if not result.get(metric):
                result[metric] = {}
            result[metric][attribute] = mean_score
            result['sample_count'][attribute] = len(scores)
    result = sort_nested_dict(result)
    show_result(result)
    return result