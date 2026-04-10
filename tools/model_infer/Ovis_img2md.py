import torch
import os
import json
import pandas as pd
from PIL import Image
from transformers import AutoModelForCausalLM
from tqdm import tqdm
import datetime

def clean_truncated_repeats(
    text: str,
    min_text_len: int = 8000,
    max_period: int = 200,
    min_period: int = 1,
    min_repeat_chars: int = 100,
    min_repeat_times: int = 5,
) -> str:
    n = len(text)
    if n < min_text_len:
        return text
    max_period = min(max_period, n - 1)
    for unit_len in range(min_period, max_period + 1):
        if text[n - 1] != text[n - 1 - unit_len]:
            continue
        match_len = 1
        idx = n - 2
        while idx >= unit_len and text[idx] == text[idx - unit_len]:
            match_len += 1
            idx -= 1
        total_len = match_len + unit_len
        repeat_times = total_len // unit_len
        tail_len = total_len % unit_len
        if repeat_times >= min_repeat_times and total_len >= min_repeat_chars:
            return text[:n - total_len + unit_len] + text[n - tail_len:]
    return text

def main():
    model_path = "AIDC-AI/Ovis2.6-30B-A3B"
    json_path = "OmniDocBench.json"
    image_root = "OmniDocBench/images"

    output_dir = f"OmniDocBench/output_md"
    os.makedirs(output_dir, exist_ok=True)

    enable_thinking = False
    max_new_tokens = 16384
    thinking_budget = 1024  # not used but kept

    # OCR 专用 Prompt
    query_prompt = (
        '</tr>\nExtract all readable content from the image in natural human reading order '
        'and output the result as a single Markdown document. For charts, images, or seals, '
        'represent them using an HTML image tag: <img src="images/bbox_{left}_{top}_{right}_{bottom}.jpg" />, '
        'where left, top, right, bottom are bounding box coordinates scaled to [0, 1000). '
        'Format formulas as LaTeX. Format tables as HTML: <table>...</table>. '
        'Transcribe all other text as standard Markdown. Preserve the original text without translation or paraphrasing.'
    )

    print(f"Loading model from {model_path}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto"
    )

    print(f"Reading dataset from {json_path}...")
    omni = pd.read_json(json_path)
    omni['image_path'] = omni['page_info'].apply(lambda x: os.path.join(image_root, x['image_path']))
    samples = omni[['image_path', 'page_info']].to_dict(orient='records')

    for sample in tqdm(samples, desc="Processing OmniDocBench"):
        image_full_path = sample['image_path']
        image_basename = os.path.basename(sample['page_info']['image_path'])
        output_path = os.path.join(output_dir, f"{image_basename}.md")

        if os.path.exists(output_path):
            continue

        try:
            image = Image.open(image_full_path).convert("RGB")

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": query_prompt},
                ],
            }]

            input_ids, pixel_values, grid_thws = model.preprocess_inputs(
                messages=messages,
                add_generation_prompt=True,
                enable_thinking=enable_thinking
            )

            input_ids = input_ids.cuda()
            pixel_values = pixel_values.cuda() if pixel_values is not None else None
            grid_thws = grid_thws.cuda() if grid_thws is not None else None

            with torch.inference_mode():
                outputs = model.generate(
                    inputs=input_ids,
                    pixel_values=pixel_values,
                    grid_thws=grid_thws,
                    max_new_tokens=max_new_tokens,
                    enable_thinking=enable_thinking,
                    pad_token_id=model.text_tokenizer.eos_token_id,
                    temperature=0.0,
                    do_sample=False
                )

            raw_response = model.text_tokenizer.decode(outputs[0], skip_special_tokens=True)

            processed_response = clean_truncated_repeats(raw_response)

            lines = processed_response.split('\n\n')
            filtered_lines = filter(lambda x: not x.strip().startswith('<img src="images/bbox_'), lines)
            final_md = '\n\n'.join(filtered_lines)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_md)

        except Exception as e:
            print(f"Error processing {image_basename}: {e}")

    print(f"All done! Results are saved in {output_dir}")

if __name__ == "__main__":
    main()