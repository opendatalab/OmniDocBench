# coding: utf-8
from registry.registry import EVAL_TASK_REGISTRY

@EVAL_TASK_REGISTRY.register("detection_eval")
class DetectionEval():
    def __init__(self, dataset, metrics_list='COCODet', page_info_path='', save_name=''):
        detect_matrix = dataset.coco_det_metric(predictions=dataset.samples['preds'], groundtruths=dataset.samples['gts'])
        print('detect_matrix', detect_matrix)
