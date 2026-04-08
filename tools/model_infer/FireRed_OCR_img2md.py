import os
import torch
from tqdm import tqdm
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from conv_for_infer import generate_conv

# ================= 配置部分 =================
# 输入图片文件夹路径
IMAGE_DIR = "./image" 
# 结果保存文件夹路径
OUTPUT_DIR = "./output"
# 模型路径
MODEL_PATH = "./model/FireRed-OCR"

# 支持的图片后缀
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
# ===========================================

# 1. 准备输出文件夹
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"创建输出目录: {OUTPUT_DIR}")

# 2. 预先获取已经处理过的文件名集合 (用于跳过)
# 我们存储不带后缀的文件名，方便对比
processed_basenames = {
    os.path.splitext(f)[0] for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')
}
print(f"检测到已有 {len(processed_basenames)} 个结果文件，将自动跳过。")

# 3. 加载模型和处理器
print("正在加载模型...")
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    dtype=torch.bfloat16,
    device_map="auto",
)
processor = AutoProcessor.from_pretrained(MODEL_PATH)
print("模型加载完成。")

# 4. 获取所有待处理图片
all_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(IMAGE_EXTENSIONS)]
# 过滤掉已经处理过的
image_files = [f for f in all_files if os.path.splitext(f)[0] not in processed_basenames]

print(f"总计图片: {len(all_files)} 张")
print(f"跳过图片: {len(all_files) - len(image_files)} 张")
print(f"剩余待处理: {len(image_files)} 张")

if len(image_files) == 0:
    print("没有新的图片需要处理，程序退出。")
    exit()

# 5. 循环处理
for filename in tqdm(image_files, desc="OCR Processing"):
    image_path = os.path.join(IMAGE_DIR, filename)
    base_name = os.path.splitext(filename)[0]
    output_file_path = os.path.join(OUTPUT_DIR, f"{base_name}.md")
    
    # 双重检查（防止运行过程中手动删减文件或多进程冲突）
    if os.path.exists(output_file_path):
        continue

    try:
        # 准备输入
        messages = generate_conv(image_path)
        
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )
        inputs = inputs.to(model.device)

        # 推理
        generated_ids = model.generate(**inputs, max_new_tokens=8192)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        # 保存结果
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(output_text[0]) 
            
    except Exception as e:
        print(f"\n处理图片 {filename} 时出错: {e}")
        continue

print(f"\n任务完成！结果目录: {OUTPUT_DIR}")