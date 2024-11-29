
import Levenshtein
import re
from collections import Counter
import itertools
from functools import reduce
from utils.extract import inline_filter
from copy import deepcopy
import numpy as np


class FuzzyMatch:
    def __init__(self, gts, preds):
        self.separator = ''
        self._gs = gts
        self._preds = preds
        self.matched_h = {}

    def match(self):
        # match stage 1
        equal_match_pair = {}
        gs_used_s, preds_used_s = set(), set()
        for i in range(len(self._gs)):
            for j in range(len(self._preds)):
                if self._gs[i] == self._preds[j]:
                    equal_match_pair[i] = j
                    gs_used_s.add(i)
                    preds_used_s.add(j)

        # match stage 2 
        # { pred_idx : [ gt_idx0, gt_idx1 ]}
        combine_gs_match_preds_ret_h = self._combine_match(self._gs, self._preds, gs_used_s, preds_used_s)

        for pred_idx in combine_gs_match_preds_ret_h.keys():
            preds_used_s.add(pred_idx)
            for gt_idx, _ in combine_gs_match_preds_ret_h[pred_idx]:
                gs_used_s.add(gt_idx)
        
        # match stage 3
        # { gt_idx : [ pred_idx0, pred_idx1 ]} 
        combine_preds_match_gs_ret_h = self._combine_match(self._preds, self._gs, preds_used_s, gs_used_s)

        for gt_idx in combine_preds_match_gs_ret_h.keys():
            gs_used_s.add(gt_idx)
            for pred_idx, _ in combine_preds_match_gs_ret_h[gt_idx]:
                preds_used_s.add(pred_idx)

        # match stage 4
        gs_free_arr = [i for i in range(len(self._gs)) if i not in gs_used_s]
        pred_free_arr = [i for i in range(len(self._preds)) if i not in preds_used_s]

        ## cal gs_free match combine_gs_match_preds
        match_gs_free_pred_combine_ret_h = self._free_match_1(gs_free_arr, self._gs, combine_gs_match_preds_ret_h, self._preds)
        match_pred_free_gs_combine_ret_h = self._free_match_1(pred_free_arr, self._preds, combine_preds_match_gs_ret_h, self._gs)

        pred_free_gt_free_h = {} 
        for i in range(len(pred_free_arr)):
            for j in range(len(gs_free_arr)):
                edit_dis, pos = self._dp(self._preds[i], self._gs[j])
                pred_free_gt_free_h[(j, i)] = (edit_dis, pos)

        gt_free_pred_free_h = {}
        for i in range(len(gs_free_arr)):
            for j in range(len(pred_free_arr)):
                edit_dis, pos = self._dp(self._gs[i], self._preds[j])
                gt_free_pred_free_h[(j, i)] = (edit_dis, pos)

        class MatchPair:
            def __init__(self, pred_idx, gt_idx):
                self.pred_idx = pred_idx
                self.gt_idx = gt_idx

        edit_dis_q = []     # heapq 
        ### cal gt match 
        for free_gt_idx in gs_free_arr:
            for pred_idx in range(len(self._preds)):
                if (pred_idx, free_gt_idx) in match_gs_free_pred_combine_ret_h:
                    edit_dis_q.append((match_gs_free_pred_combine_ret_h[(pred_idx, free_gt_idx)], MatchPair(pred_idx, free_gt_idx)))
                if (pred_idx, free_gt_idx) in gt_free_pred_free_h:
                    edit_dis_q.append((gt_free_pred_free_h[(pred_idx, free_gt_idx)], MatchPair(pred_idx, free_gt_idx)))

        ### cal pred match
        for free_pred_idx in pred_free_arr:
            for gt_idx in range(len(self._gs)):
                if (gt_idx, free_pred_idx) in match_pred_free_gs_combine_ret_h:
                    edit_dis_q.append((match_pred_free_gs_combine_ret_h[(gt_idx, free_pred_idx)], MatchPair(free_pred_idx, gt_idx)))

                if (gt_idx, free_pred_idx) in pred_free_gt_free_h:
                    edit_dis_q.append((pred_free_gt_free_h[(gt_idx, free_pred_idx)], MatchPair(free_pred_idx, gt_idx)))

        # matched groud_truth and predications
        ## first, merge matched pair!
        matched_gt_pred_h = {} 

        for gt_idx in equal_match_pair:
            pred_idx = equal_match_pair[gt_idx]
            matched_gt_pred_h[(gt_idx, pred_idx, -1)] = True

        for gt_idx in combine_preds_match_gs_ret_h.keys():
            for pred_idx, pos in combine_preds_match_gs_ret_h[gt_idx]:
                matched_gt_pred_h[(gt_idx, pred_idx, pos)] = True

        for pred_idx in combine_gs_match_preds_ret_h.keys():
            for gt_idx, pos in combine_gs_match_preds_ret_h[pred_idx]:
                matched_gt_pred_h[(gt_idx, pred_idx, pos)] = True

        edit_dis_q.sort(key=lambda x:x[0][0])

        used_pred_idx_s, used_gt_idx_s = set(), set() 

        for match_info, p in edit_dis_q:
            edit_dis, pos = match_info
            pred_idx, gt_idx = p.pred_idx, p.gt_idx
            if edit_dis*1.0 / min(len(self._preds[pred_idx]), len(self._gs[gt_idx])) >= 0.5:
                continue
            if pred_idx in pred_free_arr and pred_idx in used_pred_idx_s:
                continue
            if gt_idx in gs_free_arr and gt_idx in used_gt_idx_s:
                continue

            matched_gt_pred_h[(gt_idx, pred_idx, pos)] = True

            if pred_idx in pred_free_arr:
                used_pred_idx_s.add(pred_idx)

            if gt_idx in gs_free_arr:
                used_gt_idx_s.add(gt_idx)

        group_by_gt, group_by_pred, gt_one_pred = {}, {}, {}
        gs_matched_s, pred_matched_s = set(), set()
        for gt_idx, pred_idx, pos in matched_gt_pred_h.keys():
            gs_matched_s.add(gt_idx)
            pred_matched_s.add(pred_idx)
            if gt_idx not in group_by_gt:
                group_by_gt[gt_idx] = []
            if pred_idx not in group_by_pred:
                group_by_pred[pred_idx] = []
            
            group_by_gt[gt_idx].append((pred_idx, pos))
            group_by_pred[pred_idx].append((gt_idx, pos))

        # return combine_gs_match_preds_ret_h, combine_preds_match_gs_ret_h
        one = set()
        for gt_idx in group_by_gt.keys():
            if len(group_by_gt[gt_idx]) == 1:
                one.add((gt_idx, *group_by_gt[gt_idx][0]))        
        for pred_idx in group_by_pred.keys():
            if len(group_by_pred[pred_idx]) == 1:
                gt_idx, pos = group_by_pred[pred_idx][0]
                one.add((gt_idx, pred_idx, pos))
        
        for gt_idx, pred_idx, pos in one:
            if gt_idx in group_by_gt.keys() and pred_idx in group_by_pred.keys():
                if len(group_by_gt[gt_idx]) == 1 and len(group_by_pred[pred_idx]) == 1:
                    gt_one_pred[gt_idx] = [pred_idx, pos]
                elif len(group_by_gt[gt_idx]) == 1:
                    group_by_gt.pop(gt_idx)
                else:
                    group_by_pred.pop(pred_idx)
        return group_by_gt, group_by_pred, gt_one_pred

    def _free_match_1(self, free_source_idx, source_arr, combined_target_h, combined_target_arr):
        SHORT_STRING_LEN = 10 
        ret = {}
        def _do_match(target_str_segment):
            for free_idx in free_source_idx:
                edit_dis, pos = self._dp(source_arr[free_idx], target_str_segment)
                if (matched_target_idx, free_idx) not in ret:
                    ret[(matched_target_idx, free_idx)] = (edit_dis, pos)
                else:
                    if ret[(matched_target_idx, free_idx)][0] > edit_dis:
                        ret[(matched_target_idx, free_idx)] = (edit_dis, pos)

        for matched_target_idx in combined_target_h.keys():

            matched_source_idx_pos = sorted(combined_target_h[matched_target_idx], key=lambda x: x[1])
            if len(matched_source_idx_pos) == 0: continue

            for i, v in enumerate(matched_source_idx_pos):
                matched_source_idx, pos = v
                if i == 0:
                    hole_len = pos + 1 - len(source_arr[matched_source_idx])
                else:
                    hole_len = pos  - len(source_arr[matched_source_idx]) - matched_source_idx_pos[i-1][1]
            
                if 0 >= hole_len:
                    continue
                target_str_segment = combined_target_arr[matched_target_idx][pos+1-hole_len :pos+1]
                _do_match(target_str_segment)

            target_str_segment = combined_target_arr[matched_target_idx][matched_source_idx_pos[-1][1]+1:]
            if len(target_str_segment) > 0:
                _do_match(target_str_segment)

        return ret

    def slide_window_dp(self, line, window):
        # that must be right !
        N, M = len(line), len(window)
        dp = [[float('inf')]*M for _ in range(N)]
        for i in range(N):
            dp[i][0] = 1
            if line[i] == window[0]:
                dp[i][0] = 0

        for j in range(1, M):
            for i in range(1, N):
                dp[i][j] = dp[i-1][j-1]
                if line[i] != window[j]:
                    dp[i][j] += 1
                dp[i][j] = min(dp[i][j], dp[i][j-1]+1, dp[i-1][j]+1)
        return dp

    def _dp(self, window, line):
            dp = self.slide_window_dp(line, window)
            ret = float('inf')
            pos = 0
            for i in range(len(line)):
                if ret > dp[i][len(window)-1]: 
                    ret = dp[i][len(window)-1]
                    pos = i
            return (ret, pos)

    def _combine_match(self, window_arr, line_arr, window_used_s, line_used_s):
        MATCH_EDIT_DIS_RATIO = 0.10
        ABS_DIFF_LEN = 20
        ABS_DIFF_CHAR_COUNT = 5

        SIGMA_MULTIPLE = 2
        edit_dis_h = {}

        for i in range(len(window_arr)):
            if i in window_used_s: continue
            for j in range(len(line_arr)):
                if j in line_used_s: continue
                edit_dis_h[(i, j)] = self._dp(window_arr[i], line_arr[j])

        # search the one to one pair or combined pattern!
        matched_pair_h_gt = {}
        matched_gt_idx_s = set()
        for i in range(len(window_arr)):
            if i in window_used_s: continue
            edit_dis, pos = float('inf'), -1
            min_j_idx = -1
 
            for j in range(len(line_arr)):
                if j in line_used_s: continue
                if edit_dis > edit_dis_h[(i, j)][0]:
                    edit_dis, pos = edit_dis_h[(i, j)]
                    min_j_idx = j

            if pos == -1: continue
            if min_j_idx not in matched_pair_h_gt:
                matched_pair_h_gt[min_j_idx] = []
            if edit_dis < len(window_arr[i]) * MATCH_EDIT_DIS_RATIO or (ABS_DIFF_LEN >= len(window_arr[i]) and ABS_DIFF_CHAR_COUNT >= edit_dis):
                matched_pair_h_gt[min_j_idx].append((i, pos))
                matched_gt_idx_s.add(i)
    
        for i in range(len(window_arr)):
            if i in window_used_s: continue

            edit_dis_pair = []
            if i in matched_gt_idx_s: continue
            for j in range(len(line_arr)):
                if j in line_used_s: continue
                edit_dis_pair.append((j, *edit_dis_h[i, j]))

            if len(edit_dis_pair) == 0: continue
            if len(edit_dis_pair) == 1:
                best_j_idx, edit_dis, pos = edit_dis_pair[0]
                matched_gt_idx_s.add(i)
                matched_pair_h_gt[best_j_idx].append((i, pos))
                continue
            
            edit_dis_arr = np.array([edit_dis for _, edit_dis, _ in edit_dis_pair])
            mean = np.mean(edit_dis_pair)
            std_var = np.std(edit_dis_arr)
            
            beyond_sigma = sorted([(j, edit_dis, pos) for j, edit_dis, pos in edit_dis_pair if mean -  SIGMA_MULTIPLE*std_var >= edit_dis], key=lambda x: x[1])
            if len(beyond_sigma) > 0:
                matched_pair_h_gt[beyond_sigma[0][0]].append((i, beyond_sigma[0][2]))

        # gts idx is not the order appeart in preds, that is very bad, we need a fast way to re-order it!
        return {k: matched_pair_h_gt[k] for k in matched_pair_h_gt.keys() if len(matched_pair_h_gt[k]) > 0  }


def match_gt_pred(gts, predications):
    """
    parameters: 
            gts         : groud truth list,  [gt0, gt1, gt2, gt3, gt4]
            predications: predications list 
    return:  list of array that match the each element of ground truth 

    Example:
        gts = [gt0, gt1, gt2,]
        preds = [pr0, pr1, pr2]

        returns : [
            [pr0, pr2],  # [pr0, pr2] match gt0
            [],          # no pred match the gt1
            [pr1]        # [pr1] match gt2
        ]
    """ 
    if any([len(v) == 0 for v in predications]):
        raise Exception("please remove empty string from predications list")
    if len(predications) == 0:
        return {}, {}, {}
    if len(gts) == 0:
        return {}, {}, {}

    matcher = FuzzyMatch(gts, predications)
    return matcher.match()


def match_gt2pred_full(gts, predications):
    group_by_gt, group_by_pred, gt_one_pred = match_gt_pred(gts, predications)
    seen_gt_s = set() 

    ret = []
    for gt_idx in group_by_gt.keys():
        matched_preds = [p[0] for p in sorted(group_by_gt[gt_idx], key=lambda x:x[1])]
        ret.append({
            "gt_idx": [gt_idx],
            "gt": gts[gt_idx],
            "pred_idx": matched_preds,
            "pred": "".join([predications[pr_idx] for pr_idx in matched_preds])
        })
        seen_gt_s.add(gt_idx)

    for pred_idx in group_by_pred:
        matched_gts = [p[0] for p in sorted(group_by_pred[pred_idx], key=lambda x:x[1])]
        ret.append({
            "gt_idx": matched_gts,
            "gt": "".join([gts[gt_idx] for gt_idx in matched_gts]),
            "pred_idx": [pred_idx],
            "pred": predications[pred_idx]
        })
    
        for gt_idx in matched_gts:
            seen_gt_s.add(gt_idx)

    for gt_idx in gt_one_pred.keys():
        pred_idx = gt_one_pred[gt_idx][0]
        ret.append({
            "gt_idx": [gt_idx],
            "gt": gts[gt_idx],
            "pred_idx": [pred_idx],
            "pred": predications[pred_idx]
        })
    seen_gt_s.add(gt_idx)

    for i in range(len(gts)):
        if i in seen_gt_s: continue
        ret.append({
            "gt_idx": [i],
            "gt": gts[i],
            "pred_idx": [],
            "pred": ""
        })
    return ret


def match_gt2pred_textblock_full(gt_lines, pred_lines):
    text_inline_match_s = match_gt2pred_full(gt_lines, pred_lines, 'text')
    plain_text_match = []
    inline_formula_match = []
    for item in text_inline_match_s:
        plaintext_gt, inline_gt_list = inline_filter(item['gt'])  # this should be extracted from span
        plaintext_pred, inline_pred_list = inline_filter(item['pred'])
        # print('inline_pred_list', inline_pred_list)
        # print('plaintext_pred: ', plaintext_pred)
        plaintext_gt = plaintext_gt.replace(' ', '')
        plaintext_pred = plaintext_pred.replace(' ', '')
        if plaintext_gt or plaintext_pred:
            edit = Levenshtein.distance(plaintext_gt, plaintext_pred)/max(len(plaintext_pred), len(plaintext_gt))
            plain_text_match.append({
                'gt_idx': item['gt_idx'],
                'gt': plaintext_gt,
                'pred_idx': item['pred_idx'],
                'pred': plaintext_pred,
                'edit': edit
            })

        if inline_gt_list:
            inline_formula_match_s = match_gt2pred_full(inline_gt_list, inline_pred_list)
            inline_formula_match.extend(inline_formula_match_s)    
    return plain_text_match, inline_formula_match
