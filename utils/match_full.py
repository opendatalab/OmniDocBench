
import Levenshtein
import re
from collections import Counter
import itertools
from functools import reduce
from utils.extract import inline_filter

def cal_presum(arr):
    if len(arr) == 0:
        return []
    presum = [0] * len(arr)
    presum[0] = arr[0]
    for i in range(1, len(arr)):
        presum[i] = presum[i-1] + arr[i]
    return presum

class FuzzyMatch:
    def __init__(self, gts, preds):
        self._gts = gts
        self.separator = ""
        self.gs = self.separator.join(self._gts)
        self._preds = preds
        self.gt_presum = cal_presum([len(gts[i]) + len(self.separator) for i in range(len(gts)-1)] + [len(gts[-1])])
        self.pred_presum = cal_presum([len(preds[i]) + len(self.separator) for i in range(len(preds)-1)] + [len(preds[-1])])
        self.pred_dp_h = self.pred_dp_alone_gt()
        self.best_pos_arr = self.get_topK_best_pos()

    def match(self): 
        """
        return : [[idx of self._preds]]
        """
        max_capacity = 1 * 10 ** 5
        shrink_capacity = 1000   # should extract the top N best based on data distribution !!
        memo = [(0,(), 0, -1)]

        def shrink(memo, current_pos, capacity):
            arr = sorted([(v[2] + max(0, current_pos - v[-1]), v)  for v in memo], key=lambda x: x[0])
            return [v[1] for v in arr[:capacity]]

        # k, edit_dis, pos
        for i in range(len(self._gts)):
            tmp = []
            # even two string ends at index i. the combination of them may achieve better result
            combinations = []
       
            best_pos_arr_combination = []
            best_combination_candidates = []
            best_pos_arr = sorted(self.best_pos_arr[i], key=lambda x:x[2])  # [(k, edit_dis, pos)]
   
            for pr_idx, _, pos in sorted(self.best_pos_arr[i], key=lambda x: x[2]):
                c_tmp = []
                for pr_idx_tups, o_pos in combinations:
                    if o_pos >= pos or (0.7 * len(self._preds[pr_idx]) > pos - o_pos and len(self._preds[pr_idx]) > 10):
                        continue
                    c_tmp.append((list(pr_idx_tups)+[(pr_idx, pos)], pos))
                c_tmp.append(([(pr_idx, pos)], pos))
                combinations.extend(c_tmp)
    
            i_gts = self.separator.join(self._gts[:i+1])
            NI = len(i_gts)
            L = 0 
            if i > 0:
                L = self.gt_presum[i-1]
            for tups, pos in combinations:
                i_preds = self.separator.join([self._preds[t_idx][:t_pos+1-L] for (t_idx, t_pos) in tups])
                dis = Levenshtein.distance(i_gts, i_preds)
                best_combination_candidates.append(([t_idx for t_idx, _ in tups], dis,  pos))

            best_pos_arr_combination = sorted(best_combination_candidates, key=lambda x: x[1])[:30]

            # print(best_pos_arr_combination)
            for o_bits, o_tup, o_edit_dis, o_pos in memo:
                for pr_idxes, edit_dis, pos in best_pos_arr_combination:
                    pr_bits = sum([1 << idx for idx in pr_idxes])
                    pr_str_len = sum([len(self._preds[idx]) for idx in pr_idxes])
                    if pr_bits & o_bits > 0:
                        continue
                    tmp.append((o_bits | pr_bits, 
                                tuple(list(o_tup) + [(i, list(pr_idxes))]), 
                                o_edit_dis + edit_dis + abs(pos - o_pos - pr_str_len), 
                                pos))
            memo.extend(tmp)
            if len(memo) >= max_capacity:
                memo = shrink(memo, self.gt_presum[i], shrink_capacity)
        memo = shrink(memo, self.gt_presum[-1], shrink_capacity)

        tups_h = {}
        for v in memo:
            key = tuple(reduce(lambda r,x:  r + x[1], v[1], []))
            tups_h[key] = v

        stack = []
        for tups in tups_h.keys():
            candiate_s = "".join([self._preds[idx] for idx in tups])
            edit_dis = Levenshtein.distance(self.gs, candiate_s)
            stack.append((edit_dis, tups))

        ret = [[] for _ in range(len(self._gts))]
        key =sorted(stack, key=lambda x:x[0])[0][1]
        for gt_idx, tups in tups_h[key][1]:
            ret[gt_idx] = tups
        return ret

    def slide_window_dp(self, gs, ss):
        # that must be right !
        N, M = len(gs), len(ss)
        dp = [[float('inf')]*M for _ in range(N)]
        for i in range(N):
            dp[i][0] = 1
            if gs[i] == ss[0]:
                dp[i][0] = 0

        for j in range(1, M):
            for i in range(1, N):
                dp[i][j] = dp[i-1][j-1]
                if gs[i] != ss[j]:
                    dp[i][j] += 1
                dp[i][j] = min(dp[i][j], dp[i][j-1]+1, dp[i-1][j]+1)
        return dp

    def pred_dp_alone_gt(self):
        pred_dp_h = {}
        # prepare
        for i in range(len(self._preds)):
            pred_dp_h[i] = self.slide_window_dp(self.gs, self._preds[i])
        return pred_dp_h

    def get_topK_best_pos(self): # [(idx, edit_dis, pos)]
        def extract_edit_chain(arr):
            ret = {}
            seen = set() 
            arr = sorted(arr, key=lambda x: x[0])[:50]
            h = {pos: edit_dis for edit_dis, pos in arr}

            def find_longest_incremental_chain(pos, incr):
                l = 1 
                seen.add(pos)
                while True:
                    if (pos+incr) in seen or (pos + incr) not in h or h[pos] > h[pos+incr]: 
                        break
                    pos = pos + incr 
                    seen.add(pos)
                    l += 1
                return l

            for edit_dis, pos in arr:
                if pos in seen:
                    continue
                l1 = find_longest_incremental_chain(pos, 1)
                l2 = find_longest_incremental_chain(pos, -1)
                ret[pos] = [l1 + l2, edit_dis]
            return ret

        def may_get_the_best(arr, max_l): # [(length, edit_dis, pos)]
            arr = sorted(arr, key=lambda x: -x[1])
            stack = []
            while arr:
                length, edit_dis, pos = arr.pop()
                if stack:
                    if edit_dis - stack[-1][1] > 0.1 * max_l and max_l > 10:
                        continue
                stack.append((length, edit_dis, pos))
            return stack

        res = [[] for _ in range(len(self._gts))]
        for k in sorted(self.pred_dp_h.keys()):
            dp = self.pred_dp_h[k]
            L = len(self._preds[k])
            arr = [(dp[i][L-1], i) for i in range(len(self.gs))]
            chains_h = extract_edit_chain(arr)
            best_pos_arr = may_get_the_best([(*chains_h[k], k) for k in chains_h.keys()], len(self._preds[k]))

            arr = sorted(best_pos_arr, key=lambda x: x[1]) # [(l1+l2, edit_dis, pos)]

            gt_pos = [] # (edit_dis, gt index) 
            for _, edit_dis, pos in arr:
                if edit_dis * 1.0 / len(self._preds[k]) > 0.7:
                    continue
                for j in range(len(self._gts)):
                    if self.gt_presum[j] >= pos + 1:
                        gt_pos.append((edit_dis, j, pos))
                        break
            gt_pos = sorted(gt_pos, key=lambda x:x[0])
            best_gt_h_flag = {}
            for edit_dis, gt_idx, pos in gt_pos:
                if gt_idx not in best_gt_h_flag:
                    best_gt_h_flag[gt_idx] = 1
                    res[gt_idx].append((k, edit_dis, pos))
        return res

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
        return [[] * len(gts)]
    if len(gts) == 0:
        return []

    matcher = FuzzyMatch(gts, predications)
    return matcher.match()


def match_gt2pred_full(gts, predications):
    res = match_gt_pred(gts, predications)
    
    return [
            {
                "gt_idx": gt_idx,  
                "gt": gts[gt_idx],
                "pred_idx": pred_indices,
                "pred": "".join([predications[pred_i] for pred_i in pred_indices])
            } for gt_idx, pred_indices in enumerate(res)
        ]

def match_gt2pred_textblock_full(gt_lines, pred_lines):
    text_inline_match_s = match_gt2pred_full(gt_lines, pred_lines, 'text')
    plain_text_match = []
    inline_formula_match = []
    for item in text_inline_match_s:
        plaintext_gt, inline_gt_list = inline_filter(item['gt'])  # 这个后续最好是直接从span里提取出来
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

