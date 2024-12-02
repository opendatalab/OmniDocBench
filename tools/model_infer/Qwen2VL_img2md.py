import dashscope
import json
import os
from tqdm import tqdm
# from pdf2image import convert_from_path
from transformers import set_seed
import os
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
from modelscope import snapshot_download
import torch

def set_seed(seed):
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.cuda.manual_seed(seed)


# 指定模型的本地存储目录
model_dir =  "./.cache/huggingface/hub/models--Qwen--Qwen2-VL-72B-Instruct/snapshots/f400120e59a6196b024298b7d09fb517f742db7d"

# 加载模型
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_dir, torch_dtype=torch.bfloat16, device_map="auto",
    attn_implementation = "flash_attention_2"
)
# 加载处理器
processor = AutoProcessor.from_pretrained(model_dir)

# 设置输入和输出的基目录
input_dir = '../../demo_data/omnidocbench_demo/images'
output_dir = "/mnt/petrelfs/ouyanglinke/DocParseEval/demo_data/end2end"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# complex prompt
prompt = r'''You are an AI assistant specialized in converting PDF images to Markdown format. Please follow these instructions for the conversion:

        1. Text Processing:
        - Accurately recognize all text content in the PDF image without guessing or inferring.
        - Convert the recognized text into Markdown format.
        - Maintain the original document structure, including headings, paragraphs, lists, etc.

        2. Mathematical Formula Processing:
        - Convert all mathematical formulas to LaTeX format.
        - Enclose inline formulas with \( \). For example: This is an inline formula \( E = mc^2 \)
        - Enclose block formulas with \\[ \\]. For example: \[ \frac{-b \pm \sqrt{b^2 - 4ac}}{2a} \]

        3. Table Processing:
        - Convert tables to HTML format.
        - Wrap the entire table with <table> and </table>.

        4. Figure Handling:
        - Ignore figures content in the PDF image. Do not attempt to describe or convert images.

        5. Output Format:
        - Ensure the output Markdown document has a clear structure with appropriate line breaks between elements.
        - For complex layouts, try to maintain the original document's structure and format as closely as possible.

        Please strictly follow these guidelines to ensure accuracy and consistency in the conversion. Your task is to accurately convert the content of the PDF image into Markdown format without adding any extra explanations or comments.
        '''

image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

# 遍历目录及其子目录下的所有文件，并过滤出图片文件
for root, _, files in os.walk(input_dir):
    for name in files:
        if any(name.lower().endswith(ext) for ext in image_extensions):
            
            # 构建完整的文件路径
            image_path = os.path.join(root, name)
            
            # 提取出不包含文件后缀的文件名basename
            basename = os.path.splitext(name)[0]
            # 构建Markdown文件的完整路径
            markdown_file = os.path.join(output_dir, f"{basename}.md")

            # 如果markdown_file文件存在，则跳过
            if os.path.exists(markdown_file):
                print(f"文件已存在，跳过: {markdown_file}")
                continue
            
            # image_path
            # 设置请求消息内容
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image_path,
                            # "max_pixels":2048*2048
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            text = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to("cuda")

            set_seed(0)
            generated_ids = model.generate(**inputs, max_new_tokens=1024, temperature=0.01,do_sample=False)
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )

            # 构建Markdown文件的完整路径
            markdown_file = os.path.join(output_dir, f"{basename}.md")
            
            # 将响应写入Markdown文件
            with open(markdown_file, 'w', encoding='utf-8') as file:
                file.write(output_text[0])
                print(f"Saved: {markdown_file}")

