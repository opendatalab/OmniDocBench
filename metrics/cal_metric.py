# import evaluate
# import random
import json
import time
# from rapidfuzz.distance import Levenshtein
import Levenshtein
from .table_metric import TEDS
import evaluate
import random
from utils.read_files import save_paired_result
from registry.registry import METRIC_REGISTRY
from collections import defaultdict
import pdb
import copy

def get_groups(samples, group_info):
    group_samples = defaultdict(list)
    for sample in samples:
        group_samples['all'].append(sample)
        for group in group_info:
            select_flag = True
            for k, v in group.items():
                for gt_attribute in sample['gt_attribute']:   # gt_attribute是一个list，截断合并的gt都在里面
                    if not gt_attribute:   # 如果没有GT属性，也不纳入计算
                        select_flag = False
                    elif gt_attribute[k] != v:  # 只要其中有一个gt的属性不符合标准，则不选中        
                        select_flag = False
            if select_flag:
                group_samples[str(group)].append(sample)
    return group_samples


@METRIC_REGISTRY.register("TEDS")
class call_TEDS():
    def __init__(self, samples):
        self.samples = samples
    def evaluate(self, group_info=[]):
        teds = TEDS(structure_only=False)
        teds_structure_only = TEDS(structure_only=True)
        group_scores = defaultdict(list)
        group_scores_structure_only = defaultdict(list)
        samples = self.samples
        for sample in samples:
            score = teds.evaluate(sample['pred'], sample['gt'])
            score_structure_only = teds_structure_only.evaluate(sample['pred'], sample['gt'])
            # print('TEDS score:', score)
            group_scores['all'].append(score)
            group_scores_structure_only['all'].append(score_structure_only)
            if not sample.get('metric'):
                sample['metric'] = {}
            sample['metric']['TEDS'] = score
            sample['metric']['TEDS_structure_only'] = score_structure_only
            for group in group_info:
                select_flag = True
                for k, v in group.items():
                    for gt_attribute in sample['gt_attribute']:   # gt_attribute是一个list，截断合并的gt都在里面
                        if not gt_attribute:   # 如果没有GT属性，也不纳入计算
                            select_flag = False
                        elif gt_attribute[k] != v:  # 只要其中有一个gt的属性不符合标准，则不选中        
                            select_flag = False
                if select_flag:
                    group_scores[str(group)].append(score)

        result = {}
        for group_name, scores in group_scores.items():
            if len(scores) > 0:
                result[group_name] = sum(scores) / len(scores)    # paired级别的norm的均值
            else:
                result[group_name] = 'NaN'
                print(f'Warning: Empyty matched samples for {group_name}.')
        
        structure_only_result = {}
        for group_name, scores in group_scores_structure_only.items():
            if len(scores) > 0:
                structure_only_result[group_name] = sum(scores) / len(scores)    # paired级别的norm的均值
            else:
                structure_only_result[group_name] = 'NaN'
                print(f'Warning: Empyty matched samples for {group_name}.')

        return samples, {'TEDS': result, 'TEDS_structure_only': structure_only_result}


@METRIC_REGISTRY.register("BLEU")
class call_BLEU():
    def __init__(self, samples):
        self.samples = samples
    def evaluate(self, group_info=[]):
        group_samples = get_groups(self.samples, group_info)
        result = {}
        for group_name, samples in group_samples.items():
            predictions, references = [], []
            for sample in samples:
                gt = sample['norm_gt'] if sample.get('norm_gt') else sample['gt']
                pred = sample['norm_pred'] if sample.get('norm_pred') else sample['pred']
                predictions.append(gt)
                references.append(pred)
            bleu = evaluate.load("bleu", keep_in_memory=True, experiment_id=random.randint(1,1e8))
            bleu_results = bleu.compute(predictions=predictions, references=references)
            result[group_name] = bleu_results["bleu"]
        
        return self.samples, {'BLEU': result}
    
@METRIC_REGISTRY.register("METEOR")
class call_METEOR():
    def __init__(self, samples):
        self.samples = samples
    def evaluate(self, group_info=[]):
        group_samples = get_groups(self.samples, group_info)
        result = {}
        for group_name, samples in group_samples.items():
            predictions, references = [], []
            for sample in samples:
                gt = sample['norm_gt'] if sample.get('norm_gt') else sample['gt']
                pred = sample['norm_pred'] if sample.get('norm_pred') else sample['pred']
                predictions.append(gt)
                references.append(pred)
            meteor = evaluate.load('meteor', keep_in_memory=True, experiment_id=random.randint(1,1e8))
            meteor_results = meteor.compute(predictions=predictions, references=references)
            result[group_name] = meteor_results['meteor']
        
        return self.samples, {'METEOR': result}

@METRIC_REGISTRY.register("Edit_dist")
class call_Edit_dist():
    def __init__(self, samples):
        self.samples = samples
    def evaluate(self, group_info=[]):
        group_scores = defaultdict(list)
        samples = self.samples
        for sample in samples:
            gt = sample['norm_gt'] if sample.get('norm_gt') else sample['gt']
            pred = sample['norm_pred'] if sample.get('norm_pred') else sample['pred']
            if len(pred) > 0 or len(gt) > 0:
                normalized_edit_dist = Levenshtein.distance(pred, gt) / max(len(pred), len(gt))
                if not sample.get('metric'):
                    sample['metric'] = {}
                sample['metric']['Edit_dist'] = normalized_edit_dist
                group_scores['all'].append(normalized_edit_dist)
                for group in group_info:
                    select_flag = True
                    for k, v in group.items():
                        for gt_attribute in sample['gt_attribute']:   # gt_attribute是一个list，截断合并的gt都在里面
                            if not gt_attribute:   # 如果没有GT属性，也不纳入计算
                                select_flag = False
                            elif gt_attribute[k] != v:  # 只要其中有一个gt的属性不符合标准，则不选中        
                                select_flag = False
                    if select_flag:
                        group_scores[str(group)].append(normalized_edit_dist)

        result = {}
        for group_name, scores in group_scores.items():
            if len(scores) > 0:
                result[group_name] = sum(scores) / len(scores)    # paired级别的norm的均值
            else:
                result[group_name] = 'NaN'
                print(f'Warning: Empyty matched samples for {group_name}.')

        return samples, {'Edit_dist': result}
    
# @METRIC_REGISTRY.register("Move_dist")
# class call_Move_dist():
#     def __init__(self, dataset):
#         self.dataset = dataset
#     def evaluate(self, group_info=[]):
#         gt_len = 0
#         move_dist_list = []
#         for sample in self.dataset.samples:
#             pred = sample['pred']
#             gt = sample['gt']
#             assert len(gt) == len(pred), 'Not right length'
#             step = 0
#             for i, gt_c in enumerate(gt):
#                 if gt_c != pred[i]:
#                     step += abs(i - pred.index(gt_c))
#                     pred.pop(pred.index(gt_c))
#                     pred.insert(i, gt_c)
#             move_dist_list.append(step)
#             gt_len += len(gt)
        
#         if gt_len != 0:
#             Move_dist = sum(move_dist_list) / gt_len
#         else:
#             Move_dist = 0

#         return {'Move_dist': Move_dist}
    
@METRIC_REGISTRY.register("CDM")
class call_CDM():
    def __init__(self, samples):
        self.samples = samples
    def evaluate(self, group_info=[]):
        cdm_samples = copy.deepcopy(self.samples)
        for i, sample in enumerate(cdm_samples):
            sample['image_name'] = sample['img_id']
            sample['img_id'] = str(i)
        time_stap = time.time()
        with open(f'result/{time_stap}_formula.json', 'w', encoding='utf-8') as f:
            json.dump(cdm_samples, f, indent=4, ensure_ascii=False)
        return self.samples, False