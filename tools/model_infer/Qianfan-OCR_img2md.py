
"""批量调用 VLM API 将文档图片转换为 Markdown。

# Serve with vLLM for high-throughput inference
# vllm serve baidu/Qianfan-OCR --trust-remote-code
"""

import json
import logging
import mimetypes
import time
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import requests
from tqdm import tqdm

# ========================= 配置区 =========================

@dataclass
class Config:
    """所有可调参数集中管理。"""

    api_url: str = ""
    api_key: str | None = None
    model_name: str = ""

    image_dir: Path = Path("./images")
    output_dir: Path = Path("./output")

    max_workers: int = 1
    temperature: float = 0.0
    seed: int = 666
    max_tokens: int = 20480
    stream: bool = True

    max_retries: int = 3
    retry_backoff: float = 2.0  # 指数退避基数（秒）

    image_extensions: tuple[str, ...] = (
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    )

    prompt_text: str = """\
You are an AI assistant specialized in converting document images (one or multiple pages extracted from a PDF) into Markdown with high fidelity.

Your task is to accurately convert all visible content from the images into Markdown, strictly following the rules below. Do not add explanations, comments, or inferred content.

1. Pages:
- The input may contain one or multiple page images.
- Preserve the exact page order as provided.
- If there are multiple pages, separate pages using the marker:
  --- Page N ---
  (N starts from 1)
- If there is only one page, do NOT output any page separator.

2. Text Recognition:
- Accurately convert all visible text.
- No guessing, inference, paraphrasing, or correction.
- Preserve the original document structure, including headings, paragraphs, lists, captions, and footnotes.
- Completely REMOVE all header and footer text. Do not output page numbers, running titles, or repeated marginal content.

3. Reading Order:
- Follow a top-to-bottom, left-to-right reading order.
- For multi-column layouts, fully read the left column before the right column.
- Do not reorder content for semantic or logical clarity.

4. Mathematical Formulas:
- Convert all mathematical expressions to LaTeX.
- Inline formulas must use $...$.
- Display (block) formulas must use:
  $$
  ...
  $$
- Preserve symbols, spacing, and structure exactly.
- Do not invent, simplify, normalize, or correct formulas.

5. Tables:
- Convert all tables to HTML format.
- Wrap each table with <table> and </table>.
- Preserve row and column order, merged cells (rowspan, colspan), and empty cells.
- Do not restructure or reinterpret tables.

6. Images:
- Do NOT describe image content.
- Preserve images using the exact format:
  ![label](<box>[[x1, y1, x2, y2]]</box>)
- Allowed labels: image, chart, seal.
- Completely REMOVE all header_image and footer_image elements.
- Do not introduce new labels.
- Do not remove or merge remaining image elements.

7. Unreadable or Missing Content:
- If text, symbols, or table cells are unreadable, preserve their position and leave the content empty.
- Do not guess or fill in missing information.

8. Output Requirements:
- Output Markdown only.
- Preserve original layout, spacing, and structure as closely as possible.
- Ensure clear separation between elements using line breaks.
- Do not include any explanations, metadata, or comments."""

# ======================== 配置区结束 ========================


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------- 工具函数 ----------

def encode_image(image_path: Path) -> str:
    """将本地图片转换为 base64 编码。"""
    return b64encode(image_path.read_bytes()).decode("utf-8")


def guess_mime_type(image_path: Path) -> str:
    """根据文件扩展名推断 MIME 类型，默认 image/jpeg。"""
    mime, _ = mimetypes.guess_type(image_path.name)
    return mime or "image/jpeg"


def collect_images(image_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """收集目录下所有符合扩展名的图片，按文件名排序返回。"""
    images = sorted(
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )
    return images


# ---------- 流式 / 非流式响应解析 ----------

def _parse_stream_response(resp: requests.Response) -> str:
    """解析 SSE 流式响应，返回拼接后的文本。"""
    chunks: list[str] = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        if payload == "[DONE]":
            break
        try:
            delta = json.loads(payload)["choices"][0].get("delta", {})
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            log.warning("解析流式 chunk 失败，已跳过: %s", exc)
            continue
        if "content" in delta:
            chunks.append(delta["content"])
    return "".join(chunks)


def _parse_normal_response(resp: requests.Response) -> str:
    """解析非流式响应，返回文本。"""
    return resp.json()["choices"][0]["message"]["content"]


# ---------- 单张图片处理 ----------

def process_single_image(image_path: Path, cfg: Config) -> str:
    """处理单张图片：调用 API 并将结果写入 .md 文件。

    内置指数退避重试机制。
    """
    mime = guess_mime_type(image_path)
    b64 = encode_image(image_path)

    data = {
        "model": cfg.model_name,
        "temperature": cfg.temperature,
        "seed": cfg.seed,
        "max_tokens": cfg.max_tokens,
        "skip_special_tokens": False,
        "stream": cfg.stream,
        "mm_processor_kwargs": {
            "min_dynamic_patch": 8,
            "max_dynamic_patch": 24,
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": cfg.prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                        },
                    },
                ],
            }
        ],
    }

    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    last_exc: Exception | None = None
    for attempt in range(1, cfg.max_retries + 1):
        try:
            resp = requests.post(
                cfg.api_url,
                headers=headers,
                data=json.dumps(data),
                stream=cfg.stream,
                timeout=300,
            )
            resp.raise_for_status()

            content = (
                _parse_stream_response(resp) if cfg.stream
                else _parse_normal_response(resp)
            )

            if not content.strip():
                raise ValueError("API 返回内容为空")

            # 写入输出文件
            md_path = cfg.output_dir / f"{image_path.stem}.md"
            md_path.write_text(content, encoding="utf-8")
            return f"✅ {image_path.name}"

        except Exception as exc:
            last_exc = exc
            if attempt < cfg.max_retries:
                wait = cfg.retry_backoff ** attempt
                log.warning(
                    "%s 第 %d 次失败，%0.1f 秒后重试: %s",
                    image_path.name, attempt, wait, exc,
                )
                time.sleep(wait)

    return f"❌ {image_path.name}: {last_exc}"


# ---------- 批量处理 ----------

def process_images(cfg: Config) -> None:
    """处理目录中的所有图片并为每个图片生成单独的 Markdown 文件（多线程版本）。"""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = collect_images(cfg.image_dir, cfg.image_extensions)
    if not image_paths:
        log.warning("在 %s 中没有找到图片文件", cfg.image_dir)
        return

    log.info("找到 %d 张图片，开始处理（workers=%d）...", len(image_paths), cfg.max_workers)

    results: list[str] = []
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        futures = {
            executor.submit(process_single_image, path, cfg): path.name
            for path in image_paths
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="处理进度"):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append(f"❌ 异常: {exc}")

    success = sum(1 for r in results if r.startswith("✅"))
    failure = len(results) - success
    log.info("处理完成！成功: %d, 失败: %d", success, failure)

    if failure:
        log.error("失败详情:")
        for r in results:
            if r.startswith("❌"):
                log.error("  %s", r)


# ---------- 入口 ----------

def main() -> None:
    cfg = Config()
    process_images(cfg)


if __name__ == "__main__":
    main()