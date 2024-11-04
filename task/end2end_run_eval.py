# from modules.cal_matrix import cal_text_matrix, cal_table_teds
from registry.registry import EVAL_TASK_REGISTRY
from metrics.result_show import show_result, get_full_labels_results
from registry.registry import METRIC_REGISTRY
# import json   fe


@EVAL_TASK_REGISTRY.register("end2end_eval")
class End2EndEval():
    def __init__(self, dataset, metrics_list):
        for element in metrics_list.keys():
            result = {}
            group_info = metrics_list[element].get('group', [])
            samples = dataset.samples[element]
            for metric in metrics_list[element]['metric']:
                metric_val = METRIC_REGISTRY.get(metric)
                samples, result_s = metric_val(samples).evaluate(group_info)
                if result_s:
                    result.update(result_s)
            if result:
                print(f'【{element}】')
                show_result(result)
            
            get_full_labels_results(samples)
            # with open(f'./result/{element}_result.json', 'w', encoding='utf-8') as f:
            #     json.dump(samples, f, )
    