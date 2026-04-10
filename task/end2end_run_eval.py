# from modules.cal_matrix import cal_text_matrix, cal_table_teds
from registry.registry import EVAL_TASK_REGISTRY
from metrics.show_result import show_result, get_full_labels_results, get_page_split
from registry.registry import METRIC_REGISTRY
import json
import os
import pdb

@EVAL_TASK_REGISTRY.register("end2end_eval")
class End2EndEval():
    def __init__(self, dataset, metrics_list, page_info_path, save_name):
        result_all = {}
        page_info = {}
        if os.path.isdir(page_info_path):
            md_flag = True
        else:
            md_flag = False
        if not md_flag:
            with open(page_info_path, 'r') as f:
                pages = json.load(f)
            
            for page in pages:
                img_path = os.path.basename(page['page_info']['image_path'])
                page_info[img_path[:-4]] = page['page_info']['page_attribute']

        for element in metrics_list.keys():
            result = {}
            group_info = metrics_list[element].get('group', [])
            samples = dataset.samples[element]
            for metric in metrics_list[element]['metric']:
                metric_val = METRIC_REGISTRY.get(metric)
                samples, result_s = metric_val(samples).evaluate(group_info, f"{save_name}_{element}")
                if result_s:
                    result.update(result_s)
            if result:
                print(f'【{element}】')
                show_result(result)
            result_all[element] = {}
            
            if md_flag:
                group_result =  {}
                page_result = {}
            else:
                group_result = get_full_labels_results(samples)
                page_result = get_page_split(samples, page_info)
            result_all[element] = {
                'all': result,
                'group':  group_result,
                'page': page_result}
            # pdb.set_trace()

            if not os.path.exists('./result'):
                os.makedirs('./result')
            if isinstance(samples, list):
                saved_samples = samples
            else:
                saved_samples = samples.samples
            try:

                with open(f'./result/{save_name}_{element}_result.json', 'w', encoding='utf-8') as f:
                    json.dump(saved_samples, f, indent=4, ensure_ascii=False)
            except TypeError as e:
                print(f"JSON 序列化错误: {e}")
                print("请检查 saved_samples 中是否包含非 JSON 可序列化的数据类型")
                
                # 打印出有问题的数据类型
                def find_non_serializable(data):
                    if isinstance(data, dict):
                        for k, v in data.items():
                            try:
                                json.dumps(v)
                            except TypeError:
                                print(f"键 '{k}' 包含不可序列化的值: {v} (类型: {type(v)})")
                                find_non_serializable(v)
                    elif isinstance(data, (list, tuple)):
                        for i, item in enumerate(data):
                            try:
                                json.dumps(item)
                            except TypeError:
                                print(f"索引 {i} 包含不可序列化的项: {item} (类型: {type(item)})")
                                find_non_serializable(item)
                
                find_non_serializable(saved_samples)


        with open(f'./result/{save_name}_metric_result.json', 'w', encoding='utf-8') as f:
            json.dump(result_all, f, indent=4, ensure_ascii=False)
    