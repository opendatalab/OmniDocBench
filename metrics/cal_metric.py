# import evaluate
# import random
import json
import time
from rapidfuzz.distance import Levenshtein
from .table_metric import TEDS
import evaluate
import random
from utils.read_files import save_paired_result
from registry.registry import METRIC_REGISTRY
import pdb


@METRIC_REGISTRY.register("TEDS")
class call_TEDS():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        teds = TEDS(structure_only=False)
        teds_socres = []
        for sample in self.dataset.samples:
            score = teds.evaluate(sample['pred'], sample['gt'])
            # print('TEDS score:', score)
            teds_socres.append(score)
        if len(teds_socres):
            return {'teds': sum(teds_socres) / len(teds_socres)}
        else:
            return {'teds': 'NaN'}


@METRIC_REGISTRY.register("BLEU")
class call_BLEU():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        predictions, references = [], []
        for sample in self.dataset.samples:
            predictions.append(sample['gt'])
            references.append(sample['pred'])
        bleu = evaluate.load("bleu", keep_in_memory=True, experiment_id=random.randint(1,1e8))
        bleu_results = bleu.compute(predictions=predictions, references=references)
        
        return {'BLEU': bleu_results["bleu"]}
    
@METRIC_REGISTRY.register("METEOR")
class call_METEOR():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        predictions, references = [], []
        for sample in self.dataset.samples:
            predictions.append(sample['gt'])
            references.append(sample['pred'])
        meteor = evaluate.load('meteor', keep_in_memory=True, experiment_id=random.randint(1,1e8))
        meteor_results = meteor.compute(predictions=predictions, references=references)
        
        return {'METEOR': meteor_results['meteor']}

@METRIC_REGISTRY.register("Edit_dist")
class call_Edit_dist():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        lev_dist = []
        gt_len = 0
        pred_len = 0
        for sample in self.dataset.samples:
            lev_dist.append(Levenshtein.distance(sample['pred'], sample['gt']))
            gt_len += len(sample['gt'])
            pred_len += len(sample['pred'])
        
        if gt_len != 0 or pred_len != 0:
            Edit_dist = sum(lev_dist) / max(gt_len, pred_len)
        else:
            Edit_dist = 0

        return {'Edit_dist': Edit_dist}
    
@METRIC_REGISTRY.register("Move_dist")
class call_Move_dist():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        gt_len = 0
        move_dist_list = []
        for sample in self.dataset.samples:
            pred = sample['pred']
            gt = sample['gt']
            assert len(gt) == len(pred), 'Not right length'
            step = 0
            for i, gt_c in enumerate(gt):
                if gt_c != pred[i]:
                    step += abs(i - pred.index(gt_c))
                    pred.pop(pred.index(gt_c))
                    pred.insert(i, gt_c)
            move_dist_list.append(step)
            gt_len += len(gt)
        
        if gt_len != 0:
            Move_dist = sum(move_dist_list) / gt_len
        else:
            Move_dist = 0

        return {'Move_dist': Move_dist}
    
@METRIC_REGISTRY.register("CDM")
class call_CDM():
    def __init__(self, dataset):
        self.dataset = dataset
    def evaluate(self):
        time_stap = time.time()
        with open(f'result/{time_stap}_formula.json', 'w', encoding='utf-8') as f:
            json.dump(self.dataset.samples, f, indent=4, ensure_ascii=False)