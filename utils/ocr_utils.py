# revised from https://github.com/opendatalab/MinerU/blob/7f0fe20004af7416db886f4b75c116bcc1c986b4/magic_pdf/pdf_parse_union_core.py#L177
# from fast_langdetect import detect_language
# import unicodedata
import re


def __is_overlaps_y_exceeds_threshold(bbox1, bbox2, overlap_ratio_threshold=0.8):
    """Check if two bboxes overlap on y-axis and if the overlap height exceeds 80% of the shorter bbox height"""
    _, y0_1, _, y1_1 = bbox1
    _, y0_2, _, y1_2 = bbox2

    overlap = max(0, min(y1_1, y1_2) - max(y0_1, y0_2))
    height1, height2 = y1_1 - y0_1, y1_2 - y0_2
    max_height = max(height1, height2)
    min_height = min(height1, height2)

    return (overlap / min_height) > overlap_ratio_threshold

def merge_spans_to_line(spans):
    if len(spans) == 0:
        return []
    else:
        # Sort by y0 coordinate
        spans.sort(key=lambda span: span['bbox'][1])

        lines = []
        current_line = [spans[0]]
        for span in spans[1:]:
            # If current span type is "interline_equation" or current line contains "interline_equation"
            # Same for image and table types
            if span['type'] in ['interline_equation'] or any(
                    s['type'] in ['interline_equation'] for s in
                    current_line):
                # Start a new line
                lines.append(current_line)
                current_line = [span]
                continue

            # If current span overlaps with the last span in current line on y-axis, add to current line
            if __is_overlaps_y_exceeds_threshold(span['bbox'], current_line[-1]['bbox']):
                current_line.append(span)
            else:
                # Otherwise, start a new line
                lines.append(current_line)
                current_line = [span]

        # Add the last line
        if current_line:
            lines.append(current_line)

        return lines
    
# Sort spans in each line from left to right
def line_sort_spans_by_left_to_right(lines):
    line_objects = []
    for line in lines:
        # Sort by x0 coordinate
        line.sort(key=lambda span: span['bbox'][0])
        line_bbox = [
            min(span['bbox'][0] for span in line),  # x0
            min(span['bbox'][1] for span in line),  # y0
            max(span['bbox'][2] for span in line),  # x1
            max(span['bbox'][3] for span in line),  # y1
        ]
        line_objects.append({
            "bbox": line_bbox,
            "spans": line,
        })
    return line_objects

def fix_text_block(block):
    # Formula spans in text block should be converted to inline type
    block_lines = merge_spans_to_line(block['spans'])
    sort_block_lines = line_sort_spans_by_left_to_right(block_lines)
    block['lines'] = sort_block_lines
    del block['spans']
    return block


# def detect_lang(text: str) -> str:

#     if len(text) == 0:
#         return ""
#     try:
#         lang_upper = detect_language(text)
#     except:
#         html_no_ctrl_chars = ''.join([l for l in text if unicodedata.category(l)[0] not in ['C', ]])
#         lang_upper = detect_language(html_no_ctrl_chars)
#     try:
#         lang = lang_upper.lower()
#     except:
#         lang = ""
#     return lang

def detect_lang(string):
    """
    Check if the string contains Chinese characters
    :param string: String to check
    :return: bool
    """
    
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return 'zh'
    return 'en'

def ocr_escape_special_markdown_char(content):
    """
    Escape special markdown characters in content
    """
    special_chars = ["*", "`", "~", "$"]
    for char in special_chars:
        content = content.replace(char, "\\" + char)

    return content

# def split_long_words(text):
#     segments = text.split(' ')
#     for i in range(len(segments)):
#         words = re.findall(r'\w+|[^\w]', segments[i], re.UNICODE)
#         for j in range(len(words)):
#             if len(words[j]) > 15:
#                 words[j] = ' '.join(wordninja.split(words[j]))
#         segments[i] = ''.join(words)
#     return ' '.join(segments)


def merge_para_with_text(para_block):
    para_text = ''
    for line in para_block['lines']:
        line_text = ""
        line_lang = ""
        for span in line['spans']:
            span_type = span['type']
            if span_type == "text":
                line_text += span['content'].strip()
        if line_text != "":
            line_lang = detect_lang(line_text)
        for span in line['spans']:
            span_type = span['type']
            content = ''
            if span_type == "text":
                content = span['content']
                content = ocr_escape_special_markdown_char(content)
                # language = detect_lang(content)
                # if language == 'en':  # Only split long words for English text, Chinese word splitting will lose text
                    # content = ocr_escape_special_markdown_char(split_long_words(content))
                # else:
                #     content = ocr_escape_special_markdown_char(content)
            elif span_type == 'inline_equation':
                content = f" ${span['content'].strip('$')}$ "
            elif span_type == 'ignore-formula':
                content = f" ${span['content'].strip('$')}$ "
            elif span_type == 'interline_equation':
                content = f"\n$$\n{span['content'].strip('$')}\n$$\n"    
            elif span_type == 'footnote':
                content_ori = span['content'].strip('$')
                if '^' in content_ori:
                    content = f" ${content_ori}$ "
                else:
                    content = f" $^{content_ori}$ "

            if content != '':
                if 'zh' in line_lang:  # For documents with one character per span, character-level language detection is inaccurate, need to detect language for whole line
                    para_text += content.strip()  # In Chinese context, no space needed between contents
                else:
                    para_text += content.strip() + ' '  # In English context, space needed between contents
    return para_text

def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

def normalize_format(block, pred_spans):
    spans = []
    for span in pred_spans:
        spans.append({
            "type": span['category_type'],
            "bbox": poly2bbox(span['poly']),
            "content": span['text']
        })

    block_type = block["category_type"]
    block_bbox = poly2bbox(block['poly'])
    block_dict = {
        'type': block_type,
        'bbox': block_bbox,
        'spans': spans
    }
    return block_dict

def get_text_for_block(gt, pred_spans):
    '''Fix operations for block'''
    block_with_spans = normalize_format(gt, pred_spans)
    para_block = fix_text_block(block_with_spans)
    pred_text = merge_para_with_text(para_block)
    return pred_text