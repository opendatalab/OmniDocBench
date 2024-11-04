import re
import unicodedata
from pylatexenc.latex2text import LatexNodes2Text
import concurrent.futures
import time

# def timed_function_single(func, *args, timeout=5, **kwargs):
#     """
#     在指定时间内执行函数，如果超时则触发其他逻辑。
#     :param func: 被执行的函数
#     :param timeout: 超时时间（秒）
#     :param args: 函数的参数
#     :param kwargs: 函数的关键字参数
#     :return: 函数返回值或超时逻辑
#     """
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(func, *args, **kwargs)
#         try:
#             return future.result(timeout=timeout)
#         except concurrent.futures.TimeoutError:
#             print(f"Function '{func.__name__}' timed out after {timeout} seconds.")
#             return None

# def timed_function(func, change_func, *args, timeout=5, print_msg="", **kwargs):
#     """
#     在指定时间内执行函数，如果超时则触发其他逻辑。
#     :param func: 被执行的函数
#     :param timeout: 超时时间（秒）
#     :param args: 函数的参数
#     :param kwargs: 函数的关键字参数
#     :return: 函数返回值或超时逻辑
#     """
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(func, *args, **kwargs)
#         try:
#             return future.result(timeout=timeout)
#         except concurrent.futures.TimeoutError:
#             print(f"Function '{func.__name__}' timed out after {timeout} seconds. The alternate Function '{change_func.__name__}' will be used.")
#             print('Input is: ', print_msg)
#             future = executor.submit(change_func, *args, **kwargs)
#             try:
#                 return future.result(timeout=timeout)
#             except concurrent.futures.TimeoutError:
#                 print(f"The alternate Function '{change_func.__name__}' timed out after {timeout} seconds. The result would be None.")
#                 print('Input is: ', print_msg)
#                 return None

def remove_markdown_fences(content):
    content = re.sub(r'^```markdown\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'```\n?$', '', content, flags=re.MULTILINE)
    return content.rstrip()

# # 标准化连续下划线和空格
# def standardize_underscores(content):
#     content = re.sub(r'_{5,}', '____', content) # 下划线
#     content = re.sub(r'\s+', ' ', content)   # 空格
#     return content

# 标准化所有连续的字符
def replace_repeated_chars(input_str):
    # content = re.sub(r'_{5,}', '____', input_str) # 下划线连续超过4个替换成4个
    input_str = re.sub(r' +', ' ', input_str)   # 空格有连续全部替换成1个
    # return re.sub(r'(.)\1{10,}', r'\1\1\1\1', input_str) # 其他连续字符超过10个的话就替换成4个
    return re.sub(r'([^a-zA-Z0-9])\1{4,}', r'\1\1\1\1', input_str)

# 特殊Unicode处理
def fullwidth_to_halfwidth(s):
    result = []
    for char in s:
        code = ord(char)
        # 全角空格转换为半角空格
        if code == 0x3000:
            code = 0x0020
        # 其他全角字符转换为半角字符
        elif 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        result.append(chr(code))
    return ''.join(result)

def find_special_unicode(s):
    special_chars = {}
    for char in s:
        if ord(char) > 127:  # 非 ASCII 字符
            # unicode_name = unicodedata.name(char, None)
            unicode_name = unicodedata.category(char)
            special_chars[char] = f'U+{ord(char):04X} ({unicode_name})'
    return special_chars

# # 定义要替换的Unicode字符和替换后的内容的字典
# unicode_replacements = {
#     "\u00A9": r"$\copyright$",  # 版权符号©替换为latex
#     "\u00AE": r"$^\circledR$",  # 注册商标符号®替换为latex
#     "\u2122": r"$^\text{TM}$",   # 商标符号™替换latex
#     "\u2018": "'",             # 左单引号转直引号
#     "\u2019": "'",             # 右单引号转直引号
#     "\u201C": "\"",            # 左双引号转直双引号
#     "\u201D": "\"",            # 右双引号转直双引号
#     "\u2013": "-",             # 短破折号转连字符
#     "\u2014": "-",             # 长破折号转连字符
#     "\u2026": "...",           # Unicode 省略号转三个点
#     "\u2103": r"$\textdegree C$",  # ℃
#     "\u03B1": r"$\alpha$",         # α
#     "\u03B2": r"$\beta$",          # β
#     "\u03A3": r"$\Sigma$",         # Σ
# }

# # 使用正则表达式替换Unicode字符
# def replace_unicode(match):
#     char = match.group(0)
#     return unicode_replacements.get(char, char)

inline_reg = re.compile(
    r'\$(.*?)\$|'
    r'\\\((.*?)\\\)',
)

def textblock2unicode(text):
    inline_matches = inline_reg.finditer(text)
    removal_positions = []
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        # print('-------- content-------', content)
        # 移除转义字符 \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            # inline_array.append(match.group(0))
            unicode_content = LatexNodes2Text().latex_to_text(clean_content)
            removal_positions.append((position[0], position[1], unicode_content))
    
    # 从原始文本中移除行内公式
    for start, end, unicode_content in sorted(removal_positions, reverse=True):
        text = text[:start] + unicode_content.strip() + text[end:]

    return text

def normalized_formula(text):
    # 把数学公式做一下norm再匹配
    filter_list = ['\\mathbf', '\\mathrm', '\\mathnormal', '\\mathit', '\\mathbb', '\\mathcal', '\\mathscr', '\\mathfrak', '\\mathsf', '\\mathtt', 
                   '\\textbf', '\\text', '\\boldmath', '\\boldsymbol', '\\operatorname', '\\bm',
                   '\\symbfit', '\\mathbfcal', '\\symbf', '\\scriptscriptstyle', '\\notag',
                   '\\setlength', '\\coloneqq', '\\space', '\\thickspace', '\\thinspace', '\\medspace', '\\nobreakspace', '\\negmedspace',
                   '\\quad', '\\qquad', '\\enspace', '\\substackw',
                   '\\left', '\\right', '{', '}', ' ']
    
    # delimiter_filter
    pattern = re.compile(r"\\\[(.+?)(?<!\\)\\\]")
    match = pattern.search(text)

    if match:
        text = match.group(1).strip()
    
    tag_pattern = re.compile(r"\\tag\{.*?\}")
    text = tag_pattern.sub('', text)
    hspace_pattern = re.compile(r"\\hspace\{.*?\}")
    text = hspace_pattern.sub('', text)
    begin_pattern = re.compile(r"\\begin\{.*?\}")
    text = begin_pattern.sub('', text)
    end_pattern = re.compile(r"\\end\{.*?\}")
    text = end_pattern.sub('', text)
    col_sep = re.compile(r"\\arraycolsep.*?\}")
    text = col_sep.sub('', text)
    text = text.strip('.')
    
    for filter_text in filter_list:
        text = text.replace(filter_text, '')
        
    # text = normalize_text(delimiter_filter(text))
    # text = delimiter_filter(text)
    text = text.lower()
    return text

def textblock_with_norm_formula(text):
    inline_matches = inline_reg.finditer(text)
    removal_positions = []
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        # print('-------- content-------', content)

        norm_content = normalized_formula(content)
        removal_positions.append((position[0], position[1], norm_content))
    
    # 从原始文本中移除行内公式
    for start, end, norm_content in sorted(removal_positions, reverse=True):
        text = text[:start] + norm_content.strip() + text[end:]

    return text

# def inline_filter_unicode(text):
#     # 确保 text 是字符串类型
#     if not isinstance(text, str):
#         text = str(text)
    
#     # 将LaTeX内容转换为Unicode表示
#     text = LatexNodes2Text().latex_to_text(text)
    
#     inline_array = []
#     inline_matches = inline_reg.finditer(text)
    
#     for match in inline_matches:
#         position = [match.start(), match.end()]
#         content = match.group(1) if match.group(1) is not None else match.group(2)
        
#         # 移除转义字符 \
#         clean_content = re.sub(r'\\([\\_&%^])', '', content)

#         if any(char in clean_content for char in r'\^_'):
#             # inline_array.append(match.group(0))
#             inline_array.append({
#                 'category_type': 'equation_inline',
#                 'position': position,
#                 'content': match.group(0),
#             })
#             text = text.replace(match.group(0), '')
#             # print('-----Found inline formula: ', match.group(0))
#         else:
#             text = text.replace(match.group(0), content)
#         # # 添加到 inline_array 中
#         # inline_array.append({
#         #     'category_type': 'equation_inline',
#         #     'position': position,
#         #     'content': content,
#         # })
        
#         # # 将匹配到的公式从原始文本中移除，这里可以选择是否替换为空格或直接移除
#         # text = text[:position[0]] + ' '*(position[1]-position[0]) + text[position[1]:]

#     return text, inline_array

def inline_filter_unicode(text):
    # 确保 text 是字符串类型
    if not isinstance(text, str):
        text = str(text)
    
    # 替换行内公式的边界标识符
    #print('--------text-------',text)
    placeholder = '__INLINE_FORMULA_BOUNDARY__'
    text_copy = text.replace('$', placeholder).replace('\\(', placeholder).replace('\\)', placeholder)
    #print('--------text_copy-------',text_copy)
    # 将LaTeX内容转换为Unicode表示
    text_copy = LatexNodes2Text().latex_to_text(text_copy)
    #print('--------text_copy---unicode----',text_copy)
    # 恢复边界标识符
    text_copy = text_copy.replace(placeholder, '$')
    
    inline_array = []
    inline_matches = inline_reg.finditer(text_copy)
    # 记录需要移除的行内公式及其位置
    removal_positions = []
    
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        print('-------- content-------', content)
        # 移除转义字符 \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            # inline_array.append(match.group(0))
            inline_array.append({
                'category_type': 'equation_inline',
                'position': position,
                'content': content,
            })
            removal_positions.append((position[0], position[1]))
    
    # 从原始文本中移除行内公式
    for start, end in sorted(removal_positions, reverse=True):
        text = text[:start] + text[end:]

    return text, inline_array

def inline_filter(text):
    # 确保 text 是字符串类型
    if not isinstance(text, str):
        text = str(text)
    
    inline_array = []
    inline_matches = inline_reg.finditer(text)
    
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        # print('inline_content: ', content)
        
        # 移除转义字符 \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            # inline_array.append(match.group(0))
            inline_array.append({
                'category_type': 'equation_inline',
                'position': position,
                'content': match.group(0),
            })
            text = text.replace(match.group(0), '')
            # print('-----Found inline formula: ', match.group(0))
        else:
            text = text.replace(match.group(0), content)

    return text, inline_array
