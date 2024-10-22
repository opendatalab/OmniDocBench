import re
import os
import json
from utils.table_utils import convert_markdown_to_html

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


def md_tex_filter(content):
    '''
    Input: 1 page md or tex content - String
    Output: text, display, inline, table, title - list
    '''

    content = re.sub(img_pattern, '', content)

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
        # print("md table found!")
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


    return text_array, display_array, table_array, title_array


# def replace_or_extract(match):
#     content = match.group(1) if match.group(1) is not None else match.group(2)
    
#     if any(char in content for char in r'\^_'):
#         inline_array.append(match.group(0))
#         return ''
#     else:
#         return content

# extract inline math equations in text
def inline_filter(text):

    inline_array = []
    inline_matches = inline_reg.finditer(text)
    for match in inline_matches:
        content = match.group(1) if match.group(1) is not None else match.group(2)
        
        # remove \\, \_, \&, \%, \^
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            inline_array.append(match.group(0))
            text = text.replace(match.group(0), '')
        else:
            text = text.replace(match.group(0), content)

    return text, inline_array


