from mmeval import COCODetection
import json
import os
import numpy as np
from registry.registry import DATASET_REGISTRY
from collections import defaultdict
from utils.ocr_utils import poly2bbox
import pdb

@DATASET_REGISTRY.register("detection_dataset")
class DetectionDataset():
    def __init__(self, cfg_task):
        gt_path = cfg_task['dataset']['ground_truth']['data_path']
        pred_path = cfg_task['dataset']['prediction']['data_path']
        label_classes_level = cfg_task['categories'].get('eval_cat', {})
        label_classes = sum(list(label_classes_level.values()), [])
        gt_cat_mapping = cfg_task['categories']['gt_cat_mapping']
        pred_cat_mapping = cfg_task['categories']['pred_cat_mapping']
        filtered_types = cfg_task['dataset'].get('filter')
        
        gts, img_list = self.get_gts_and_img_list(filtered_types, gt_path, label_classes, label_classes_level, gt_cat_mapping)

        preds = self.get_preds(img_list, pred_path, label_classes, label_classes_level, pred_cat_mapping)

        self.samples = {
            'gts': gts,
            'preds': preds
        }
        # print(self.samples)
        
        meta={'CLASSES':tuple(label_classes)}
        self.coco_det_metric = COCODetection(dataset_meta=meta, metric=['bbox'], classwise=True)

    def get_gts_and_img_list(self, filtered_types, gt_path, label_classes, label_classes_level, gt_cat_mapping):
        with open(os.path.join(gt_path), 'r') as f:
            gt_samples = json.load(f)
        basename = os.path.basename(gt_path)[:-5]

        img_list = []
        filtered_gt_samples = []
        if filtered_types:
            for gt_sample in gt_samples:
                select_flag = True
                page_num = gt_sample['page_info']['page_no']
                if gt_sample['page_info'].get('image_path'):
                    sample_name = gt_sample['page_info']['image_path']
                else:
                    sample_name = f'{basename}_{page_num}'
                for k, v in filtered_types.items():
                    if gt_sample["page_info"]["page_attribute"][k] != v:
                        select_flag = False
                if select_flag:
                    filtered_gt_samples.append(gt_sample)
                    img_list.append(sample_name)
        else:
            filtered_gt_samples = gt_samples
            img_list = [gt_sample["page_info"]['image_path'] for gt_sample in gt_samples]

        gts = self.reform_gt(filtered_gt_samples, label_classes, label_classes_level, gt_cat_mapping)

        return gts, img_list
    
    def get_omni_annos(self, sample, cat_mapping, label_classes, label_classes_level):
        bboxes = []
        labels = []
        scores = []
        for item in sample['layout_dets']:
            if cat_mapping.get(item['category_type']):
                class_name = cat_mapping[item['category_type']]
            else:
                class_name = item['category_type']

            if class_name in label_classes_level.get('block_level'):
                bbox = poly2bbox(item['poly'])
                bboxes.append(bbox)
                labels.append(label_classes.index(class_name))
                if item.get('score'):
                    scores.append(item['score'])
                else:
                    scores.append(1)

            for span in item.get('line_with_spans', []):
                if cat_mapping.get(span['category_type']):
                    class_name = cat_mapping[span['category_type']]
                else:
                    class_name = span['category_type']

                if class_name in label_classes_level.get('span_level'):
                    bbox = poly2bbox(span['poly'])
                    bboxes.append(bbox)
                    labels.append(label_classes.index(class_name))
                    if span.get('score'):
                        scores.append(span['score'])
                    else:
                        scores.append(1)
        return bboxes, labels, scores

    def reform_gt(self, filtered_gt_samples, label_classes, label_classes_level, gt_cat_mapping): 
        gts = []

        for idx, sample in enumerate(filtered_gt_samples):            
            bboxes, labels, scores = self.get_omni_annos(sample, gt_cat_mapping, label_classes, label_classes_level)
            gts.append({
                'img_id': idx,
                'width': sample['page_info']['width'],
                'height': sample['page_info']['height'],
                'bboxes': np.array(bboxes),
                'labels': np.array(labels),
                'ignore_flags': [False]*len(labels),
            })
        return gts

    def get_preds(self, img_list, pred_path, label_classes, label_classes_level, pred_cat_mapping):
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
        
        preds = self.reform_pred(pred_dict, img_list, label_classes, label_classes_level, pred_cat_mapping)
                
        return preds
    
    def reform_pred(self, pred_dict, img_list, label_classes, label_classes_level, pred_cat_mapping): 
        preds = []

        for idx, sample_name in enumerate(img_list):
            sample = pred_dict.get(sample_name)
            if not sample:
                print(f'No matching prediction for {sample_name}. The prediction wiil be empty.')
                preds.append({
                    'img_id': idx,
                    'bboxes': np.array([]),
                    'scores': np.array([]),
                    'labels': np.array([]),
                })
                continue
            
            bboxes, labels, scores = self.get_omni_annos(sample, pred_cat_mapping, label_classes, label_classes_level)
        
            preds.append({
                'img_id': idx,
                'bboxes': np.array(bboxes),
                'scores': np.array(scores),
                'labels': np.array(labels),
            })
        return preds
    
@DATASET_REGISTRY.register("detection_dataset_simple_format")
class DetectionDatasetSimpleFormat(DetectionDataset):
    def get_preds(self, img_list, pred_path, label_classes, label_classes_level, pred_cat_mapping):
        pred_dict = defaultdict(list)

        with open(os.path.join(pred_path), 'r') as f:
            preds_sample = json.load(f)

        for pred in preds_sample['results']:
            pred_dict[pred["image_name"]+'.jpg'].append(pred)

        pred_name2cat = {name: int(cat) for cat, name in preds_sample["categories"].items()}
        pred_cat_mapping = {pred_name2cat[cat]:name for cat, name in pred_cat_mapping.items()}
        
        preds = self.reform_pred(pred_dict, img_list, label_classes, label_classes_level, pred_cat_mapping)
                
        return preds
    
    def reform_pred(self, pred_dict, img_list, label_classes, label_classes_level, pred_cat_mapping): 
        preds = []
        for idx, sample_name in enumerate(img_list):
            sample = pred_dict.get(sample_name)
            if not sample:
                print(f'No matching prediction for {sample_name}. The prediction wiil be empty.')
                preds.append({
                    'img_id': idx,
                    'bboxes': np.array([]),
                    'scores': np.array([]),
                    'labels': np.array([]),
                })
                continue
            
            pred_bboxes = []
            pred_labels = []
            scores = []
            for item in sample:
                if pred_cat_mapping.get(item["category_id"]):
                    class_name = pred_cat_mapping[item["category_id"]]
                else:
                    class_name = item["category_id"]

                if class_name in label_classes:
                    pred_bboxes.append(item['bbox'])
                    pred_labels.append(label_classes.index(class_name))
                    scores.append(item['score'])
                           
            preds.append({
                'img_id': idx,
                'bboxes': np.array(pred_bboxes),
                'scores': np.array(scores),
                'labels': np.array(pred_labels),
            })
        return preds