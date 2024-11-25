from tabulate import tabulate
from registry.registry import EVAL_TASK_REGISTRY
from registry.registry import METRIC_REGISTRY
import os
import json
from metrics.show_result import show_result, get_full_labels_results, get_page_split

@EVAL_TASK_REGISTRY.register("recogition_eval")
class RecognitionBaseEval():
    def __init__(self, dataset, metrics_list, page_info_path, save_name, **kwargs):
        p_scores = {}
        samples = dataset.samples

        page_info = {}
        if os.path.isdir(page_info_path):
            md_flag = True
        else:
            md_flag = False

        no_page_flag = False
        if not md_flag:
            with open(page_info_path, 'r') as f:
                pages = json.load(f)
            
            for page in pages:
                if 'page_info' not in page:
                    no_page_flag = True
                    break
                img_path = os.path.basename(page['page_info']['image_path'])
                page_info[img_path] = page['page_info']['page_attribute']

        for metric in metrics_list:
            metric_val = METRIC_REGISTRY.get(metric)
            samples, result = metric_val(samples).evaluate({}, save_name)
            if result:
                p_scores.update(result) 
        # score_table = [[k,v] for k,v in p_scores.items()]
        show_result(p_scores)
        # print(tabulate(score_table))
        # print('='*100)

        if md_flag:
            group_result =  {}
            page_result = {}
        else:
            group_result = get_full_labels_results(samples)
            if no_page_flag:
                page_result = {}
            else:
                page_result = get_page_split(samples, page_info)

        result_all = {
            'all': p_scores,
            'group':  group_result,
            'page': page_result
        }

        with open(f'./result/{save_name}_metric_result.json', 'w', encoding='utf-8') as f:
            json.dump(result_all, f, indent=4, ensure_ascii=False)


    