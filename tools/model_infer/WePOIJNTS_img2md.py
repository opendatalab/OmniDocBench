import sys
from transformers import AutoModelForCausalLM, AutoTokenizer, Qwen2VLImageProcessor, AutoConfig, BitsAndBytesConfig
import torch

sys.path.insert(0, "/data/boyu/WePOINTS")

prompt = (
    'Please extract all the text from the image with the following requirements:\n'
    '1. Return tables in HTML format.\n'
    '2. Return all other text in Markdown format.'
)
model_path = 'tencent/POINTS-Reader'

model = AutoModelForCausalLM.from_pretrained(model_path,
                                            trust_remote_code=True,
                                            torch_dtype=torch.float16,
                                            device_map='auto',
                                            attn_implementation="eager")

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
image_processor = Qwen2VLImageProcessor.from_pretrained(model_path)


def model_infer(image_path):
    # We recommend using the following prompt to better performance,
    # since it is used throughout the training process.
    content = [
                dict(type='image', image=image_path),
                dict(type='text', text=prompt)
            ]

    messages = [
            {
                'role': 'user',
                'content': content
            }
        ]

    generation_config = {
            'max_new_tokens': 2048,
            'repetition_penalty': 1.05,
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 20,
            'do_sample': True
        }

    response = model.chat(
        messages,
        tokenizer,
        image_processor,
        generation_config
    )
    return response

def main():
    import os
    from tqdm import tqdm

    image_dir = '/home/boyu/autopoet/pics'
    output_dir = '/home/boyu/autopoet/infers'
    os.makedirs(output_dir, exist_ok=True)

    all_files = []
    for root, _, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')): # 过滤掉非图片文件
                all_files.append((root, file))

    for root, file in tqdm(all_files, desc="Processing Images"):
        full_path = os.path.join(root, file)
        
        text = model_infer(full_path)
        base_name = os.path.splitext(file)[0]
        output_path = os.path.join(output_dir, f"{base_name}.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

if __name__=="__main__":
    main()