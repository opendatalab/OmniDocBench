from mmeval import COCODetection
import json
import os
import numpy as np
from registry.registry import DATASET_REGISTRY

@DATASET_REGISTRY.register("detection_dataset")
class DetectionDataset():
    def __init__(self, cfg_task):
        gt_path = cfg_task['dataset']['ground_truth']['data_path']
        pred_path = cfg_task['dataset']['prediction']['data_path']
        label_classes = cfg_task['categories']['eval_cat']
        gt_cat_mapping = cfg_task['categories']['gt_cat_mapping']
        pred_cat_mapping = cfg_task['categories']['pred_cat_mapping']
        labels = []
        det_res = []
        pred_dict = {}

        with open(os.path.join(pred_path), 'r') as f:
            preds_sample = json.load(f)
        basename = os.path.basename(pred_path)[:-5]
        for pred in preds_sample:
            page_num = pred['page_info']['page_no']
            if pred['page_info'].get('image_path'):
                pred_dict[pred['page_info']['image_path']] = pred
            else:
                pred_dict[f'{basename}_{page_num}'] = pred
        
        
        with open(os.path.join(gt_path), 'r') as f:
            gt_sample = json.load(f)
        basename = os.path.basename(gt_path)[:-5]
        for gt in gt_sample:
            page_num = gt['page_info']['page_no']
            if gt['page_info'].get('image_path'):
                sample_name = gt['page_info']['image_path']
            else:
                sample_name = f'{basename}_{page_num}'
            if pred_dict.get(sample_name):
                det_res.append(pred_dict[sample_name])
                labels.append(gt)
            else:
                print(f'No matching prediction for {sample_name}.')

        gts, preds = self.reformat_gt_and_pred(labels, det_res, label_classes, gt_cat_mapping, pred_cat_mapping)
        self.samples = {
            'gts': gts,
            'preds': preds
        }
        print(self.samples)
        meta={'CLASSES':tuple(label_classes)}
        self.coco_det_metric = COCODetection(dataset_meta=meta, metric=['bbox'], classwise=True)

        
    def reformat_gt_and_pred(self, labels, det_res, label_classes, gt_cat_mapping, pred_cat_mapping):
        preds = []
        gts = []
        
        for idx, (ann, pred) in enumerate(zip(labels, det_res)):
            gt_bboxes = []
            gt_labels = []
            for item in ann['layout_dets']:
                if gt_cat_mapping.get(item['category_type']):
                    class_name = gt_cat_mapping[item['category_type']]
                else:
                    class_name = item['category_type']

                if class_name in label_classes:
                    L = item['poly'][0]
                    U = item['poly'][1]
                    R = item['poly'][4]
                    D = item['poly'][5]
                    L, R = min(L, R), max(L, R)
                    U, D = min(U, D), max(U, D)
                    gt_bboxes.append([L, U, R, D])
                    gt_labels.append(label_classes.index(class_name))
            
            gts.append({
                'img_id': idx,
                'width': ann['page_info']['width'],
                'height': ann['page_info']['height'],
                'bboxes': np.array(gt_bboxes),
                'labels': np.array(gt_labels),
                'ignore_flags': [False]*len(gt_labels),
            })
            
            bboxes = []
            labels = []
            scores = []

            for item in pred['layout_dets']:
                if pred_cat_mapping.get(item['category_type']):
                    class_name = pred_cat_mapping[item['category_type']]
                else:
                    class_name = item['category_type']

                if class_name in label_classes:
                    L = item['poly'][0]
                    U = item['poly'][1]
                    R = item['poly'][4]
                    D = item['poly'][5]
                    L, R = min(L, R), max(L, R)
                    U, D = min(U, D), max(U, D)
                    bboxes.append([L, U, R, D])
                    labels.append(label_classes.index(class_name))
                    scores.append(item['score'])
            
            preds.append({
                'img_id': idx,
                'bboxes': np.array(bboxes),
                'scores': np.array(scores),
                'labels': np.array(labels),
            })
        
        return gts, preds