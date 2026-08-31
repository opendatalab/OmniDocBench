import os
import base64
import argparse
import sys
from openai import OpenAI, APIConnectionError
from tqdm import tqdm


def encode_image(image_path):
    """
    Encode the image file to base64 string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
    Process a single image file.
    """
    try:
        # Skip images that have already been converted
        output_path = os.path.join(result_dir, image_file + ".md")
        if os.path.exists(output_path):
            return f"Skipped existing file: {image_file}"

        image_path = os.path.join(image_dir, image_file)
        base64_image = encode_image(image_path)
        data_url = f"data:image/jpeg;base64,{base64_image}"

        response = client.chat.completions.create(
            model=model_name,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    }
                ],
            }],
            stream=True,
            timeout=10000,
        )

        result = ""
        for chunk in response:
            if chunk.choices[0].finish_reason is not None:
                break
            content = chunk.choices[0].delta.content
            if content is not None:
                result += content

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)

        return f"Successfully processed: {image_file}"
    except APIConnectionError as e:
        return f"Connection timeout: {image_file}, error: {str(e)}"
    except Exception as e:
        return f"Failed to process: {image_file}, error: {str(e)}"


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Convert images to Markdown via the OrcaRouter gateway")
    parser.add_argument(
        "--base_url",
        type=str,
        default="https://api.orcarouter.ai/v1",
        help="OrcaRouter OpenAI-compatible API base URL",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default="",
        help="OrcaRouter API key (defaults to the ORCAROUTER_API_KEY environment variable)",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="orcarouter/auto",
        help="Model name routed by OrcaRouter, e.g. orcarouter/auto or provider/model-name",
    )
    parser.add_argument(
        "--image_dir",
        type=str,
        default="./images",
        help="Directory containing the input images",
    )
    parser.add_argument(
        "--result_dir",
        type=str,
        default="./results",
        help="Directory to store the generated Markdown files",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    api_key = args.api_key or os.environ.get("ORCAROUTER_API_KEY", "")
    if not api_key:
        print("Please provide an API key via --api_key or the ORCAROUTER_API_KEY environment variable.")
        sys.exit(1)

    os.makedirs(args.image_dir, exist_ok=True)
    os.makedirs(args.result_dir, exist_ok=True)

    client = OpenAI(
        base_url=args.base_url,
        api_key=api_key,
    )

    # Collect all images to process
    image_files = [f for f in os.listdir(args.image_dir)
                   if f.endswith((".jpg", ".png", ".jpeg"))]

    # Filter out images that have already been converted
    existing_files = []
    new_files = []
    for image_file in image_files:
        output_path = os.path.join(args.result_dir, image_file + ".md")
        if os.path.exists(output_path):
            existing_files.append(image_file)
        else:
            new_files.append(image_file)

    print(f"Found {len(image_files)} image files")
    print(f"{len(existing_files)} already processed, {len(new_files)} to process")

    if len(new_files) == 0:
        print("All images have been processed already!")
        sys.exit(0)

    # Process images sequentially
    completed_count = 0
    failed_count = 0

    for image_file in tqdm(new_files, desc="Processing images"):
        result = process_image(client, image_file, args.image_dir, args.result_dir, args.model_name)
        if result.startswith("Successfully"):
            completed_count += 1
        else:
            failed_count += 1
            print(result)

    print(f"\nProcessing summary:")
    print(f"  Successfully processed: {completed_count}")
    print(f"  Skipped existing: {len(existing_files)}")
    print(f"  Failed: {failed_count}")
    print(f"  Results saved in: {args.result_dir}")
