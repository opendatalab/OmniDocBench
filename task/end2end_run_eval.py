# from modules.cal_matrix import cal_text_matrix, cal_table_teds
from registry.registry import EVAL_TASK_REGISTRY
from tabulate import tabulate
from registry.registry import METRIC_REGISTRY   


@EVAL_TASK_REGISTRY.register("end2end_eval")
class End2EndEval():
    def __init__(self, dataset, metrics_list):
        for element in metrics_list.keys():
            result = {}
            for metric in metrics_list[element]:
                metric_val = METRIC_REGISTRY.get(metric)
                result_s = metric_val.evaluate(dataset.samples[element])
                if result_s:
                    result.update(result_s)
            if result:
                print(f'【{element}】')
                self.show_result(result)

    def show_result(self, results):
        score_table = [[k,v] for k,v in results.items()]
        print(tabulate(score_table))
        print('='*100)