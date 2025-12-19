from openai import OpenAI, APIConnectionError
import base64
import os
import time
import sys
import argparse
from tqdm import tqdm

def encode_image(image_path):
    """
    Encode the image file to base64 string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

prompt = """You are an AI assistant specialized in converting PDF images to Markdown format. Please follow these instructions for the conversion:

1. Text Processing:
- Accurately recognize all text content in the PDF image without guessing or inferring.
- Convert the recognized text into Markdown format.
- Maintain the original document structure, including headings, paragraphs, lists, etc.

2. Mathematical Formula Processing:
- Convert all mathematical formulas to LaTeX format.
- Enclose inline formulas with \\( \\). For example: This is an inline formula \\( E = mc^2 \\)
- Enclose block formulas with \\[ \\]. For example: \\[ \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} \\]

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

def process_image(client, image_file, image_dir, result_dir, model_name):
    """
    处理单个图片文件
    """
    try:
        # 检查输出文件是否已存在
        output_path = os.path.join(result_dir, image_file + ".md")
        if os.path.exists(output_path):
            return f"⏭ 跳过已存在: {image_file}"
        
        image_path = os.path.join(image_dir, image_file)
        base64_image = encode_image(image_path)
        data_url = f"data:image/jpeg;base64,{base64_image}"
        # from urllib.parse import quote
        # encoded = quote(image_file, safe='')
        # data_url = f"https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/main/images/{encoded}"
        # print(data_url)

        response = client.chat.completions.create(
            model=model_name,
            messages=[{
                'role':'user',
                'content': [
                    {
                        'type': 'text',
                        'text': prompt,
                    }, 
                    {
                        'type': 'image_url',
                        'image_url': {'url': data_url},
                    }
                ],
            }],
            stream=True,
            timeout=10000,
        )
        
        result = ""
        for chunk in response:
            # print(chunk)
            # if chunk.choices[0].delta.type == "thought":
            #     continue
            if chunk.choices[0].finish_reason is not None:
                break
            result += chunk.choices[0].delta.content
            print(f"{time.time()} {image_file} content:{chunk.choices[0].delta.content}")
        
        with open(output_path, "w", encoding='utf-8') as f:
            print(result, file=f)
            
        return f"✓ 成功处理: {image_file}"
    except APIConnectionError as e:
        return f"✗ 连接超时: {image_file}, 错误: {str(e)}"
    except Exception as e:
        # 保存错误信息到文件
        # output_path = os.path.join(result_dir, image_file + ".md")
        # with open(output_path, "w", encoding='utf-8') as f:
        #     print(f"处理错误: {str(e)}", file=f)
        return f"✗ 处理失败: {image_file}, 错误: {str(e)}"


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='串行处理图片并转换为Markdown格式')
    
    parser.add_argument('--base_url', type=str, 
                       default='https://api_host',
                       help='API基础URL')
    
    parser.add_argument('--api_key', type=str, 
                       default='sk-xxx',
                       help='API密钥')
    
    parser.add_argument('--model_name', type=str, 
                       default='qwen/qwen3-vl-235b-a22b-instruct',
                       help='模型名称')
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    image_dir = "./images"
    result_dir = f"./{args.model_name.split("/")[-1]}"
    os.makedirs(result_dir, exist_ok=True)

    client = OpenAI(
        base_url=args.base_url,
        api_key=args.api_key,
    )

    # 获取所有图片文件
    image_files = [f for f in os.listdir(image_dir) 
                   if f.endswith((".jpg", ".png", ".jpeg"))]
    # image_files = image_files[:10]
    
    # 检查已存在的文件
    existing_files = []
    new_files = []
    for image_file in image_files:
        output_path = os.path.join(result_dir, image_file + ".md")
        if os.path.exists(output_path):
            existing_files.append(image_file)
        else:
            new_files.append(image_file)
    
    print(f"找到 {len(image_files)} 个图片文件")
    print(f"其中 {len(existing_files)} 个已处理，{len(new_files)} 个待处理")
    
    if len(new_files) == 0:
        print("所有文件都已处理完成！")
        sys.exit(0)
    
    print("开始串行处理...")
    
    # 串行处理所有文件
    completed_count = 0
    failed_count = 0
    
    for image_file in tqdm(new_files, desc="处理图片"):
        print(f"开始处理: {image_file}")
        try:
            result = process_image(client, image_file, image_dir, result_dir, args.model_name)
            if "✓ 成功处理" in result:
                completed_count += 1
            elif "✗" in result:
                failed_count += 1
            print(result)
        except Exception as exc:
            failed_count += 1
            print(f"✗ {image_file} 处理时发生异常: {exc}")
    
    print(f"\n处理完成统计:")
    print(f"✓ 成功处理: {completed_count} 个")
    print(f"⏭ 跳过已存在: {len(existing_files)} 个") 
    print(f"✗ 处理失败: {failed_count} 个")
    print(f"📁 总共处理: {len(image_files)} 个文件")
    print(f"结果保存在: {result_dir}")