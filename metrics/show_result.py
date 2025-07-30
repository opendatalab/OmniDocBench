from collections import defaultdict
from tabulate import tabulate
import pandas as pd
import pdb
import numpy as np

def show_result(results):
    for metric_name in results.keys():
        print(f'{metric_name}:')
        score_table = [[k,v] for k,v in results[metric_name].items()]
        print(tabulate(score_table))
        print('='*100)

def show_result_table(result):
    save_dict = {}
    en_overall = []
    ch_overall = []
    use_show_result = False
    # print(result)
    print('【Overall】')
    for category_type, metric in [("text_block", "Edit_dist"), ("display_formula", "Edit_dist"), ("display_formula", "CDM"), ("table", "TEDS"), ("table", "Edit_dist"), ("reading_order", "Edit_dist")]:
        if not result.get(category_type):
            continue
        if not result[category_type].get("page"):
            use_show_result = True
            continue
        if metric == "TEDS":
            scale = 100
        else:
            scale = 1
        try:
            save_dict[category_type+'_'+metric+'_EN'] = result[category_type]["page"][metric].get("language: english", np.nan) * scale
        except:
            print(f'{category_type} {metric} is not found')
            save_dict[category_type+'_'+metric+'_EN'] = '-'
        try:
            save_dict[category_type+'_'+metric+'_CH'] = result[category_type]["page"][metric].get("language: simplified_chinese",np.nan) * scale
        except:
            print(f'{category_type} {metric} is not found')
            save_dict[category_type+'_'+metric+'_CH'] = '-'
        
        if metric == "Edit_dist":
            en_overall.append(result[category_type]["page"][metric].get("language: english", np.nan))
            ch_overall.append(result[category_type]["page"][metric].get("language: simplified_chinese",np.nan))
    
    if use_show_result:
        show_result(result)
        return 'Finished'

    save_dict['overall_EN'] = sum(en_overall) / len(en_overall)
    save_dict['overall_CH'] = sum(ch_overall) / len(ch_overall)
    
    # df = pd.DataFrame([save_dict], index=['current']).round(3)
    # print(df)
    score_table = [[k,v] for k,v in save_dict.items()]
    print(tabulate(score_table))
    print('\n')

    print('【PDF types】')
    pdf_types_result = result['text_block']["page"]["Edit_dist"]
    types_sorted = ["data_source: book", "data_source: PPT2PDF", "data_source: research_report", "data_source: colorful_textbook", "data_source: exam_paper", "data_source: magazine", "data_source: academic_literature", "data_source: note", "data_source: newspaper", "ALL"]
    score_table = [[k, pdf_types_result.get(k, np.nan)] for k in types_sorted]
    print(tabulate(score_table))
    print('\n')

    print('【Layout】')
    layout_result_mean = result['reading_order']["page"]["Edit_dist"]
    layout_result_var = result['text_block']["page"]["Edit_dist_var"]
    layout_types = ["layout: single_column", "layout: double_column", "layout: three_column", "layout: other_layout"]
    score_table = [[k, layout_result_mean.get(k, np.nan), layout_result_var.get(k, np.nan)] for k in layout_types]
    print(tabulate(score_table, headers=['Layout', 'Mean', 'Var']))
    print('\n')

    print('【Text Attribute】')
    try:
        text_attribute_result = result['text_block']["group"]["Edit_dist"]
        text_attribute_types = ["text_language: text_english", "text_language: text_simplified_chinese", "text_language: text_en_ch_mixed", "text_background: white", "text_background: single_colored", "text_background: multi_colored"]
        score_table = [[k, text_attribute_result.get(k, np.nan)] for k in text_attribute_types]
        print(tabulate(score_table))
        print('\n')
    except:
        print('Text Attribute is not found')
        text_attribute_result = {}
    

    print('【Table Attribute】')
    try:
        table_attribute_result = result['table']["group"]["TEDS"]
        table_attribute_types = ["language: table_en", "language: table_simplified_chinese", "language: table_en_ch_mixed", "line: full_line", "line: less_line", "line: fewer_line", "line: wireless_line", 
                            "with_span: True", "with_span: False", "include_equation: True", "include_equation: False", "include_background: True", "include_background: False", "table_layout: vertical", "table_layout: horizontal"]
        score_table = [[k, table_attribute_result.get(k, np.nan)] for k in table_attribute_types]
        print(tabulate(score_table))
        print('\n')
    except:
        print('Table Attribute is not found')
        table_attribute_result = {}
    return 'Finished'

def sort_nested_dict(d):
    # If it's a dictionary, recursively sort it
    if isinstance(d, dict):
        # Sort the current dictionary
        sorted_dict = {k: sort_nested_dict(v) for k, v in sorted(d.items())}
        return sorted_dict
    # If not a dictionary, return directly
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
        for label_name in list(set(label_list)):  # Currently if there are merged cases, calculate based on the set of all labels involved after merging
            for metric, score in sample['metric'].items():
                label_group_dict[label_name][metric].append(score)

    # print('----Anno Attribute---------------')
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
    # show_result(result)
    return result

# def get_page_split(samples, page_info):    # Sample level metric
#     if not page_info:
#         return {}
#     page_split_dict = defaultdict(lambda: defaultdict(list)) 
#     for sample in samples:
#         img_name = sample['img_id'] if sample['img_id'].endswith('.jpg') else '_'.join(sample['img_id'].split('_')[:-1])
#         page_info_s = page_info[img_name]
#         if not sample.get('metric'):
#             continue
#         for metric, score in sample['metric'].items():
#             for k,v in page_info_s.items():
#                 if isinstance(v, list): # special issue
#                     for special_issue in v:
#                         if 'table' not in special_issue:  # Table-related special fields have duplicates
#                             page_split_dict[metric][special_issue].append(score)
#                 else:
#                     page_split_dict[metric][k+": "+str(v)].append(score)
    
#     print('----Page Attribute---------------')
#     result = {}
#     result['sample_count'] = {}
#     for metric in page_split_dict.keys():
#         for attribute, scores in page_split_dict[metric].items():
#             mean_score = sum(scores) / len(scores)
#             if not result.get(metric):
#                 result[metric] = {}
#             result[metric][attribute] = mean_score
#             result['sample_count'][attribute] = len(scores)
#     result = sort_nested_dict(result)
#     show_result(result)
#     return result

def get_page_split(samples, page_info):   # Page level metric
    if not page_info:
        return {}
    result_list = defaultdict(list)
    for sample in samples:
        img_name = sample['img_id'] if sample['img_id'].endswith('.jpg') else '_'.join(sample['img_id'].split('_')[:-1])
        page_info_s = page_info[img_name]
        if not sample.get('metric'):
            continue
        for metric, score in sample['metric'].items():
            gt = sample['norm_gt'] if sample.get('norm_gt') else sample['gt']
            pred = sample['norm_pred'] if sample.get('norm_pred') else sample['pred']
            result_list[metric].append({
                'image_name': img_name,
                'metric': metric,
                'attribute': 'ALL',
                'score': score,
                'upper_len': max(len(gt), len(pred))
            })
            for k,v in page_info_s.items():
                if isinstance(v, list): # special issue
                    for special_issue in v:
                        if 'table' not in special_issue:  # Table-related special fields have duplicates
                            result_list[metric].append({
                                'image_name': img_name,
                                'metric': metric,
                                'attribute': special_issue,
                                'score': score,
                                'upper_len': max(len(gt), len(pred))
                            })
                else:
                    result_list[metric].append({
                        'image_name': img_name,
                        'metric': metric,
                        'attribute': k+": "+str(v),
                        'score': score,
                        'upper_len': max(len(gt), len(pred))
                    })
    
    # Page level logic, accumulation is only done within pages, and mean operation is performed between pages
    result = {}
    if result_list.get('Edit_dist'):
        df = pd.DataFrame(result_list['Edit_dist'])
        up_total_avg = df.groupby(["image_name", "attribute"]).apply(lambda x: (x["score"]*x['upper_len']).sum() / x['upper_len'].sum()).groupby('attribute').mean()  # At page level, accumulate edits, denominator is sum of max(gt, pred) from each sample
        up_total_var = df.groupby(["image_name", "attribute"]).apply(lambda x: (x["score"]*x['upper_len']).sum() / x['upper_len'].sum()).groupby('attribute').var()  # At page level, accumulate edits, denominator is sum of max(gt, pred) from each sample
        result['Edit_dist'] = up_total_avg.to_dict()
        result['Edit_dist_var'] = up_total_var.to_dict()
    for metric in result_list.keys():
        if metric == 'Edit_dist':
            continue
        df = pd.DataFrame(result_list[metric])
        page_avg = df.groupby(["image_name", "attribute"]).apply(lambda x: x["score"].mean()).groupby('attribute').mean()
        result[metric] = page_avg.to_dict()

    result = sort_nested_dict(result)
    # print('----Page Attribute---------------')
    # show_result(result)
    return result