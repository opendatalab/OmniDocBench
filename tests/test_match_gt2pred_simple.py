from src.core.matching.match import match_gt2pred_simple


def test_match_gt2pred_simple_keeps_metadata_for_pred_index_zero():
    gt_items = [
        {
            "category_type": "table",
            "html": "<table><tr><td>A</td></tr></table>",
            "order": 2,
            "attribute": {},
        }
    ]
    pred_items = [
        {
            "category_type": "html_table",
            "content": "<table><tr><td>A</td></tr></table>",
            "position": [2, 3],
        }
    ]

    matches, unmatched = match_gt2pred_simple(gt_items, pred_items, "html_table", "mini.png")

    assert unmatched is None
    assert matches[0]["pred_idx"] == [0]
    assert matches[0]["edit"] == 0
    assert matches[0]["pred_category_type"] == "html_table"
    assert matches[0]["pred_position"] == 2
