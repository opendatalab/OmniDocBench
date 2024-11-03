
import Levenshtein
import re
from collections import Counter
import itertools
from functools import reduce
from utils.extract import inline_filter
from copy import deepcopy
import numpy as np


class WrapStr:
    def __init__(self, idx, content, sep=""):
        self.idx = idx
        self.contents = [content]
        self.indices = [idx]
        self.sep = sep
        self._content = content 

    def content(self):
        return self._content

    def __add__(self, other):
        """
        The order matters
        """
        self.idx = min(self.idx, other.idx)
        self.indices += other.indices
        self.contents += other.contents
        self._content = self.sep.join(self.contents)

    def idx_in(self, idx):
        return idx in self.indices

    def __len__(self):
        return len(self._content)


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
        self.separator = ''

        self._gs = [WrapStr(idx, content, self.separator) for idx, content in enumerate(gts)]
        self._preds = [WrapStr(idx, content, self.separator) for idx, content in enumerate(preds)]


        self.frozen_gts = set()
        self.frozen_preds = set()
        self.matched_h = {}

        self._slide_window_dp_memo = {}
        self.__preds = preds
        self.__gts = gts

        """
        self.gs = self.separator.join(self._gts)
    
        self.gt_presum = cal_presum([len(gts[i]) + len(self.separator) for i in range(len(gts)-1)] + [len(gts[-1])])
        self.pred_presum = cal_presum([len(preds[i]) + len(self.separator) for i in range(len(preds)-1)] + [len(preds[-1])])
        self.pred_dp_h = self.pred_dp_alone_gt()
        self.best_pos_arr = self.get_topK_best_pos()
        self.step_dp_h = {}
        """


    def match_stage1(self):
        # match stage 1
        equal_match_pair = {}
        gs_used_s, preds_used_s = set(), set()
        for i in range(len(self._gs)):
            for j in range(len(self._preds)):
                if j in preds_used_s: continue
                if self._gs[i].content() == self._preds[j].content():
                    equal_match_pair[i] = j
                    gs_used_s.add(i)
                    preds_used_s.add(j)

        # match stage 2 
        combine_gs_match_preds_ret_h = self._match_stage_2(self._gs, self._preds, gs_used_s, preds_used_s)

        for pred_idx in combine_gs_match_preds_ret_h.keys():
            preds_used_s.add(pred_idx)
            for gt_idx, _ in combine_gs_match_preds_ret_h[pred_idx]:
                gs_used_s.add(gt_idx)
        
        combine_preds_match_gs_ret_h = self._match_stage_2(self._gs, self._preds, preds_used_s, gs_used_s)
        
        for gt_idx in combine_preds_match_gs_ret_h.keys():
            gs_used_s.add(pred_idx)
            for pred_idx, _ in combine_preds_match_gs_ret_h[gt_idx]:
                preds_used_s.add(pred_idx)

        gs_free_arr = [i for i in range(len(self._gs)) if i not in gs_used_s]
        pred_free_arr = [i for i in range(len(self._preds)) if i not in preds_used_s]

        # return combine_gs_match_preds_ret_h, combine_preds_match_gs_ret_h
        return gs_free_arr, pred_free_arr

    def _match_stage_2(self, window_arr, line_arr, window_used_s, line_used_s):
        MATCH_EDIT_DIS_RATIO = 0.05
        ABS_DIFF_LEN = 20
        ABS_DIFF_CHAR_COUNT = 5

        SIGMA_MULTIPLE = 2

        edit_dis_h = {}
        def _dp(s, t):
            window = s.content()
            line = t.content()
            dp = self.slide_window_dp(line, window)
            ret = float('inf')
            pos = 0
            for i in range(len(line)):
                if ret > dp[i][len(window)-1]: 
                    ret = dp[i][len(window)-1]
                    pos = i
            return (ret, pos)

        for i in range(len(window_arr)):
            if i in window_used_s: continue
            for j in range(len(line_arr)):
                if j in line_used_s: continue
                edit_dis_h[(i, j)] = _dp(window_arr[i], line_arr[j])

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
            if i in matched_gt_idx_s:
                continue
            for j in range(len(line_arr)):
                if j in line_used_s: continue
                edit_dis_pair.append((j, *edit_dis_h[i, j]))

            if len(edit_dis_pair) == 0:
                continue

            if len(edit_dis_pair) == 1:
                best_j_idx, edit_dis, pos = edit_dis_pair[0]
                matched_gt_idx_s.add(i)
                matched_pair_h_gt[best_j_idx].append((i, pos))
                continue
            
            edit_dis_arr = np.array([edit_dis for _, edit_dis, pos in edit_dis_pair])
            mean = np.mean(edit_dis_pair)
            std_var = np.std(edit_dis_arr)
            
            beyond_sigma = sorted([(j, edit_dis, pos) for j, edit_dis, pos in edit_dis_pair if mean -  SIGMA_MULTIPLE*std_var >= edit_dis], key=lambda x: x[1])
            if len(beyond_sigma) > 0:
                matched_pair_h_gt[beyond_sigma[0][0]].append((i, beyond_sigma[0][2]))

        # gts idx is not the order appeart in preds, that is very bad, we need a fast way to reorder it!
        return matched_pair_h_gt
    

    def match_stage2(self): 
        """
        return : [[idx of self._preds]]
        """
        max_capacity = 1000
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
                # i_preds = self.separator.join([self._preds[t_idx][:t_pos+1-L] for (t_idx, t_pos) in tups])
                # dis = Levenshtein.distance(i_gts, i_preds)
                dis = float('inf')
                best_combination_candidates.append(([t_idx for t_idx, _ in tups], dis,  pos))
   
                
            # best_pos_arr_combination = sorted(best_combination_candidates, key=lambda x: x[1])[:30]
            best_pos_arr_combination = best_combination_candidates

            # print(best_pos_arr_combination)
            for o_bits, o_tup, o_edit_dis, o_pos in memo:
                pre_matched_str_len = sum([len(self._preds[j]) for j in reduce(lambda r,x:  r + list(x[1]), o_tup, [])])

                for pr_idxes, edit_dis, pos in best_pos_arr_combination:
                    pr_bits = sum([1 << idx for idx in pr_idxes])
                    pr_str_len = sum([len(self._preds[idx]) for idx in pr_idxes])
                    if pr_bits & o_bits > 0:
                        continue

                    if o_tup not in self.step_dp_h:
                        dp = self.build_step_window_dp()
                    else:
                        dp = self.step_dp_h[o_tup]
                    
                    dp = deepcopy(dp)
                    n_tup =  tuple(list(o_tup) + [(i, tuple(pr_idxes))])
                    
                    matched_pred_ss = self.separator.join([self._preds[j] for j in reduce(lambda r,x:  r + list(x[1]), n_tup, [])])

                    dp, edit_dis = self.step_window_dp(i_gts, matched_pred_ss, 1 if len(o_tup) == 0 else self.gt_presum[o_tup[-1][0]]+1, self.gt_presum[i], pre_matched_str_len+1, dp)
                    self.step_dp_h[n_tup] = dp

                    tmp.append((o_bits | pr_bits, 
                                n_tup,
                                edit_dis, 
                                pos))
            memo.extend(tmp)
            if len(memo) >= max_capacity:
                memo = shrink(memo, self.gt_presum[i], max_capacity)
        memo = shrink(memo, self.gt_presum[-1], max_capacity)

        tups_h = {}
        for v in memo:
            key = tuple(reduce(lambda r,x:  r + list(x[1]), v[1], []))
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
        """
        slide match gs in ss, the order of (gs, ss) is very important !
        """
        k1, k2 = hash(gs), hash(ss)
        if (k1, k2) in self._slide_window_dp_memo:
            return self._slide_window_dp_memo[(k1, k2)]

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
        self._slide_window_dp_memo[(k1, k2)] = dp
        return dp

    def step_window_dp(self, gs, ss, start_pos_gs, end_pos_gs, start_pos_ss, dp):
        """
        start_pos_gs: 匹配 gs 的开始的位置，下表从 1 开始
        end_pos_gs: 匹配 gs 的终止位置，下标从 1 开始
        start_pos_ss: 匹配 ss 的开始位置，下标从 1 开始
        """
        for i in range(start_pos_gs, end_pos_gs+1):
            for j in range(start_pos_ss, len(ss)+1):
                dp[i][j] = dp[i-1][j-1]
                if gs[i-1] != ss[j-1]:
                    dp[i][j] += 1
                dp[i][j] = min(dp[i][j], dp[i][j-1]+1, dp[i-1][j]+1)

        edit_dis = float('inf')
        for i in range(start_pos_gs, end_pos_gs+1):
            edit_dis = min(edit_dis, dp[i][len(ss)])

        return dp, edit_dis

    def build_step_window_dp(self):
        gs = self.separator.join(self._gts)
        preds = self.separator.join(self._preds)
        dp = [[float('inf')]*(len(preds)+1) for _ in range(len(gs)+1)]
        dp[0][0] = 0

        for i in range(len(gs)+1):
            dp[i][0] = i

        for j in range(len(preds)+1):
            dp[0][j] = j 
        return dp 

    def pred_dp_alone_gt(self):
        pred_dp_h = {}
        # prepare
        for i in range(len(self._preds)):
            pred_dp_h[i] = self.slide_window_dp(self.gs, self._preds[i])
        return pred_dp_h

    def get_topK_best_pos(self): # [(idx, edit_dis, pos)]
        MAX_BEST_POS = 2 # may be multiple by 2 
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
            best_gt_pos = []

            for edit_dis, gt_idx, pos in gt_pos:
                if gt_idx not in best_gt_h_flag:
                    best_gt_h_flag[gt_idx] = 1
                    best_gt_pos.append((edit_dis, gt_idx, pos))
                    if len(best_gt_pos) == 2:
                        break
            
            expanded_best_gt_pos = []
            for edit_dis, pre_gt_idx in [(edit_dis, gt_idx -1) for edit_dis, gt_idx, _ in best_gt_pos]:
                if 0 > pre_gt_idx or pre_gt_idx in best_gt_h_flag:
                    continue
                expanded_best_gt_pos.append((edit_dis, pre_gt_idx, self.gt_presum[pre_gt_idx]-1))

            for edit_dis, gt_idx, pos in best_gt_pos + expanded_best_gt_pos:
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

