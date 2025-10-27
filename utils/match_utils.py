from itertools import combinations
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

import json
from pathlib import Path


def bbox_iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    x1 = max(float(box_a[0]), float(box_b[0]))
    y1 = max(float(box_a[1]), float(box_b[1]))
    x2 = min(float(box_a[2]), float(box_b[2]))
    y2 = min(float(box_a[3]), float(box_b[3]))
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area_a = (float(box_a[2]) - float(box_a[0])) * (float(box_a[3]) - float(box_a[1]))
    area_b = (float(box_b[2]) - float(box_b[0])) * (float(box_b[3]) - float(box_b[1]))
    union = area_a + area_b - inter
    if union <= 0.0:
        return 0.0
    return inter / union


def has_overlap(box_a: Sequence[float], box_b: Sequence[float]) -> bool:
    x1 = max(float(box_a[0]), float(box_b[0]))
    y1 = max(float(box_a[1]), float(box_b[1]))
    x2 = min(float(box_a[2]), float(box_b[2]))
    y2 = min(float(box_a[3]), float(box_b[3]))
    return x2 > x1 and y2 > y1


def union_box(boxes: Sequence[Sequence[float]], indices: Sequence[int]) -> Optional[List[float]]:
    if not indices:
        return None
    x1 = min(float(boxes[i][0]) for i in indices)
    y1 = min(float(boxes[i][1]) for i in indices)
    x2 = max(float(boxes[i][2]) for i in indices)
    y2 = max(float(boxes[i][3]) for i in indices)
    return [x1, y1, x2, y2]


def _build_overlap_maps(
    gt_boxes: Sequence[Sequence[float]],
    pred_boxes: Sequence[Sequence[float]],
) -> Tuple[Dict[int, List[int]], Dict[int, List[int]]]:
    gt_to_pred: Dict[int, List[int]] = {}
    pred_to_gt: Dict[int, List[int]] = {}
    for gi, g_box in enumerate(gt_boxes):
        overlaps = []
        for pi, p_box in enumerate(pred_boxes):
            if has_overlap(g_box, p_box):
                overlaps.append(pi)
                pred_to_gt.setdefault(pi, []).append(gi)
        if overlaps:
            gt_to_pred[gi] = overlaps
    for gi in list(gt_to_pred.keys()):
        gt_to_pred[gi].sort()
    for pi in list(pred_to_gt.keys()):
        pred_to_gt[pi].sort()
    return gt_to_pred, pred_to_gt


def _box_area(box: Sequence[float]) -> float:
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def _overlap_fraction(source_box: Sequence[float], target_box: Optional[Sequence[float]]) -> float:
    if target_box is None:
        return 0.0
    x1 = max(float(source_box[0]), float(target_box[0]))
    y1 = max(float(source_box[1]), float(target_box[1]))
    x2 = min(float(source_box[2]), float(target_box[2]))
    y2 = min(float(source_box[3]), float(target_box[3]))
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area_src = _box_area(source_box)
    if area_src <= 0.0:
        return 0.0
    return inter / area_src


def _best_subset_against_reference(
    reference_box: Sequence[float],
    candidate_boxes: Sequence[Sequence[float]],
    candidate_indices: Sequence[int],
    allow_merge: bool,
    max_merge: int,
) -> Tuple[List[int], float]:
    if not candidate_indices:
        return [], 0.0
    ordered = sorted(
        candidate_indices,
        key=lambda idx: bbox_iou(reference_box, candidate_boxes[idx]),
        reverse=True,
    )
    if (not allow_merge) or len(ordered) == 1:
        best_idx = ordered[0]
        return [best_idx], bbox_iou(reference_box, candidate_boxes[best_idx])

    limited = ordered[: max_merge if max_merge else len(ordered)]
    best_subset: List[int] = []
    best_iou = 0.0
    eps = 1e-9
    for r in range(1, len(limited) + 1):
        for combo in combinations(limited, r):
            merged = union_box(candidate_boxes, combo)
            if merged is None:
                continue
            current_iou = bbox_iou(reference_box, merged)
            if (current_iou > best_iou + eps) or (
                abs(current_iou - best_iou) <= eps and len(combo) > len(best_subset)
            ):
                best_iou = current_iou
                best_subset = list(combo)
    return best_subset, best_iou


def _enumerate_cluster_matches(
    cluster_gts: Sequence[int],
    cluster_preds: Sequence[int],
    gt_boxes: Sequence[Sequence[float]],
    pred_boxes: Sequence[Sequence[float]],
    allow_merge: bool,
    max_merge: int,
    limit_merge: bool,
) -> Optional[Tuple[List[int], List[int], float]]:
    if not cluster_gts or not cluster_preds:
        return None

    cluster_gts = sorted(cluster_gts)
    cluster_preds = sorted(cluster_preds)

    adjacency_g = {gi: set() for gi in cluster_gts}
    adjacency_p = {pi: set() for pi in cluster_preds}
    for gi in cluster_gts:
        for pi in cluster_preds:
            if has_overlap(gt_boxes[gi], pred_boxes[pi]):
                adjacency_g[gi].add(pi)
                adjacency_p[pi].add(gi)

    if limit_merge:
        best_state: Optional[Tuple[List[int], List[int], float]] = None
        eps = 1e-9

        for gi in cluster_gts:
            preds = adjacency_g.get(gi)
            if not preds:
                continue
            subset, iou_val = _best_subset_against_reference(
                gt_boxes[gi], pred_boxes, preds, allow_merge, max_merge
            )
            if not subset or iou_val <= 0.0:
                continue
            complexity = 1 + len(subset)
            if (
                best_state is None
                or iou_val > best_state[2] + eps
                or (abs(iou_val - best_state[2]) <= eps and complexity > len(best_state[0]) + len(best_state[1]))
            ):
                best_state = ([gi], subset, iou_val)

        for pi in cluster_preds:
            gts = adjacency_p.get(pi)
            if not gts:
                continue
            subset, iou_val = _best_subset_against_reference(
                pred_boxes[pi], gt_boxes, gts, allow_merge, max_merge
            )
            if not subset or iou_val <= 0.0:
                continue
            complexity = len(subset) + 1
            if (
                best_state is None
                or iou_val > best_state[2] + eps
                or (abs(iou_val - best_state[2]) <= eps and complexity > len(best_state[0]) + len(best_state[1]))
            ):
                best_state = (subset, [pi], iou_val)

        if best_state is not None:
            return best_state
        return None

    eps = 1e-9
    best_state: Optional[Tuple[List[int], List[int], float]] = None
    best_complexity = -1

    def evaluate(gt_subset: Sequence[int], pred_subset: Sequence[int]) -> None:
        nonlocal best_state, best_complexity
        if not gt_subset or not pred_subset:
            return
        if limit_merge and len(gt_subset) > 1 and len(pred_subset) > 1:
            return
        gt_union = union_box(gt_boxes, gt_subset)
        pred_union = union_box(pred_boxes, pred_subset)
        if gt_union is None or pred_union is None:
            return
        iou_val = bbox_iou(gt_union, pred_union)
        if iou_val <= 0.0:
            return
        complexity = len(gt_subset) + len(pred_subset)
        if (
            best_state is None
            or iou_val > best_state[2] + eps
            or (abs(iou_val - best_state[2]) <= eps and complexity > best_complexity)
        ):
            best_state = (list(gt_subset), list(pred_subset), iou_val)
            best_complexity = complexity

    visited: set[Tuple[FrozenSet[int], FrozenSet[int]]] = set()
    stack: List[Tuple[FrozenSet[int], FrozenSet[int]]] = []
    for gi in cluster_gts:
        for pi in adjacency_g.get(gi, ()):
            stack.append((frozenset({gi}), frozenset({pi})))

    while stack:
        g_set, p_set = stack.pop()
        state_key = (g_set, p_set)
        if state_key in visited:
            continue
        visited.add(state_key)

        evaluate(sorted(g_set), sorted(p_set))

        if not allow_merge:
            continue

        allow_expand_pred = True
        allow_expand_gt = True
        if limit_merge:
            if len(g_set) > 1:
                allow_expand_pred = False
            if len(p_set) > 1:
                allow_expand_gt = False

        if allow_expand_gt and len(g_set) < max_merge:
            candidate_g = set()
            for pi in p_set:
                candidate_g.update(adjacency_p.get(pi, ()))
            candidate_g = (candidate_g - set(g_set)) & set(cluster_gts)
            for gi in sorted(candidate_g):
                stack.append((g_set | {gi}, p_set))

        if allow_expand_pred and len(p_set) < max_merge:
            candidate_p = set()
            for gi in g_set:
                candidate_p.update(adjacency_g.get(gi, ()))
            candidate_p = (candidate_p - set(p_set)) & set(cluster_preds)
            for pi in sorted(candidate_p):
                stack.append((g_set, p_set | {pi}))

    if best_state is not None:
        return best_state

    best_pair: Optional[Tuple[List[int], List[int], float]] = None
    best_iou = 0.0
    for gi in cluster_gts:
        for pi in cluster_preds:
            iou_val = bbox_iou(gt_boxes[gi], pred_boxes[pi])
            if iou_val > best_iou:
                best_iou = iou_val
                best_pair = ([gi], [pi], iou_val)
    return best_pair if best_iou > 0.0 else None


def compute_matches(
    gt_boxes: Sequence[Sequence[float]],
    pred_boxes: Sequence[Sequence[float]],
    allow_merge: bool,
    max_merge: int,
    limit_merge: bool,
) -> Tuple[List[Dict[str, object]], Dict[int, List[int]], Dict[int, List[int]], List[int], List[int]]:
    unmatched_gt = set(range(len(gt_boxes)))
    unmatched_pred = set(range(len(pred_boxes)))
    gt_overlap, pred_overlap = _build_overlap_maps(gt_boxes, pred_boxes)

    matches: List[Dict[str, object]] = []
    gt_to_pred: Dict[int, List[int]] = {}
    pred_to_gt: Dict[int, List[int]] = {}

    while unmatched_gt and unmatched_pred:
        start_gt = next((gi for gi in unmatched_gt if any(pi in unmatched_pred for pi in gt_overlap.get(gi, []))), None)
        start_pred = next((pi for pi in unmatched_pred if any(gi in unmatched_gt for gi in pred_overlap.get(pi, []))), None)

        if start_gt is None and start_pred is None:
            break

        stack: List[Tuple[str, int]] = []
        if start_gt is not None:
            stack.append(("gt", start_gt))
        elif start_pred is not None:
            stack.append(("pred", start_pred))

        cluster_gts: set[int] = set()
        cluster_preds: set[int] = set()
        visited_gt: set[int] = set()
        visited_pred: set[int] = set()

        while stack:
            typ, idx = stack.pop()
            if typ == "gt":
                if idx in visited_gt or idx not in unmatched_gt:
                    continue
                visited_gt.add(idx)
                cluster_gts.add(idx)
                for pi in gt_overlap.get(idx, []):
                    if pi in unmatched_pred:
                        stack.append(("pred", pi))
            else:
                if idx in visited_pred or idx not in unmatched_pred:
                    continue
                visited_pred.add(idx)
                cluster_preds.add(idx)
                for gi in pred_overlap.get(idx, []):
                    if gi in unmatched_gt:
                        stack.append(("gt", gi))

        if not cluster_gts or not cluster_preds:
            break

        best = _enumerate_cluster_matches(
            cluster_gts,
            cluster_preds,
            gt_boxes,
            pred_boxes,
            allow_merge,
            max_merge,
            limit_merge,
        )
        if best is None:
            break

        gt_subset, pred_subset, iou_val = best
        matches.append({"gt_indices": gt_subset, "pred_indices": pred_subset, "iou": iou_val})

        for gi in gt_subset:
            unmatched_gt.discard(gi)
            gt_to_pred.setdefault(gi, []).extend(pred_subset)
        for pi in pred_subset:
            unmatched_pred.discard(pi)
            pred_to_gt.setdefault(pi, []).extend(gt_subset)

    if matches and (unmatched_pred or unmatched_gt):
        for pi in list(unmatched_pred):
            pred_box = pred_boxes[pi]
            best_idx = None
            best_ratio = 0.0
            for idx_match, match in enumerate(matches):
                if not match['gt_indices']:
                    continue
                ratios = [
                    _overlap_fraction(pred_box, gt_boxes[gi])
                    for gi in match['gt_indices']
                ]
                gt_union = union_box(gt_boxes, match['gt_indices'])
                if gt_union:
                    ratios.append(_overlap_fraction(pred_box, gt_union))
                ratio = max(ratios) if ratios else 0.0
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_idx = idx_match
            if best_idx is not None and best_ratio >= 0.9:
                match = matches[best_idx]
                if pi not in match['pred_indices']:
                    match['pred_indices'].append(pi)
                pred_to_gt[pi] = list(match['gt_indices'])
                for gi in match['gt_indices']:
                    gt_to_pred.setdefault(gi, [])
                    if pi not in gt_to_pred[gi]:
                        gt_to_pred[gi].append(pi)
                unmatched_pred.remove(pi)
                gt_union = union_box(gt_boxes, match['gt_indices'])
                pred_union = union_box(pred_boxes, match['pred_indices'])
                if gt_union and pred_union:
                    match['iou'] = bbox_iou(gt_union, pred_union)

        for gi in list(unmatched_gt):
            gt_box = gt_boxes[gi]
            best_idx = None
            best_ratio = 0.0
            for idx_match, match in enumerate(matches):
                if not match['pred_indices']:
                    continue
                ratios = [
                    _overlap_fraction(gt_box, pred_boxes[pi])
                    for pi in match['pred_indices']
                ]
                pred_union = union_box(pred_boxes, match['pred_indices'])
                if pred_union:
                    ratios.append(_overlap_fraction(gt_box, pred_union))
                ratio = max(ratios) if ratios else 0.0
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_idx = idx_match
            if best_idx is not None and best_ratio >= 0.9:
                match = matches[best_idx]
                if gi not in match['gt_indices']:
                    match['gt_indices'].append(gi)
                gt_to_pred[gi] = list(match['pred_indices'])
                for pi in match['pred_indices']:
                    pred_to_gt.setdefault(pi, [])
                    if gi not in pred_to_gt[pi]:
                        pred_to_gt[pi].append(gi)
                unmatched_gt.remove(gi)
                gt_union = union_box(gt_boxes, match['gt_indices'])
                pred_union = union_box(pred_boxes, match['pred_indices'])
                if gt_union and pred_union:
                    match['iou'] = bbox_iou(gt_union, pred_union)

    return (
        matches,
        gt_to_pred,
        pred_to_gt,
        sorted(unmatched_gt),
        sorted(unmatched_pred),
    )


__all__ = [
    "bbox_iou",
    "has_overlap",
    "union_box",
    "compute_matches",
    "load_azure_words",
]


def load_azure_words(
    doc_name: str,
    page_index: int,
    root: Path,
    page_width: Optional[float] = None,
    page_height: Optional[float] = None,
) -> List[List[float]]:
    stem = Path(doc_name).stem.split('_')[0]
    json_path = root / f"{stem}_ocr_result.json"
    if not json_path.exists():
        return []
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    target_page = page_index + 1

    if isinstance(data, list):
        pages = data
    else:
        pages = data.get("pages") or data.get("analysisResult", {}).get("readResults") or []

    if not pages:
        return []

    def resolve_page_number(entry: Any) -> Optional[int]:
        if isinstance(entry, dict):
            for key in ("pageNumber", "page", "number", "id"):
                if key in entry:
                    value = entry[key]
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        try:
                            return int(str(value).split("_")[-1])
                        except (TypeError, ValueError):
                            continue
        return None

    page: Optional[Dict[str, Any]] = None

    if isinstance(pages, dict):
        page = pages.get(str(target_page)) or pages.get(target_page)
        if page is None:
            for candidate in pages.values():
                if resolve_page_number(candidate) == target_page:
                    page = candidate
                    break
    else:
        for candidate in pages:
            if resolve_page_number(candidate) == target_page:
                page = candidate
                break
        if page is None and 0 <= page_index < len(pages):
            page = pages[page_index]
            print("forced")
    if not page:
        return []

    width = page.get("width") or 1.0
    height = page.get("height") or 1.0
    scale_x = float(page_width) / float(width) if page_width else 1.0
    scale_y = float(page_height) / float(height) if page_height else 1.0
    words = []
    for line in page.get("lines", []):
        for word in line.get("words", []):
            bbox = word.get("boundingBox") or []
            if len(bbox) == 8:
                xs = bbox[0::2]
                ys = bbox[1::2]
                x1 = min(xs) * scale_x
                y1 = min(ys) * scale_y
                x2 = max(xs) * scale_x
                y2 = max(ys) * scale_y
                words.append([x1, y1, x2, y2])
    return words
