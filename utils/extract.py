import re
import os
import json
import copy
#from  modules.table_utils import convert_markdown_to_html #end
from  utils.table_utils import convert_markdown_to_html
import re
import unicodedata
from bs4 import BeautifulSoup
from pylatexenc.latexencode import unicode_to_latex
# from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexwalker import LatexWalker, LatexEnvironmentNode, LatexCharsNode, LatexGroupNode, LatexMacroNode, LatexSpecialsNode
from collections import defaultdict
import pdb


def extract_tabular(text):
    begin_pattern = r'\\begin{tabular}'
    end_pattern = r'\\end{tabular}'

    tabulars = []
    positions = []
    current_pos = 0
    stack = []
    
    while current_pos < len(text):
        begin_match = re.search(begin_pattern, text[current_pos:])
        end_match = re.search(end_pattern, text[current_pos:])
        
        if not begin_match and not end_match:
            break
            
        if begin_match and (not end_match or begin_match.start() < end_match.start()):
            stack.append(current_pos + begin_match.start())
            current_pos += begin_match.start() + len(end_pattern)
        elif end_match:
            if stack:
                start_pos = stack.pop()
                if not stack:
                    end_pos = current_pos + end_match.start() + len(end_pattern)
                    tabular_code = text[start_pos:end_pos]
                    tabulars.append(tabular_code)
                    positions.append((start_pos, end_pos))
            current_pos += end_match.start() + len(end_pattern)
        else:
            current_pos += 1
    
    if stack:
        new_start = stack[0] + len(begin_pattern)
        new_tabulars, new_positions = extract_tabular(text[new_start:])
        new_positions = [(start + new_start, end + new_start) for start, end in new_positions]
        tabulars.extend(new_tabulars)
        positions.extend(new_positions)

    return tabulars, positions

# math reg
display_reg = re.compile(
    r'\\begin{equation\*?}(.*?)\\end{equation\*?}|'
    r'\\begin{align\*?}(.*?)\\end{align\*?}|'
    r'\\begin{gather\*?}(.*?)\\end{gather\*?}|'
    r'\$\$(.*?)\$\$|'
    r'\\\[(.*?)\\\]',
    re.DOTALL
)
# inline_reg = re.compile(
#     r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)|'
#     r'\\\((.*?)\\\)',
# )
inline_reg = re.compile(
    r'\$(.*?)\$|'
    r'\\\((.*?)\\\)',
)

# table 
table_reg = re.compile(
    r'\\begin{table\*?}(.*?)\\end{table\*?}|'
    r'\\begin{tabular\*?}(.*?)\\end{tabular\*?}',
    re.DOTALL 
)
md_table_reg = re.compile(
    r'\|\s*.*?\s*\|\n', 
    re.DOTALL)
html_table_reg = re.compile(
    r'(<table.*?</table>)',
    re.DOTALL
)

# title
title_reg = re.compile(
    r'^\s*#.*$', 
    re.MULTILINE)

# img
img_pattern = r'!\[.*?\]\(.*?\)'

# code block
code_block_reg = re.compile(
    r'```(\w+)\n(.*?)```',
    re.DOTALL
)

def remove_markdown_fences(content):
    content = re.sub(r'^```markdown\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'```\n?$', '', content, flags=re.MULTILINE)
    return content.strip()  

# 标准化连续下划线
def standardize_underscores(content):
    content = re.sub(r'_{5,}', '____', content)
    return content

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

# 定义要替换的Unicode字符和替换后的内容的字典
unicode_replacements = {
    "\u00A9": r"$\copyright$",  # 版权符号©替换为latex
    "\u00AE": r"$^\circledR$",  # 注册商标符号®替换为latex
    "\u2122": r"$^\text{TM}$",   # 商标符号™替换latex
    "\u2018": "'",             # 左单引号转直引号
    "\u2019": "'",             # 右单引号转直引号
    "\u201C": "\"",            # 左双引号转直双引号
    "\u201D": "\"",            # 右双引号转直双引号
    "\u2013": "-",             # 短破折号转连字符
    "\u2014": "-",             # 长破折号转连字符
    "\u2026": "...",           # Unicode 省略号转三个点
    "\u2103": r"$\textdegree C$",  # ℃
    "\u03B1": r"$\alpha$",         # α
    "\u03B2": r"$\beta$",          # β
    "\u03A3": r"$\Sigma$",         # Σ
}

# 使用正则表达式替换Unicode字符
def replace_unicode(match):
    char = match.group(0)
    return unicode_replacements.get(char, char)

def md_tex_filter(content):
    '''
    Input: 1 page md or tex content - String
    Output: text, display, inline, table, title, code - list
    '''

    content = re.sub(img_pattern, '', content)  # 去除图片
    content = remove_markdown_fences(content)   # 去除开头的markdown标记，若有
    content = standardize_underscores(content) # 下划线标准化处理
    
    # # 使用正则表达式对unicode进行替换
    # special_unicode = ''.join(unicode_replacements.keys())
    # content = re.sub(f'[{special_unicode}]', replace_unicode, content)

    # content = fullwidth_to_halfwidth(content)  # 全角转半角，TODO: GT也需要做这个操作

    # # pylatexenc的unicode转latex
    # content = unicode_to_latex(content, unknown_char_warning=False)
    # markdown_table_content[i, j] = LatexNodes2Text().latex_to_text(content_str)
    # content_ori = copy.deepcopy(content)

    # print('--------------After pre_process: \n', content)

    pred_all = []

    # 提取latex表格 
    latex_table_array, table_positions = extract_tex_table(content)
    for latex_table, position in zip(latex_table_array, table_positions):
        position = [position[0], position[0]+len(latex_table)]   # !!!
        pred_all.append({
            'category_type': 'latex_table',
            'position': position,  # 只记录start
            'content': latex_table
        })
        content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格

    # print('--------After latex table: \n', content)
    # print('-------latex_table_array: \n', latex_table_array)
    
    # 按照位置顺序从后向前删除，以免影响未处理的起始位置
    # for start, end in sorted(table_positions, reverse=True):
        # content = content[:start] + content[end:]

    # 提取html表格
    html_table_array, table_positions = extract_html_table(content)
    for html_table, position in zip(html_table_array, table_positions):
        position = [position[0], position[0]+len(html_table)]
        pred_all.append({
            'category_type': 'html_table',
            'position': position,
            'content': html_table
        })
        content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
    # html_table_array = []
    # html_table_matches = html_table_reg.finditer(content)
    # if html_table_matches:
    #     for match in html_table_matches:
    #         matched = match.group(0)
    #         position = [match.start(), match.end()]
    #         html_table_array.append(matched.strip())
    #         # content = content.replace(matched, ' '*len(matched)) # 替换成空格
    #         content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
    #         pred_all.append({
    #             'category_type': 'html_table',
    #             'position': position,
    #             'content': matched.strip()
    #         })

    # print('--------------After html table: \n', content)
    # # extract tables in latex and html
    # table_array = []
    # table_matches = table_reg.finditer(content)
    # tables = ""
    # for match in table_matches:
    #     matched = match.group(0)
    #     if matched:
    #         tables += matched
    #         tables += "\n\n"
    #         table_array.append(matched)
    #         content = content.replace(matched, '')
  
    # extract interline formula
    display_matches = display_reg.finditer(content)
    display_array = []
    for match in display_matches:
        matched = match.group(0)
        if matched:
            single_line = ''.join(matched.split())
            position = [match.start(), match.end()]
            # replace $$ with \[\]
            dollar_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
            single_line = re.sub(dollar_pattern, r'\\[\1\\]', single_line)
            # print('single_line: ', single_line)
            display_array.append(single_line)
            # content = content.replace(matched, ' '*len(matched))
            content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
            pred_all.append({
                'category_type': 'equation_isolated',
                'position': position,
                'content': single_line
            })
            # print('-----Found display formula: ', matched)

    # print('-------------After display: \n', content)

    # extract md table with ||
    md_table_mathces = md_table_reg.findall(content)        
    if md_table_mathces:
        # print("md table found!")
        # print("content:", content)
        content = convert_markdown_to_html(content)
        # print('content after converting md table to html:', content)
        html_table_matches = html_table_reg.finditer(content)
        if html_table_matches:
            for match in html_table_matches:
                matched = match.group(0)
                position = [match.start(), match.end()]
                html_table_array.append(matched.strip())
                # content = content.replace(match, '')
                # print('content after removing the md table:', content)
                content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
                pred_all.append({
                    'category_type': 'html_table',
                    'position': position,
                    'content': matched.strip(),
                    'fine_category_type': 'md2html_table'
                })
    
    # print('---------After md table: \n', content)

    # extract code blocks
    code_array = []
    code_matches = code_block_reg.finditer(content)
    if code_matches:
        for match in code_matches:
            position = [match.start(), match.end()]
            language = match.group(1)
            code = match.group(2).strip()
            code_array.append({'language': language, 'code': code})
            # content = content.replace(match.group(0), '')
            content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
            pred_all.append({
                'category_type': 'text_all',
                'position': position,
                'content': code,
                'language': language,
                'fine_category_type': 'code'
            })

    # print('-------After code block: \n', content)

    # extract titles
    title_matches = title_reg.finditer(content)
    title_array =[]
    if title_matches:
        for match in title_matches:
            position = [match.start(), match.end()]
            matched = match.group(0)
            title_array.append(matched.strip('\n').strip('#').strip(' '))
            # content = content.replace(match, '')
            # print('content after removing the titles:', content)
            content = content[:position[0]] + ' '*(position[1]-position[0]) + content[position[1]:]  # 把表格的内容替换成空格
            pred_all.append({
                'category_type': 'text_all',
                'position': position,
                'content': matched.strip('\n').strip('#').strip(' '),
                'fine_category_type': 'title'
            })
    
    # print('----------After title: \n', content)

    # extract texts
    res = content.split('\n\n')
    text_array = []

    content_position = 0
    for text in res:
        position = [content_position, content_position+len(text)]
        content_position += len(text)
        text = text.strip()
        text = text.strip('\n')
        if text:  # Check if the stripped text is not empty
            if text.startswith('<table') and text.endswith('</table>'):
                html_table_array.append(text)
                pred_all.append({
                    'category_type': 'html_table',
                    'position': position,
                    'content': text,
                })
            elif text.startswith('#') and '\n' not in text:
                title_array.append(text)
                pred_all.append({
                    'category_type': 'text_all',
                    'position': position,
                    'content': text,
                    'fine_category_type': 'title'
                })
            elif text.startswith('$') and text.endswith('$'):
                display_array.append(text)
                pred_all.append({
                    'category_type': 'equation_isolated',
                    'position': position,
                    'content': text,
                })
            else:
                text_array.append(text)
                pred_all.append({
                    'category_type': 'text_all',
                    'position': position,
                    'content': text,
                    'fine_category_type': 'text_block'
                })
                # if '$' in text:
                #     for formula in re.findall(r'\$(.*?)\$', text):
                #         formula_array.append(formula)

    pred_dataset = defaultdict(list)
    pred_all = sorted(pred_all, key=lambda x: x['position'][0])
    for item in pred_all:
        pred_dataset[item['category_type']].append(item)
        
    return pred_dataset


# def replace_or_extract(match):
#     content = match.group(1) if match.group(1) is not None else match.group(2)
    
#     if any(char in content for char in r'\^_'):
#         inline_array.append(match.group(0))
#         return ''
#     else:
#         return content

# extract inline math equations in text
# def inline_filter(text):

#     inline_array = []
#     inline_matches = inline_reg.finditer(text)
#     for match in inline_matches:
#         content = match.group(1) if match.group(1) is not None else match.group(2)
        
#         # remove \\, \_, \&, \%, \^
#         clean_content = re.sub(r'\\([\\_&%^])', '', content)

#         if any(char in clean_content for char in r'\^_'):
#             inline_array.append(match.group(0))
#             text = text.replace(match.group(0), '')
#         else:
#             text = text.replace(match.group(0), content)

#     return text, inline_array


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

# def extract_tex_table(content):
#     tables = []
#     positions = []

#     walker = LatexWalker(content)
#     nodes, _, _ = walker.get_latex_nodes()
#     if nodes is None:
#         return tables, positions

#     for node in nodes:
#         if isinstance(node, LatexEnvironmentNode) and (
#             node.environmentname == 'tabular' or node.environmentname == 'table'):
#             # table_latex = extract_node_content(node)
#             table_latex = content[node.pos:node.pos_end]
#             tables.append(table_latex)
#             start_pos = node.pos
#             end_pos = get_node_end_pos(node)
#             positions.append((start_pos, end_pos))

#     return tables, positions

def extract_tex_table(content):
    tables = []
    tables_positions = []

    pattern = r'\\begin{table}(.*?)\\end{table}'
    for match in re.finditer(pattern, content, re.DOTALL):
        start_pos = match.start()
        end_pos = match.end()
        table_content = match.group(0)
        tables.append(table_content)
        tables_positions.append((start_pos, end_pos))
        content = content[:start_pos] + ' '*(end_pos-start_pos) + content[end_pos:]

    tabulars, tabular_positions = extract_tabular(content)
    all_tables = tables + tabulars
    all_positions = tables_positions + tabular_positions

    all_result = sorted([[pos, table]for pos, table in zip(all_positions, all_tables)], key=lambda x: x[0][0])
    all_tables = [x[1] for x in all_result]
    all_positions = [x[0] for x in all_result]

    return all_tables, all_positions

def extract_html_table(content):
    soup = BeautifulSoup(content, 'html.parser')
    all_tables = soup.find_all('table')
    tables = []
    positions = []
    
    for table in all_tables:
        if table.find_parent('table') is None:
            table_str = str(table)
            start_pos = content.find(table_str)
            end_pos = start_pos + len(table_str)
            
            tables.append(table_str)
            positions.append((start_pos, end_pos))
    return tables, positions


def extract_node_content(node):
    """ 递归提取LatexEnvironmentNode的内容，重建表格的LaTeX表示 """
    if isinstance(node, LatexCharsNode):
        return node.chars  # 使用 chars 属性
    elif isinstance(node, LatexGroupNode):
        return "{" + "".join(extract_node_content(n) for n in node.nodelist) + "}"
    elif isinstance(node, LatexMacroNode):
        # 提取宏命令及其参数
        macro_content = "\\" + node.macroname
        if node.nodeargs:
            macro_content += "".join([extract_node_content(arg) for arg in node.nodeargs])
        return macro_content
    elif isinstance(node, LatexEnvironmentNode):
        # 提取环境，保留环境名和参数
        content = "\\begin{" + node.environmentname + "}"
        if node.nodeargd and node.nodeargd.argnlist:
            # content += "".join("{" + extract_node_content(arg) + "}" for arg in node.nodeargd)
            # content += "".join("{" + extract_node_content(node.nodeargd) + "}")
            content += "{" + extract_node_content(node.nodeargd.argnlist[0]) + "}"
        if node.nodelist:
            content += "".join(extract_node_content(n) for n in node.nodelist)
        content += "\\end{" + node.environmentname + "}"
        return content
    elif isinstance(node, LatexSpecialsNode):  # 修改为 LatexSpecialsNode
        return node.specials_chars
    else:
        return ""
        
def get_node_end_pos(node):
    """递归确定节点的结束位置"""
    if hasattr(node, 'nodelist') and node.nodelist:
        # 如果节点有子节点，则递归查找最后一个子节点的结束位置
        return get_node_end_pos(node.nodelist[-1])
    elif hasattr(node, 'pos_end'):
        # 如果节点有 pos_end 属性，直接返回
        return node.pos_end
    else:
        # 如果没有子节点，则假设该节点结束于其内容的最后一个字符
        return node.pos + len(str(node))

def remove_tex_table(content):
    tables, positions = extract_tex_table(content)

    # 按照位置顺序从后向前删除，以免影响未处理的起始位置
    for start, end in sorted(positions, reverse=True):
        content = content[:start] + content[end:]  # 删除表格内容

    return content