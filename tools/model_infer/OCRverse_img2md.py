from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
import torch
import os

# Load model
model_path = './checkpoints/OCRVerse-text'
model = Qwen3VLForConditionalGeneration.from_pretrained(
    model_path,
    dtype="auto", 
    device_map="cuda",
    trust_remote_code=True
)
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

imgae_folder = "./images"
output_folder = "./OCRverse"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for image_file in os.listdir(imgae_folder):
    if not (image_file.endswith('.jpg') or image_file.endswith('.png')):
        continue

    save_path = os.path.join(output_folder, image_file.replace('.png', '.md').replace('.jpg', '.md'))
    if os.path.exists(save_path):
        continue
    # Prepare input with image and text
    image_path = os.path.join(imgae_folder, image_file)
    # We recommend using the following prompt to better performance, since it is used throughout the training process.
    prompt = "Extract the main content from the document in the image, keeping the original structure. Convert all formulas to LaTeX and all tables to HTML."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": prompt},
            ]
        }
    ]

    # Preparation for inference
    inputs = processor.apply_chat_template(
        messages, 
        tokenize=True, 
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt"
    )
    inputs = inputs.to(model.device)

    # Inference: Generation of the output
    generated_ids = model.generate(**inputs, max_new_tokens=8192, do_sample=False)

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.tokenizer.batch_decode(
        generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    # print(output_text[0])
    with open(save_path, 'w') as f:
        f.write(output_text[0])

# $$
# r = \frac{\alpha}{\beta} \sin \beta (\sigma_1 \pm \sigma_2)
# $$