import json
import random
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import argparse
import re
import os
import base64
from tqdm import tqdm
random.seed(42)

PROMPT = """ You are an AI assistant specialized in converting PDF images to Markdown format. Please follow these instructions for the conversion:

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
"""

def get_gpt_response(image_path):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    # 直接将原始图片字节转换为base64，避免重复编码
    img_str = base64.b64encode(image_bytes).decode()
    try:
        client = OpenAI(
            api_key= "API_KEY", 
            base_url="API_URL", 
        )
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_str}"
                        }
                    },
                    {"type": "text", "text": PROMPT}
                ]}
            ],
            # max_tokens=32000,
            # temperature=0.0 # OCR任务需要设置成0
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] Failed to get response: {e}")
        return ""

def process_image(args):
    image_path, save_root = args
    file_name = os.path.basename(image_path)
    try:
        response = get_gpt_response(image_path)
        output_path = os.path.join(save_root, file_name[:-4] + ".md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response)
        return f"成功处理: {file_name}"
    except Exception as e:
        return f"处理失败 {file_name}: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="使用GPT-4o处理图像并生成Markdown")
    parser.add_argument("--image_root", type=str, default="/mnt/hwfile/doc_parse/renzhifei/data/table_mask", help="图像文件夹路径")
    parser.add_argument("--save_root", type=str, default="/mnt/hwfile/doc_parse/oylk/model_mds/Omnidocbench_patch_table/GPT-4o", help="保存结果的文件夹路径")
    parser.add_argument("--threads", type=int, default=10, help="并行处理的线程数")
    args = parser.parse_args()
    
    image_root = args.image_root
    save_root = args.save_root
    num_threads = args.threads
    
    os.makedirs(save_root, exist_ok=True)
    
    # 收集所有需要处理的图像
    image_files = []
    for file in os.listdir(image_root):
        if file.endswith(".jpg") or file.endswith(".png"):
            # if file.startswith("news") or file.startswith("notes"):
            image_path = os.path.join(image_root, file)
            image_files.append((image_path, save_root))
    
    # 使用线程池并行处理图像
    print(f"开始使用 {num_threads} 个线程处理 {len(image_files)} 张图像...")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(tqdm(executor.map(process_image, image_files), total=len(image_files), desc="处理进度"))
    
    # 打印处理结果统计
    success_count = sum(1 for result in results if "成功" in result)
    print(f"处理完成: 总共 {len(image_files)} 张图像, 成功 {success_count} 张, 失败 {len(image_files) - success_count} 张")

if __name__ == "__main__":
    main()