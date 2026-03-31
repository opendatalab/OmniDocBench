import torch
import os 
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from PIL import Image, ImageFont, ImageDraw
import json 
import re
import math 
import cv2 
import argparse
import time 
from tqdm import tqdm  # 用于显示进度条


def inference(img_url, prompt="QwenVL HTML"):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": img_url,
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt")
    inputs = inputs.to(model.device)
    
    # 模型推理
    generated_ids = model.generate(**inputs, max_new_tokens=16384, temperature=0.1, top_p=0.5, repetition_penalty=1.05)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    
    # 输出为html格式
    html_output = output_text[0]
    return html_output


def remove_lines_starting_with(text):
    lines = text.splitlines(keepends=True)
    
    filtered = []
    prefixes_to_remove = ('Z:')
    
    for line in lines:
        stripped = line.lstrip()
        if not stripped.strip():
            continue
        if stripped.startswith(prefixes_to_remove):
            continue

        filtered.append(line)  
    return "".join(filtered)

def process_code_content(content: str) -> str:
    content = content.replace('```', '')
    
    content = re.sub(r'^\s*<pre[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</pre>\s*$', '', content, flags=re.IGNORECASE)
    
    content = re.sub(r'^\s*<code[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</code>\s*$', '', content, flags=re.IGNORECASE)
    
    # 包裹在 ``` 中
    return f"```code\n{content.strip()}\n```"


def process_pseudocode_content(content: str) -> str:
    """Process pseudocode content, preserving indentation and not breaking LaTeX formulas"""

    content = content.replace('```', '')
    content = re.sub(r'^\s*<(pre|code)[^>]*>', '', content, flags=re.IGNORECASE | re.MULTILINE)
    content = re.sub(r'</(pre|code)>\s*$', '', content, flags=re.IGNORECASE | re.MULTILINE)

    # Extract and protect LaTeX formulas
    math_blocks = []
    def save_math(match):
        placeholder = f"___MATH_ID_{len(math_blocks)}___"
        math_blocks.append(match.group(0))
        return placeholder

    # Regex: prioritize matching double dollar signs, then single dollar signs
    math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'
    protected_content = re.sub(math_pattern, save_math, content, flags=re.DOTALL)

    protected_content = protected_content.replace(' ', '&nbsp;')
    protected_content = protected_content.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    protected_content = protected_content.replace('\n', '<br>')

    # Restore LaTeX formulas
    final_content = protected_content
    for i, original_math in enumerate(math_blocks):
        placeholder = f"___MATH_ID_{i}___"
        final_content = final_content.replace(placeholder, original_math)

    return f"___\n<br>{final_content.strip()}<br>\n___"


def qwenvl_cast_html_tag(input_text: str) -> str:
    output = input_text
    IMG_RE = re.compile(
        r'<img\b[^>]*\bdata-bbox\s*=\s*"?\d+,\d+,\d+,\d+"?[^>]*\/?>',
        flags=re.IGNORECASE,
    )
    output = IMG_RE.sub('', output)

    # code
    def replace_code(match):
        content = match.group(1)
        processed_content = process_code_content(content)
        return f"\n\n{processed_content}\n\n"
    
    code_pattern = re.compile(
        r'<div\b[^>]*class="code"[^>]*>(.*?)</div>',
        flags=re.DOTALL | re.IGNORECASE,
    )
    output = code_pattern.sub(replace_code, output)
    
    # pseudocode
    def replace_pseudocode(match):
        content = match.group(1)
        processed_content = process_pseudocode_content(content)
        return f"\n\n{processed_content}\n\n"
    
    pseudocode_pattern = re.compile(
        r'<div\b[^>]*class="pseudocode"[^>]*>(.*?)</div>',
        flags=re.DOTALL | re.IGNORECASE,
    )
    output = pseudocode_pattern.sub(replace_pseudocode, output)

    # <div>
    def strip_div(class_name: str, txt: str) -> str:
        if class_name in ['code', 'pseudocode']:
            return txt

        def replace_func(match):
            content = match.group(1)
            
            # 仅针对匹配到的 div 内部内容进行清洗
            if class_name == 'chart':
                content = re.sub(r'^\s*(click\s+|style\s+|linkStyle\s+|stroke|classDef\s+|class\s+)\b.*\n?', '', content, flags=re.MULTILINE | re.IGNORECASE)
                content = re.sub(r'^\s*(?:%%|::icon).*\n?', '', content, flags=re.MULTILINE)

                content = content.strip()
                if content.startswith('mermaid'):
                    content = '```' + content
                elif re.match(r'^```\s*mermaid', content):
                    pass
                else:
                    content = '```mermaid\n' + content
                if not content.endswith('```'):
                    content += '\n```'

            if class_name == 'music':
                content = remove_lines_starting_with(content)

                content = content.strip()
                if content.startswith('abc'):
                    content = '```' + content
                elif re.match(r'^```\s*abc', content):
                    pass
                else:
                    content = '```abc\n' + content
                if not content.endswith('```'):
                    content += '\n```'
                
            return f"\n\n{content}\n\n"

        pattern = re.compile(
            rf'\s*<div\b[^>]*class="{class_name}"[^>]*>(.*?)</div>\s*',
            flags=re.DOTALL | re.IGNORECASE,
        )
        return pattern.sub(replace_func, txt)

    other_classes = ['image', 'chemistry', 'table', 'formula', 'image caption', 'table caption']
    for cls in other_classes:
        output = strip_div(cls, output)
    
    # <p>
    output = re.sub(
        r'<p\b[^>]*>(.*?)</p>',
        r'\n\n\1\n\n',
        output,
        flags=re.DOTALL | re.IGNORECASE,
    )
    
    output = output.replace(" </td>", "</td>")
    return output


def smart_resize(
    height: int, width: int, factor: int = 32, min_pixels: int = 3136, max_pixels: int = 7200*32*32
):
    if height < factor or width < factor:
        raise ValueError(f"height:{height} or width:{width} must be larger than factor:{factor}")
    elif max(height, width) / min(height, width) > 200:
        raise ValueError(
            f"absolute aspect ratio must be smaller than 200, got {max(height, width) / min(height, width)}"
        )
    h_bar = round(height / factor) * factor
    w_bar = round(width / factor) * factor
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = math.floor(height / beta / factor) * factor
        w_bar = math.floor(width / beta / factor) * factor
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = math.ceil(height * beta / factor) * factor
        w_bar = math.ceil(width * beta / factor) * factor
    return h_bar, w_bar

def plot_bbox(img_path, pred, output_path):
    img = cv2.imread(img_path)
    if img is None:
        return
    img_height, img_width, _ = img.shape
    bboxes = []
    pattern = re.compile(r'data-bbox="(\d+),(\d+),(\d+),(\d+)"')

    def replace_bbox(match):
        x1, y1, x2, y2 = map(int, match)
        x1, y1 = int(x1/1000 * img_width), int(y1/1000 * img_height)
        x2, y2 = int(x2/1000 * img_width), int(y2/1000 * img_height)
        bboxes.append([x1,y1,x2,y2])

    matches = re.findall(pattern, pred)
    if matches:
        for match in matches:
            replace_bbox(match)
    for bbox in bboxes:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 8)
    cv2.imwrite(output_path, img)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Logics-Parsing for document parsing.")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--prompt", type=str, default="QwenVL HTML")

    args = parser.parse_args()
    
    # 1. 加载模型
    print(f"Loading model from {args.model_path}...")
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="cuda:0",
    )
    processor = AutoProcessor.from_pretrained(args.model_path)
    processor.image_processor.max_pixels = 7200 * 32 * 32
    processor.image_processor.min_pixels = 3136

    # 2. 准备输出目录
    os.makedirs(args.output_path, exist_ok=True)
    md_only_dir = os.path.join(args.output_path, "md_results")
    os.makedirs(md_only_dir, exist_ok=True)

    # 3. 获取待处理图片列表
    if os.path.isdir(args.image_path):
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
        img_files = sorted([f for f in os.listdir(args.image_path) if f.lower().endswith(valid_extensions)])
        input_is_dir = True
    else:
        img_files = [os.path.basename(args.image_path)]
        args.image_path = os.path.dirname(args.image_path)
        input_is_dir = False

    print(f"Total images found: {len(img_files)}")

    # 4. 循环处理（加入进度条和跳过逻辑）
    for img_name in tqdm(img_files, desc="Inference Progress"):
        img_path = os.path.join(args.image_path, img_name)
        base_name = os.path.splitext(img_name)[0]
        
        # 预先定义各输出路径
        if input_is_dir:
            curr_output_base = os.path.join(args.output_path, base_name)
        else:
            # 单文件模式下，如果 output_path 是目录则组合，否则直接作为前缀
            curr_output_base = os.path.join(args.output_path, base_name) if os.path.isdir(args.output_path) else args.output_path
            
        output_img_path = curr_output_base + "_vis.png"
        output_raw_path = curr_output_base + "_raw.mmd"
        output_mmd_path = curr_output_base + ".mmd"
        output_md_file = os.path.join(md_only_dir, base_name + ".md")

        # 【检测是否处理过】
        if os.path.exists(output_md_file):
            # print(f"Skipping {img_name}: Already processed.") # 可选：如果嫌进度条跳动太快可以注释掉
            continue

        try:
            raw_output = inference(img_path, args.prompt)
            
            # 保存可视化图
            plot_bbox(img_path, raw_output, output_img_path)
            
            # 保存原始输出
            with open(output_raw_path, 'w', encoding='utf-8') as f:
                f.write(raw_output)
            
            # 转换 Markdown 内容
            markdown_output = qwenvl_cast_html_tag(raw_output)
            
            # 保存到当前目录下的 .mmd
            with open(output_mmd_path, 'w', encoding='utf-8') as f:
                f.write(markdown_output)
            
            # 保存到 md_results 下的 .md
            with open(output_md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_output)
                
        except Exception as e:
            print(f"\nError processing {img_name}: {e}")

    print("\nAll done!")