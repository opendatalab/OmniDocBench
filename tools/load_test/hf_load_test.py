#!/usr/bin/env python3
"""
Run a configurable load test against the Hugging Face OpenAI-compatible endpoint
using all images under `data/publicBench_data/images`.

The script relies exclusively on Python's standard library to orchestrate
concurrent requests, collect latency metrics, and persist responses.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
DEFAULT_IMAGE_DIR = DATA_ROOT / "publicBench_data" / "images"
DEFAULT_ENDPOINT = (
    "https://fhuwo4wg30kufkv1.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
    #"https://czqg2ofkq3whhgr6.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
    #"https://czqg2ofkq3whhgr6.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
    #"https://f1zls6v8h1mb611e.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
    #"https://zxrgjmcqn28by9g9.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions"
)
DEFAULT_MODEL = "opendatalab/MinerU2.5-2509-1.2B"#"rednote-hilab/dots.ocr"#"nanonets/Nanonets-OCR2-3B"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "runs" / "load_tests"
DEFAULT_PROMPT="""Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]

2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].

3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown.

4. Constraints:
    - The output text must be the original text from the image, with no translation.
    - All layout elements must be sorted according to human reading order.

5. Final Output: The entire output must be a single JSON object.
"""
#"Extract the text from the above document as if you were reading it naturally. Return the tables in html format. Return the equations in LaTeX representation. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes.",


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute a concurrent load test against a Hugging Face inference endpoint."
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=DEFAULT_IMAGE_DIR,
        help="Directory containing input page images (default: data/publicBench_data/images).",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default=DEFAULT_ENDPOINT,
        help="OpenAI-compatible chat completions endpoint URL.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model identifier to include in the request payload.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        help="User prompt appended to each request.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Number of concurrent requests to maintain.",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay (seconds) between scheduling consecutive requests.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Optionally limit the number of images processed.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to persist the JSON report (defaults to runs/load_tests/<timestamp>.json).",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face API token. Overrides HF_TOKEN environment variable if provided.",
    )
    return parser.parse_args()


def _detect_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".bmp":
        return "image/bmp"
    if suffix in {".tif", ".tiff"}:
        return "image/tiff"
    return "application/octet-stream"


def _load_image_as_data_uri(path: Path) -> str:
    mime_type = _detect_mime_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _parse_response_text(choice_payload: Dict) -> str:
    message = choice_payload.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    fragments.append(str(text))
        return "".join(fragments)
    return ""


def _perform_request(
    image_path: Path,
    endpoint_url: str,
    model: str,
    prompt: str,
    token: str,
    timeout: float,
) -> Dict:
    """
    Execute a single inference request and return structured metadata.
    """
    request_started = time.perf_counter()
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": _load_image_as_data_uri(image_path), "detail": "high"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "stream": False,
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        endpoint_url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            elapsed = time.perf_counter() - request_started
            response_body = response.read().decode("utf-8")
            parsed = json.loads(response_body)
            choices = parsed.get("choices") or []
            first_choice = choices[0] if choices else {}
            text = _parse_response_text(first_choice)
            return {
                "image": image_path.name,
                "status": "ok",
                "http_status": response.status,
                "latency_sec": elapsed,
                "response_text": text,
                "raw_response": parsed,
            }
    except HTTPError as err:
        elapsed = time.perf_counter() - request_started
        error_body = err.read().decode("utf-8", errors="replace")
        return {
            "image": image_path.name,
            "status": "error",
            "http_status": err.code,
            "latency_sec": elapsed,
            "error": f"HTTPError: {err.reason}",
            "error_body": error_body,
        }
    except URLError as err:
        elapsed = time.perf_counter() - request_started
        return {
            "image": image_path.name,
            "status": "error",
            "http_status": None,
            "latency_sec": elapsed,
            "error": f"URLError: {err.reason}",
        }
    except Exception as err:
        elapsed = time.perf_counter() - request_started
        return {
            "image": image_path.name,
            "status": "error",
            "http_status": None,
            "latency_sec": elapsed,
            "error": f"UnexpectedError: {err}",
        }


def main() -> None:
    args = parse_args()
    token = args.hf_token or os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN environment variable not set and no --hf-token provided.")

    if not args.image_dir.exists():
        raise FileNotFoundError(f"Image directory {args.image_dir} does not exist.")

    supported_suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    image_paths = sorted(
        [p for p in args.image_dir.iterdir() if p.is_file() and p.suffix.lower() in supported_suffixes],
        key=lambda p: p.name,
    )
    if args.max_images is not None:
        image_paths = image_paths[: args.max_images]

    if not image_paths:
        raise RuntimeError(f"No files found in {args.image_dir}.")

    output_path = args.output
    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = DEFAULT_OUTPUT_DIR / f"nanonets_load_test_{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.concurrency < 1:
        raise ValueError("Concurrency must be at least 1.")
    if args.delay < 0:
        raise ValueError("Delay must be non-negative.")

    print(
        f"Starting load test with {len(image_paths)} images | "
        f"concurrency={args.concurrency} | delay={args.delay}s | timeout={args.request_timeout}s"
    )

    run_started_at = datetime.now(timezone.utc)
    run_started = time.perf_counter()
    request_results: List[Dict] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_to_image = {}
        for image_path in image_paths:
            future = executor.submit(
                _perform_request,
                image_path,
                args.endpoint_url,
                args.model,
                args.prompt,
                token,
                args.request_timeout,
            )
            future_to_image[future] = image_path.name
            if args.delay > 0:
                time.sleep(args.delay)

        for idx, future in enumerate(as_completed(future_to_image), start=1):
            result = future.result()
            request_results.append(result)
            name = result["image"]
            status = result["status"]
            latency = result.get("latency_sec", 0.0)
            timestamp = time.time()
            formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{idx}/{len(image_paths)}] {name}: {status} ({latency:.2f}s) [{formatted_time}]")

    duration = time.perf_counter() - run_started
    run_finished_at = datetime.now(timezone.utc)
    successes = sum(1 for r in request_results if r["status"] == "ok")
    failures = len(request_results) - successes

    report = {
        "metadata": {
            "run_started_at": run_started_at.isoformat(),
            "run_finished_at": run_finished_at.isoformat(),
            "image_dir": str(args.image_dir),
            "endpoint_url": args.endpoint_url,
            "model": args.model,
            "prompt": args.prompt,
            "concurrency": args.concurrency,
            "request_timeout_sec": args.request_timeout,
            "delay_between_submissions_sec": args.delay,
            "image_count": len(image_paths),
            "successes": successes,
            "failures": failures,
            "duration_sec": duration,
            "throughput_images_per_sec": len(image_paths) / duration if duration > 0 else None,
        },
        "results": request_results,
    }

    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2, ensure_ascii=False)

    print(f"Load test complete. Results written to {output_path}")


if __name__ == "__main__":
    main()
