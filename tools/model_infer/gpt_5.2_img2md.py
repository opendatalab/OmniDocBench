import os
import asyncio
import aiohttp
import base64
import time
from pathlib import Path


API_KEY = "sk-XXX"
BASE_URL = "http://XX"

INPUT_DIR = "./image"  
OUTPUT_DIR = "./output_md"
MAX_RETRIES = 3  # set retry times
REQUEST_SLEEP = 5  # set sleep time(seconds)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

prompt = r'''You are an AI assistant specialized in converting PDF images to Markdown format. Please follow these instructions for the conversion:

        1. Text Processing:
        - Accurately recognize all text content in the PDF image without guessing or inferring.
        - Convert the recognized text into Markdown format.
        - Maintain the original document structure, including headings, paragraphs, lists, etc.

        2. Mathematical Formula Processing:
        - Convert all mathematical formulas to LaTeX format.
        - Enclose inline formulas with \( \). For example: This is an inline fo\rmula \( E = mc^2 \)
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
        '''

async def process_image(session, image_path, retry_count=0):
    try:
        with open(image_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        async with session.post(
            url=f"{BASE_URL}/chat/completions",
            json={
                # "model": "gemini-3-flash-preview", 
                # "model": "gemini-3-pro-preview", 
                "model": "gpt-5.2", 
                # "model": "gpt-5.2-pro", 
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]}
                ],
            },
            headers=headers
        ) as response:
            await asyncio.sleep(REQUEST_SLEEP)
            print(response)
            
            if response.status == 200:
                result = await response.json()
                print(result)
                markdown_content = result['choices'][0]['message']['content']
                
                if not markdown_content or markdown_content.strip() == "":
                    if retry_count < MAX_RETRIES:
                        print(f"Received empty response, retrying ({retry_count + 1}/{MAX_RETRIES}): {image_path}")
                        return await process_image(session, image_path, retry_count + 1)
                    else:
                        print(f"The maximum number of retries has been reached, and the process failed: {image_path}")
                        return False
                
                markdown_content = clean_markdown(markdown_content)
                
                file_name = os.path.basename(image_path)
                base_name = ".".join(file_name.split(".")[:-1])
                
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                md_path = os.path.join(OUTPUT_DIR, f"{base_name}.md")
                
                with open(md_path, 'w', encoding='utf-8') as md_file:
                    md_file.write(markdown_content)
                
                print(f"Successfully processed {image_path} -> {md_path}")
                return True
            else:
                # === 新增这两行 ===
                error_text = await response.text()
                print(f"Server Error Details: {error_text}")
                if retry_count < MAX_RETRIES:
                    print(f"Request failed, status code: {response.status}， retrying ({retry_count + 1}/{MAX_RETRIES}): {image_path}")
                    return await process_image(session, image_path, retry_count + 1)
                else:
                    print(f"The maximum number of retries has been reached, and the process failed: {image_path}")
                    return False
    except Exception as e:
        await asyncio.sleep(REQUEST_SLEEP)  
        if retry_count < MAX_RETRIES:
            print(f"Handling exception, retrying ({retry_count + 1}/{MAX_RETRIES}): {image_path}, Error: {e}")
            return await process_image(session, image_path, retry_count + 1)
        else:
            print(f"The maximum number of retries has been reached, and the process failed: {image_path}, Error: {e}")
            return False

def clean_markdown(markdown_text):
    if markdown_text.strip().startswith("```markdown"):
        markdown_text = markdown_text.strip()[len("```markdown"):].strip()
    if markdown_text.strip().endswith("```"):
        markdown_text = markdown_text.strip()[:-len("```")].strip()
    return markdown_text

async def process_directory(file_extensions=None):
    if file_extensions is None:
        file_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    
    files_to_process = []
    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if any(file.lower().endswith(ext) for ext in file_extensions):
                files_to_process.append(os.path.join(root, file))
    
    if not files_to_process:
        print(f"Not find img in {INPUT_DIR}")
        return
    
    print(f"Find  {len(files_to_process)} file to process")
    
    processed_files = []
    if os.path.exists(OUTPUT_DIR):
        existing_md_files = [os.path.splitext(f)[0] for f in os.listdir(OUTPUT_DIR) if f.endswith('.md')]
        files_to_process = [f for f in files_to_process if os.path.splitext(os.path.basename(f))[0] not in existing_md_files]
        processed_files = len(existing_md_files)
        print(f"Skip {processed_files} files")
    
    if not files_to_process:
        print("All files have been processed.")
        return
    
    print(f"Start process {len(files_to_process)} files")
    
    remaining_files = files_to_process.copy()
    failed_files = []
    
    timeout_settings = aiohttp.ClientTimeout(total=300, connect=60)
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout_settings) as session:
        while remaining_files:
            current_file = remaining_files.pop(0)
            print(f"Processing ({len(files_to_process) - len(remaining_files)}/{len(files_to_process)}): {current_file}")
            
            result = await process_image(session, current_file)
            if not result:
                failed_files.append(current_file)
    
    while failed_files:
        print(f"\nThere are  {len(failed_files)} more files that failed to process，retrying...")
        
        remaining_files = failed_files.copy()
        failed_files = []

        timeout_settings = aiohttp.ClientTimeout(total=300, connect=60)
        
        async with aiohttp.ClientSession(trust_env=True, timeout=timeout_settings) as session:
            while remaining_files:
                current_file = remaining_files.pop(0)
                print(f"Reprocess ({len(files_to_process) - len(remaining_files) - len(failed_files)}/{len(files_to_process)}): {current_file}")
                
                result = await process_image(session, current_file)
                if not result:
                    failed_files.append(current_file)
    
    print(f"\n{len(files_to_process)} files has been converted to markdown")

async def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.listdir(INPUT_DIR):
        print(f"Input dir {INPUT_DIR} is empty, Please put your images in {INPUT_DIR} and run again.")
        return
    
    file_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    # if extensions_input.strip():
    #     file_extensions = [ext.strip() for ext in extensions_input.split(',')]
    # else:
    #     file_extensions = None

    print(f"处理以下格式的文件: {file_extensions}")
    
    await process_directory(file_extensions)

if __name__ == "__main__":
    asyncio.run(main()) 