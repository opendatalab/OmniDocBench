from metrics.cal_metric import *
import os
import yaml
import io
from metrics.result_show import show_result, get_full_labels_results, get_page_split
import sys

page_info_path = '/mnt/petrelfs/ouyanglinke/CDM_match/benchmark/middle/ocr-main-1114_change_type.json' # 到时候改成对的
config_path = '/mnt/petrelfs/ouyanglinke/DocParseEval/configs/end2end_1.yaml'

with io.open(os.path.abspath(config_path), "r", encoding="utf-8") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

# save_name = 'mathpix1108_quick_match'
save_name = sys.argv[1] + '_quick_match'

for task in cfg.keys():
    if not cfg.get(task):
        print('No config for task {task}')

    metrics_list = cfg[task]['metrics']  # 在task里再实例化
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
            page_info[img_path] = page['page_info']['page_attribute']

    for element in metrics_list.keys():
        result = {}
        group_info = metrics_list[element].get('group', [])
        with open(f'/mnt/petrelfs/ouyanglinke/DocParseEval/result_1115_2/{save_name}_{element}_result.json', 'r') as f:
            samples = json.load(f)
        for metric in metrics_list[element]['metric']:
            metric_val = METRIC_REGISTRY.get(metric)
            samples, result_s = metric_val(samples).evaluate(group_info)
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

        # if not os.path.exists('./result'):
        #     os.makedirs('./result')
        # if isinstance(samples, list):
        #     saved_samples = samples
        # else:
        #     saved_samples = samples.samples
        # with open(f'./result/{save_name}_{element}_result.json', 'w', encoding='utf-8') as f:
        #     json.dump(saved_samples, f, indent=4, ensure_ascii=False)

    with open(f'/mnt/petrelfs/ouyanglinke/DocParseEval/result_change_type/{save_name}_metric_result.json', 'w', encoding='utf-8') as f:
        json.dump(result_all, f, indent=4, ensure_ascii=False)