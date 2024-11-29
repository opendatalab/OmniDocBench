import re
import unicodedata
from pylatexenc.latex2text import LatexNodes2Text
import concurrent.futures
import time

def remove_markdown_fences(content):
    content = re.sub(r'^```markdown\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'```\n?$', '', content, flags=re.MULTILINE)
    return content

# Standardize all consecutive characters
def replace_repeated_chars(input_str):
    input_str = re.sub(r'_{4,}', '____', input_str) # Replace more than 4 consecutive underscores with 4 underscores
    input_str = re.sub(r' {4,}', '    ', input_str)   # Replace more than 4 consecutive spaces with 4 spaces
    return re.sub(r'([^a-zA-Z0-9])\1{10,}', r'\1\1\1\1', input_str) # For other consecutive symbols (except numbers and letters), replace more than 10 occurrences with 4

# Special Unicode handling
def fullwidth_to_halfwidth(s):
    result = []
    for char in s:
        code = ord(char)
        # Convert full-width space to half-width space
        if code == 0x3000:
            code = 0x0020
        # Convert other full-width characters to half-width
        elif 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        result.append(chr(code))
    return ''.join(result)

def find_special_unicode(s):
    special_chars = {}
    for char in s:
        if ord(char) > 127:  # Non-ASCII characters
            # unicode_name = unicodedata.name(char, None)
            unicode_name = unicodedata.category(char)
            special_chars[char] = f'U+{ord(char):04X} ({unicode_name})'
    return special_chars

# # Define dictionary for Unicode character replacements
# unicode_replacements = {
#     "\u00A9": r"$\copyright$",  # Copyright symbol © to latex
#     "\u00AE": r"$^\circledR$",  # Registered trademark ® to latex
#     "\u2122": r"$^\text{TM}$",   # Trademark ™ to latex
#     "\u2018": "'",             # Left single quote to straight quote
#     "\u2019": "'",             # Right single quote to straight quote
#     "\u201C": "\"",            # Left double quote to straight quote
#     "\u201D": "\"",            # Right double quote to straight quote
#     "\u2013": "-",             # En dash to hyphen
#     "\u2014": "-",             # Em dash to hyphen
#     "\u2026": "...",           # Unicode ellipsis to three dots
#     "\u2103": r"$\textdegree C$",  # ℃
#     "\u03B1": r"$\alpha$",         # α
#     "\u03B2": r"$\beta$",          # β
#     "\u03A3": r"$\Sigma$",         # Σ
# }

# # Use regex to replace Unicode characters
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
        # Remove escape characters \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        try:
            if any(char in clean_content for char in r'\^_'):
                if clean_content.endswith('\\'):
                    clean_content += ' '
                # inline_array.append(match.group(0))
                unicode_content = LatexNodes2Text().latex_to_text(clean_content)
                removal_positions.append((position[0], position[1], unicode_content))
        except:
            continue
    
    # Remove inline formulas from original text
    for start, end, unicode_content in sorted(removal_positions, reverse=True):
        text = text[:start] + unicode_content.strip() + text[end:]

    return text

def normalized_formula(text):
    # Normalize math formulas before matching
    filter_list = ['\\mathbf', '\\mathrm', '\\mathnormal', '\\mathit', '\\mathbb', '\\mathcal', '\\mathscr', '\\mathfrak', '\\mathsf', '\\mathtt', 
                   '\\textbf', '\\text', '\\boldmath', '\\boldsymbol', '\\operatorname', '\\bm',
                   '\\symbfit', '\\mathbfcal', '\\symbf', '\\scriptscriptstyle', '\\notag',
                   '\\setlength', '\\coloneqq', '\\space', '\\thickspace', '\\thinspace', '\\medspace', '\\nobreakspace', '\\negmedspace',
                   '\\quad', '\\qquad', '\\enspace', '\\substackw', ' ']
                #    '\\left', '\\right', '{', '}', ' ']
    
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
    
    # Remove inline formulas from original text
    for start, end, norm_content in sorted(removal_positions, reverse=True):
        text = text[:start] + norm_content.strip() + text[end:]

    return text

# def inline_filter_unicode(text):
#     # Ensure text is string type
#     if not isinstance(text, str):
#         text = str(text)
    
#     # Convert LaTeX content to Unicode representation
#     text = LatexNodes2Text().latex_to_text(text)
    
#     inline_array = []
#     inline_matches = inline_reg.finditer(text)
    
#     for match in inline_matches:
#         position = [match.start(), match.end()]
#         content = match.group(1) if match.group(1) is not None else match.group(2)
        
#         # Remove escape characters \
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
#         # # Add to inline_array
#         # inline_array.append({
#         #     'category_type': 'equation_inline',
#         #     'position': position,
#         #     'content': content,
#         # })
        
#         # # Remove matched formula from original text, can choose to replace with spaces or remove directly
#         # text = text[:position[0]] + ' '*(position[1]-position[0]) + text[position[1]:]

#     return text, inline_array

def inline_filter_unicode(text):
    # Ensure text is string type
    if not isinstance(text, str):
        text = str(text)
    
    # Replace inline formula boundary markers
    #print('--------text-------',text)
    placeholder = '__INLINE_FORMULA_BOUNDARY__'
    text_copy = text.replace('$', placeholder).replace('\\(', placeholder).replace('\\)', placeholder)
    #print('--------text_copy-------',text_copy)
    # Convert LaTeX content to Unicode representation
    text_copy = LatexNodes2Text().latex_to_text(text_copy)
    #print('--------text_copy---unicode----',text_copy)
    # Restore boundary markers
    text_copy = text_copy.replace(placeholder, '$')
    
    inline_array = []
    inline_matches = inline_reg.finditer(text_copy)
    # Record positions of inline formulas to be removed
    removal_positions = []
    
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        print('-------- content-------', content)
        # Remove escape characters \
        clean_content = re.sub(r'\\([\\_&%^])', '', content)

        if any(char in clean_content for char in r'\^_'):
            # inline_array.append(match.group(0))
            inline_array.append({
                'category_type': 'equation_inline',
                'position': position,
                'content': content,
            })
            removal_positions.append((position[0], position[1]))
    
    # Remove inline formulas from original text
    for start, end in sorted(removal_positions, reverse=True):
        text = text[:start] + text[end:]

    return text, inline_array

def inline_filter(text):
    # Ensure text is string type
    if not isinstance(text, str):
        text = str(text)
    
    inline_array = []
    inline_matches = inline_reg.finditer(text)
    
    for match in inline_matches:
        position = [match.start(), match.end()]
        content = match.group(1) if match.group(1) is not None else match.group(2)
        # print('inline_content: ', content)
        
        # Remove escape characters \
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

# Text OCR quality check processing:
def clean_string(input_string):
    # Use regex to keep Chinese characters, English letters and numbers
    input_string = input_string.replace('\\t', '').replace('\\n', '').replace('\t', '').replace('\n', '').replace('/t', '').replace('/n', '')
    cleaned_string = re.sub(r'[^\w\u4e00-\u9fff]', '', input_string)
    return cleaned_string