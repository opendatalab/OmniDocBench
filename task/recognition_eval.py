from tabulate import tabulate
from registry.registry import EVAL_TASK_REGISTRY
from registry.registry import METRIC_REGISTRY

@EVAL_TASK_REGISTRY.register("recogition_eval")
class RecognitionBaseEval():
    def __init__(self, dataset, metrics_list):
        p_scores = {}
        for metric in metrics_list:
            metric_val = METRIC_REGISTRY.get(metric)
            result = metric_val(dataset).evaluate()
            if result:
                p_scores.update(result) 
        score_table = [[k,v] for k,v in p_scores.items()]
        print(tabulate(score_table))
        print('='*100)


    