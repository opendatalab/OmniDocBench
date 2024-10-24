import re
import os
import json
#from  modules.table_utils import convert_markdown_to_html #end
from  table_utils import convert_markdown_to_html
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

def md_tex_filter(content):
    '''
    Input: 1 page md or tex content - String
    Output: text, display, inline, table, title, code - list
    '''
    content = re.sub(img_pattern, '', content)
    content=remove_markdown_fences(content)
    content = standardize_underscores(content) 
    # extract tables in latex and html
    table_array = []
    table_matches = table_reg.finditer(content)
    tables = ""
    for match in table_matches:
        matched = match.group(0)
        if matched:
            tables += matched
            tables += "\n\n"
            table_array.append(matched)
            content = content.replace(matched, '')
  
    # extract interline formula
    display_matches = display_reg.finditer(content)
    display_array = []
    for match in display_matches:
        matched = match.group(0)
        if matched:
            single_line = ''.join(matched.split())
            # replace $$ with \[\]
            dollar_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
            single_line = re.sub(dollar_pattern, r'\\[\1\\]', single_line)
            display_array.append(single_line)
            content = content.replace(matched, '')

    # extract md table with ||
    md_table_mathces = md_table_reg.findall(content)        
    if md_table_mathces:
        print("md table found!")
        # print("content:", content)
        content = convert_markdown_to_html(content)
        # print('content after converting md table to html:', content)
        html_table_matches = html_table_reg.findall(content)
        if html_table_matches:
            for match in html_table_matches:
                table_array.append(match.strip())
                content = content.replace(match, '')
                # print('content after removing the md table:', content)

    # extract titles
    title_matches = title_reg.findall(content)
    title_array =[]
    if title_matches:
        for match in title_matches:
            title_array.append(match.strip('\n').strip('#').strip(' '))
            content = content.replace(match, '')
            # print('content after removing the titles:', content)
    
    # extract texts
    res = content.split('\n\n')
    text_array = []

    for text in res:
        text = text.strip()
        text = text.strip('\n')
        if text:  # Check if the stripped text is not empty
            if text.startswith('<table') and text.endswith('</table>'):
                table_array.append(text)
            elif text.startswith('#') and '\n' not in text:
                title_array.append(text)
            # elif text.startswith('$') and text.endswith('$'):
            #     formula_array.append(text)
            else:
                text_array.append(text)
                # if '$' in text:
                #     for formula in re.findall(r'\$(.*?)\$', text):
                #         formula_array.append(formula)

    # extract code blocks
    code_array = []
    code_matches = code_block_reg.finditer(content)
    for match in code_matches:
        language = match.group(1)
        code = match.group(2).strip()
        code_array.append({'language': language, 'code': code})
        content = content.replace(match.group(0), '')
        
    return text_array, display_array, table_array, title_array, code_array


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
        content = match.group(1) if match.group(1) is not None else match.group(2)
        
        # 移除转义字符 \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            inline_array.append(match.group(0))
            text = text.replace(match.group(0), '')
        else:
            text = text.replace(match.group(0), content)

    return text, inline_array

# 提取循环嵌套表
def extract_tex_table(content):
    walker = LatexWalker(content)
    nodes, _, _ = walker.get_latex_nodes()

    tables = []  # 用于存储提取的表格
    positions = []  # 用于存储表格的起始和结束位置

    # 遍历节点，查找所有 'tabular' 环境
    for node in nodes:
        if isinstance(node, LatexEnvironmentNode) and node.environmentname == 'tabular':
            table_latex = extract_node_content(node)
            tables.append(table_latex)
            start_pos = node.pos  # 表格的起始位置
            end_pos = get_node_end_pos(node)  # 获取表格的结束位置
            positions.append((start_pos, end_pos))  # 记录表格的起始和结束位置

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
        if node.nodeargd:
            # content += "".join("{" + extract_node_content(arg) + "}" for arg in node.nodeargd)
            content += "".join("{" + extract_node_content(node.nodeargd) + "}")
        if node.nodelist:
            content += "".join(extract_node_content(n) for n in node.nodelist)
        content += "\\end{" + node.environmentname + "}"
        return content
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