import os
import json
from pathlib import Path
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
import argparse

from dots_ocr.model.inference import inference_with_vllm
from dots_ocr.utils.consts import image_extensions, MIN_PIXELS, MAX_PIXELS
from dots_ocr.utils.image_utils import get_image_by_fitz_doc, fetch_image, smart_resize
from dots_ocr.utils.doc_utils import fitz_doc_to_image, load_images_from_pdf
from dots_ocr.utils.prompts import dict_promptmode_to_prompt
from dots_ocr.utils.layout_utils import post_process_output, draw_layout_on_image, pre_process_bboxes
from dots_ocr.utils.format_transformer import layoutjson2md


class DotsOCRParser:
    """
    parse image or pdf file
    """

    def __init__(self,
                 protocol='http',
                 ip='localhost',
                 port=8000,
                 model_name='model',
                 temperature=0.1,
                 top_p=1.0,
                 max_completion_tokens=16384,
                 num_thread=64,
                 dpi=200,
                 output_dir="./output",
                 min_pixels=None,
                 max_pixels=None,
                 use_hf=False,
                 ):
        self.dpi = dpi

        self.protocol = protocol
        self.ip = ip
        self.port = port
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_completion_tokens = max_completion_tokens
        self.num_thread = num_thread
        self.output_dir = output_dir
        self.min_pixels = min_pixels
        self.max_pixels = max_pixels

        self.use_hf = use_hf
        if self.use_hf:
            self._load_hf_model()
            print(f"use hf model, num_thread will be set to 1")
        else:
            print(f"use vllm model, num_thread will be set to {self.num_thread}")
        assert self.min_pixels is None or self.min_pixels >= MIN_PIXELS
        assert self.max_pixels is None or self.max_pixels <= MAX_PIXELS

    def _load_hf_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer
        from qwen_vl_utils import process_vision_info

        model_path = "./weights/DotsOCR"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            attn_implementation="flash_attention_2",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True, use_fast=True)
        self.process_vision_info = process_vision_info

    def _inference_with_hf(self, image, prompt):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        image_inputs, video_inputs = self.process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        inputs = inputs.to("cuda")

        generated_ids = self.model.generate(**inputs, max_new_tokens=24000)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        response = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        return response

    def _inference_with_vllm(self, image, prompt):
        response = inference_with_vllm(
            image,
            prompt,
            model_name=self.model_name,
            protocol=self.protocol,
            ip=self.ip,
            port=self.port,
            temperature=self.temperature,
            top_p=self.top_p,
            max_completion_tokens=self.max_completion_tokens,
        )
        return response

    def get_prompt(self, prompt_mode, bbox=None, origin_image=None, image=None, min_pixels=None, max_pixels=None):
        prompt = dict_promptmode_to_prompt[prompt_mode]
        if prompt_mode == 'prompt_grounding_ocr':
            assert bbox is not None
            bboxes = [bbox]
            bbox = pre_process_bboxes(origin_image, bboxes, input_width=image.width, input_height=image.height, min_pixels=min_pixels, max_pixels=max_pixels)[0]
            prompt = prompt + str(bbox)
        return prompt

    def _parse_single_image(
            self,
            origin_image,
            prompt_mode,
            save_dir,
            save_name,
            source="image",
            page_idx=0,
            bbox=None,
            fitz_preprocess=False,
    ):
        min_pixels, max_pixels = self.min_pixels, self.max_pixels
        if prompt_mode == "prompt_grounding_ocr":
            min_pixels = min_pixels or MIN_PIXELS
            max_pixels = max_pixels or MAX_PIXELS
        if min_pixels is not None: assert min_pixels >= MIN_PIXELS, f"min_pixels should >= {MIN_PIXELS}"
        if max_pixels is not None: assert max_pixels <= MAX_PIXELS, f"max_pixels should <= {MAX_PIXELS}"

        if source == 'image' and fitz_preprocess:
            image = get_image_by_fitz_doc(origin_image, target_dpi=self.dpi)
            image = fetch_image(image, min_pixels=min_pixels, max_pixels=max_pixels)
        else:
            image = fetch_image(origin_image, min_pixels=min_pixels, max_pixels=max_pixels)
        input_height, input_width = smart_resize(image.height, image.width)
        prompt = self.get_prompt(prompt_mode, bbox, origin_image, image, min_pixels=min_pixels, max_pixels=max_pixels)
        if self.use_hf:
            response = self._inference_with_hf(image, prompt)
        else:
            response = self._inference_with_vllm(image, prompt)
        result = {'page_no': page_idx,
                  "input_height": input_height,
                  "input_width": input_width
                  }
        if source == 'pdf':
            save_name = f"{save_name}_page_{page_idx}"
        if prompt_mode in ['prompt_layout_all_en', 'prompt_layout_only_en', 'prompt_grounding_ocr']:
            cells, filtered = post_process_output(
                response,
                prompt_mode,
                origin_image,
                image,
                min_pixels=min_pixels,
                max_pixels=max_pixels,
            )
            if filtered and prompt_mode != 'prompt_layout_only_en':
                json_file_path = os.path.join(save_dir, f"{save_name}.json")
                with open(json_file_path, 'w', encoding="utf-8") as w:
                    json.dump(response, w, ensure_ascii=False)

                image_layout_path = os.path.join(save_dir, f"{save_name}.jpg")
                origin_image.save(image_layout_path)
                result.update({
                    'layout_info_path': json_file_path,
                    'layout_image_path': image_layout_path,
                })

                md_file_path = os.path.join(save_dir, f"{save_name}.md")
                with open(md_file_path, "w", encoding="utf-8") as md_file:
                    md_file.write(cells)
                result.update({
                    'md_content_path': md_file_path
                })
                result.update({
                    'filtered': True
                })
            else:
                try:
                    image_with_layout = draw_layout_on_image(origin_image, cells)
                except Exception as e:
                    print(f"Error drawing layout on image: {e}")
                    image_with_layout = origin_image

                json_file_path = os.path.join(save_dir, f"{save_name}.json")
                with open(json_file_path, 'w', encoding="utf-8") as w:
                    json.dump(cells, w, ensure_ascii=False)

                image_layout_path = os.path.join(save_dir, f"{save_name}.jpg")
                image_with_layout.save(image_layout_path)
                result.update({
                    'layout_info_path': json_file_path,
                    'layout_image_path': image_layout_path,
                })
                if prompt_mode != "prompt_layout_only_en":
                    md_content = layoutjson2md(origin_image, cells, text_key='text')
                    md_content_no_hf = layoutjson2md(origin_image, cells, text_key='text', no_page_hf=True)
                    md_file_path = os.path.join(save_dir, f"{save_name}.md")
                    with open(md_file_path, "w", encoding="utf-8") as md_file:
                        md_file.write(md_content)
                    md_nohf_file_path = os.path.join(save_dir, f"{save_name}_nohf.md")
                    with open(md_nohf_file_path, "w", encoding="utf-8") as md_file:
                        md_file.write(md_content_no_hf)
                    result.update({
                        'md_content_path': md_file_path,
                        'md_content_nohf_path': md_nohf_file_path,
                    })
        else:
            image_layout_path = os.path.join(save_dir, f"{save_name}.jpg")
            origin_image.save(image_layout_path)
            result.update({
                'layout_image_path': image_layout_path,
            })

            md_content = response
            md_file_path = os.path.join(save_dir, f"{save_name}.md")
            with open(md_file_path, "w", encoding="utf-8") as md_file:
                md_file.write(md_content)
            result.update({
                'md_content_path': md_file_path,
            })

        return result

    def parse_image(self, input_path, filename, prompt_mode, save_dir, bbox=None, fitz_preprocess=False):
        origin_image = fetch_image(input_path)
        result = self._parse_single_image(origin_image, prompt_mode, save_dir, filename, source="image", bbox=bbox, fitz_preprocess=fitz_preprocess)
        result['file_path'] = input_path
        return [result]

    def parse_pdf(self, input_path, filename, prompt_mode, save_dir):
        print(f"loading pdf: {input_path}")
        images_origin = load_images_from_pdf(input_path, dpi=self.dpi)
        total_pages = len(images_origin)
        tasks = [
            {
                "origin_image": image,
                "prompt_mode": prompt_mode,
                "save_dir": save_dir,
                "save_name": filename,
                "source": "pdf",
                "page_idx": i,
            } for i, image in enumerate(images_origin)
        ]

        def _execute_task(task_args):
            return self._parse_single_image(**task_args)

        if self.use_hf:
            num_thread = 1
        else:
            num_thread = min(total_pages, self.num_thread)
        print(f"Parsing PDF with {total_pages} pages using {num_thread} threads...")

        results = []
        with ThreadPool(num_thread) as pool:
            with tqdm(total=total_pages, desc="Processing PDF pages") as pbar:
                for result in pool.imap_unordered(_execute_task, tasks):
                    results.append(result)
                    pbar.update(1)

        results.sort(key=lambda x: x["page_no"])
        for i in range(len(results)):
            results[i]['file_path'] = input_path
        return results

    def parse_file(self,
                   input_path,
                   output_dir="",
                   prompt_mode="prompt_layout_all_en",
                   bbox=None,
                   fitz_preprocess=False
                   ):
        output_dir = output_dir or self.output_dir
        output_dir = os.path.abspath(output_dir)
        filename, file_ext = os.path.splitext(os.path.basename(input_path))
        save_dir = os.path.join(output_dir, filename)
        os.makedirs(save_dir, exist_ok=True)

        if file_ext == '.pdf':
            results = self.parse_pdf(input_path, filename, prompt_mode, save_dir)
        elif file_ext.lower() in image_extensions:
            results = self.parse_image(input_path, filename, prompt_mode, save_dir, bbox=bbox, fitz_preprocess=fitz_preprocess)
        else:
            raise ValueError(f"file extension {file_ext} not supported, supported extensions are {image_extensions} and pdf")

        print(f"Parsing finished, results saving to {save_dir}")
        jsonl_path = os.path.join(output_dir, filename + '.jsonl')
        with open(jsonl_path, 'w', encoding="utf-8") as w:
            for result in results:
                w.write(json.dumps(result, ensure_ascii=False) + '\n')

        return results


def _collect_files(input_dir, recursive=False):
    """收集目录下所有支持的 PDF/图片文件。"""
    input_path = Path(input_dir)
    if not input_path.is_dir():
        return []
    supported = {".pdf", *{e.lower() for e in image_extensions}}
    if recursive:
        files = [p for p in input_path.rglob("*") if p.is_file() and p.suffix.lower() in supported]
    else:
        files = [p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() in supported]
    return sorted(files)


def main():
    prompts = list(dict_promptmode_to_prompt.keys())
    parser = argparse.ArgumentParser(
        description="dots.ocr Multilingual Document Layout Parser (file or folder)",
    )

    parser.add_argument(
        "input_path", type=str,
        help="Input PDF/image file path, or directory containing PDF/image files"
    )

    parser.add_argument(
        "--output", type=str, default="./output",
        help="Output directory (default: ./output)"
    )

    parser.add_argument(
        "--prompt", choices=prompts, type=str, default="prompt_layout_all_en",
        help="prompt to query the model, different prompts for different tasks"
    )
    parser.add_argument(
        '--bbox',
        type=int,
        nargs=4,
        metavar=('x1', 'y1', 'x2', 'y2'),
        help='should give this argument if you want to prompt_grounding_ocr'
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="When input is a directory, also process files in subdirectories"
    )
    parser.add_argument(
        "--skip_existing", action="store_true",
        help="When input is a directory, skip file if its output folder already exists"
    )
    parser.add_argument(
        "--protocol", type=str, choices=['http', 'https'], default="http",
        help=""
    )
    parser.add_argument(
        "--ip", type=str, default="localhost",
        help=""
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help=""
    )
    parser.add_argument(
        "--model_name", type=str, default="dots.ocr/",
        help=""
    )
    parser.add_argument(
        "--temperature", type=float, default=0.1,
        help=""
    )
    parser.add_argument(
        "--top_p", type=float, default=1.0,
        help=""
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help=""
    )
    parser.add_argument(
        "--max_completion_tokens", type=int, default=16384,
        help=""
    )
    parser.add_argument(
        "--num_thread", type=int, default=16,
        help=""
    )
    parser.add_argument(
        "--no_fitz_preprocess", action='store_true',
        help="False will use tikz dpi upsample pipeline, good for images which has been render with low dpi, but maybe result in higher computational costs"
    )
    parser.add_argument(
        "--min_pixels", type=int, default=None,
        help=""
    )
    parser.add_argument(
        "--max_pixels", type=int, default=None,
        help=""
    )
    parser.add_argument(
        "--use_hf", type=bool, default=False,
        help=""
    )
    args = parser.parse_args()

    dots_ocr_parser = DotsOCRParser(
        protocol=args.protocol,
        ip=args.ip,
        port=args.port,
        model_name=args.model_name,
        temperature=args.temperature,
        top_p=args.top_p,
        max_completion_tokens=args.max_completion_tokens,
        num_thread=args.num_thread,
        dpi=args.dpi,
        output_dir=args.output,
        min_pixels=args.min_pixels,
        max_pixels=args.max_pixels,
        use_hf=args.use_hf,
    )

    fitz_preprocess = not args.no_fitz_preprocess
    if fitz_preprocess:
        print(f"Using fitz preprocess for image input, check the change of the image pixels")

    input_path = Path(args.input_path)
    output_dir = os.path.abspath(args.output)

    if input_path.is_file():
        # 单文件：保持原有逻辑
        result = dots_ocr_parser.parse_file(
            str(input_path),
            prompt_mode=args.prompt,
            bbox=args.bbox,
            fitz_preprocess=fitz_preprocess,
        )
    elif input_path.is_dir():
        # 文件夹：收集所有支持的文件并逐个处理
        files = _collect_files(args.input_path, recursive=args.recursive)
        if not files:
            print(f"目录下未找到支持的 PDF/图片: {args.input_path}")
            return
        print(f"在 {args.input_path} 下找到 {len(files)} 个文件，输出目录: {output_dir}")

        to_process = []
        for f in files:
            stem = f.stem
            save_dir = os.path.join(output_dir, stem)
            if args.skip_existing and os.path.isdir(save_dir) and os.path.isfile(os.path.join(output_dir, stem + ".jsonl")):
                continue
            to_process.append(f)

        skipped = len(files) - len(to_process)
        if skipped:
            print(f"跳过 {skipped} 个(输出已存在)，待处理 {len(to_process)} 个")
        if not to_process:
            print("全部已有输出，无需处理")
            return

        for fp in tqdm(to_process, desc="Processing files"):
            try:
                dots_ocr_parser.parse_file(
                    str(fp),
                    output_dir=output_dir,
                    prompt_mode=args.prompt,
                    bbox=args.bbox,
                    fitz_preprocess=fitz_preprocess,
                )
            except Exception as e:
                tqdm.write(f"失败 {fp.name}: {e}")
        print("全部处理完成")
    else:
        raise FileNotFoundError(f"输入路径不存在或既不是文件也不是目录: {args.input_path}")


if __name__ == "__main__":
    main()
