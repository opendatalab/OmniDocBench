#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import requests
from typing import Dict, Any, Optional

def azure_openai_postprocess(markdown_text: str, 
                            endpoint: str,
                            api_key: str,
                            image_path: str = None,
                            deployment_name: str = "gpt4o-2024-05-13",
                            api_version: str = "2024-02-01") -> Dict[str, Any]:
    # Construct the full URL
    url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    
    # Define the system prompt for OCR postprocessing
    system_prompt = """You are a conservative OCR error corrector. Your ONLY job is to fix obvious OCR mistakes        
    while preserving everything else exactly as is.

    CRITICAL RULES - DO NOT:
    - Change any mathematical expressions, formulas, or LaTeX      
    (anything with $, \\, ^, _, etc.)
    - Modify table structure, markdown formatting, or table        
    separators (|, -, etc.)
    - Add, remove, or rearrange content
    - Change line breaks, paragraph structure, or spacing 
    between elements
    - Convert normal text into LaTeX or mathematical notation      
    - "Improve" or "enhance" the text beyond fixing clear OCR      
    errors
    - Change headers, lists, or any markdown structure elements    
    - Modify figure references, page headers, or page footers      
    - Do not add any new content or context. Do not add anything that isn't actually present in the original image.
    ONLY FIX these obvious OCR errors:
    1. Clear number spacing ONLY in plain text (e.g., "1 0" →      
    "10" but NOT in formulas)
    2. Obviously wrong single characters (e.g., "teh" → "the")     
    3. Clear word fragments where letters are separated by         
    spaces
    4. Remove obviously foreign characters that don't belong       
    (like random Chinese in English text)

    If you are unsure whether something is an error, DO NOT        
    change it. When in doubt, preserve the original.

    Compare with the image (if provided) only to verify obvious    
    mistakes. Do not use the image to "improve" or add 
    content.

    IMPORTANT: Format your response as follows:
    1. First, provide a "CORRECTIONS LOG" section listing ONLY     
    the obvious errors you fixed
    2. Then provide the corrected text with minimal changes        

    Example format:
    ```
    ## CORRECTIONS LOG
    - Line 3: Fixed obvious number spacing "1 0" → "10" (clear     
    OCR error in plain text)
    - Line 8: Fixed obvious typo "teh" → "the" 
    - Line 12: Removed random foreign character "রেন" (doesn't     
    belong in English text)

    ## CORRECTED TEXT
    [corrected text with minimal changes]
    ```

    If no obvious errors are found, respond with:
    ```
    ## CORRECTIONS LOG
    No obvious OCR errors found that meet the conservative         
    correction criteria.

    ## CORRECTED TEXT
    [original text unchanged]
    ```"""

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    # Prepare user message content
    user_content = []
    
    # Add image if provided
    if image_path and os.path.exists(image_path):
        import base64
        
        # Read and encode image
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine image type
        image_ext = os.path.splitext(image_path)[1].lower()
        if image_ext in ['.jpg', '.jpeg']:
            image_type = 'jpeg'
        elif image_ext == '.png':
            image_type = 'png'
        else:
            image_type = 'jpeg'  # default
        
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{image_type};base64,{image_data}"
            }
        })
        
        user_content.append({
            "type": "text",
            "text": f"Here is the original document image and the OCR-generated markdown text that needs correction:\n\n{markdown_text}"
        })
    else:
        # Text only if no image
        user_content.append({
            "type": "text", 
            "text": f"Please fix the OCR errors in this markdown document:\n\n{markdown_text}"
        })
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "top_p": 0.95
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # Add detailed error logging
        if response.status_code != 200:
            error_detail = f"Status {response.status_code}: {response.text}"
            print(f"API Error: {error_detail}")
            return {
                'success': False,
                'error': f'API request failed: {error_detail}'
            }
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            full_response = result['choices'][0]['message']['content']
            
            # Parse the response to separate corrections log and corrected text
            corrections_log = ""
            corrected_text = full_response
            
            if "## CORRECTIONS LOG" in full_response and "## CORRECTED TEXT" in full_response:
                parts = full_response.split("## CORRECTED TEXT")
                if len(parts) == 2:
                    log_part = parts[0].replace("## CORRECTIONS LOG", "").strip()
                    corrected_text = parts[1].strip()
                    corrections_log = log_part
            
            return {
                'success': True,
                'text': corrected_text,
                'corrections_log': corrections_log,
                'full_response': full_response,
                'raw_response': result
            }
        else:
            return {
                'success': False,
                'error': 'No choices in API response'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def process_markdown_file(input_path: str, 
                         output_path: str,
                         endpoint: str,
                         api_key: str,
                         image_path: str = None,
                         deployment_name: str = "gpt-4o",
                         max_retries: int = 3) -> bool:
    """
    Process a single markdown file with retry logic
    
    Args:
        input_path: Path to input markdown file
        output_path: Path to save corrected markdown
        endpoint: Azure OpenAI endpoint
        api_key: Azure OpenAI API key
        deployment_name: Azure OpenAI deployment name
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    
    # Skip if output already exists
    if os.path.exists(output_path):
        print(f"Skipping {os.path.basename(input_path)} - already processed")
        return True
    
    try:
        # Read input markdown
        with open(input_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # Skip empty files
        if not markdown_text.strip():
            print(f"Skipping empty file: {os.path.basename(input_path)}")
            return True
        
        # Skip very large files (>50KB) to avoid token limits
        if len(markdown_text) > 50000:
            print(f"Skipping large file ({len(markdown_text)} chars): {os.path.basename(input_path)}")
            # Copy original file instead
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            return True
        
        # Process with retry logic
        for attempt in range(max_retries):
            try:
                print(f"Processing {os.path.basename(input_path)} (attempt {attempt + 1}/{max_retries})")
                
                result = azure_openai_postprocess(
                    markdown_text=markdown_text,
                    endpoint=endpoint,
                    api_key=api_key,
                    image_path=image_path,
                    deployment_name=deployment_name
                )
                
                if result['success'] and result.get('text'):
                    # Save corrected markdown
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result['text'])
                    
                    # Save corrections log if available
                    if result.get('corrections_log'):
                        # Determine log directory from output path
                        output_dir = os.path.dirname(os.path.dirname(output_path))  # Go up from corrected_gpt to base
                        log_dir = os.path.join(output_dir, 'logs')
                        base_name = os.path.splitext(os.path.basename(input_path))[0]
                        log_path = os.path.join(log_dir, f"{base_name}_corrections.log")
                        
                        with open(log_path, 'w', encoding='utf-8') as f:
                            f.write(f"OCR Corrections for: {os.path.basename(input_path)}\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(result['corrections_log'])
                        print(f"✅ Successfully processed: {os.path.basename(input_path)} (with corrections log)")
                    else:
                        print(f"✅ Successfully processed: {os.path.basename(input_path)}")
                    return True
                else:
                    print(f"❌ Attempt {attempt + 1} failed: {result.get('error', 'No text returned')}")
                    
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # If all attempts failed, copy original file
        print(f"❌ Failed after {max_retries} attempts, copying original: {os.path.basename(input_path)}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        return False
        
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(input_path)}: {str(e)}")
        return False


def main():
    """Main function to process all markdown files"""
    
    # Configuration - Update these with your Azure OpenAI details
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://vdi-openai-eastus.openai.azure.com')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
    DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-2024-05-13')
    
    # Input and output directories
    input_dir = '../../demo_data/microsoft_ocr_results_markdownonly'
    output_base_dir = '../../demo_data/microsoft_ocr_results_gpt_processed'
    
    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(output_base_dir, f"run_{timestamp}")
    
    # Make paths absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, input_dir)
    run_dir = os.path.join(script_dir, run_dir)
    
    # Create organized output directories with timestamp
    corrected_dir = os.path.join(run_dir, "corrected_gpt")
    log_dir = os.path.join(run_dir, "logs")
    
    # Validate configuration
    if not AZURE_OPENAI_API_KEY:
        print("❌ Error: AZURE_OPENAI_API_KEY environment variable not set")
        print("Please set your Azure OpenAI API key:")
        print("export AZURE_OPENAI_API_KEY='your-api-key-here'")
        return
    
    if 'your-resource' in AZURE_OPENAI_ENDPOINT:
        print("❌ Error: Please update AZURE_OPENAI_ENDPOINT with your actual endpoint")
        print("export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'")
        return
    
    # Create output directories
    os.makedirs(corrected_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    # Get markdown files
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    markdown_files = [f for f in os.listdir(input_dir) if f.endswith('.md')]
    
    if not markdown_files:
        print(f"❌ No markdown files found in: {input_dir}")
        return
    
    print(f"Found {len(markdown_files)} markdown files to process")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {run_dir}")
    print(f"  - Corrected files: {corrected_dir}")
    print(f"  - Correction logs: {log_dir}")
    print(f"Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"Deployment: {DEPLOYMENT_NAME}")
    print(f"Run timestamp: {timestamp}")
    
    # Process files
    successful = 0
    failed = 0
    
    # Create failed files log
    failed_log = os.path.join(run_dir, 'failed_files.txt')
    
    for md_file in tqdm(markdown_files, desc="Processing markdown files"):
        input_path = os.path.join(input_dir, md_file)
        output_path = os.path.join(corrected_dir, md_file)
        
        if process_markdown_file(
            input_path=input_path,
            output_path=output_path,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            deployment_name=DEPLOYMENT_NAME
        ):
            successful += 1
        else:
            failed += 1
            # Log failed file
            with open(failed_log, 'a', encoding='utf-8') as f:
                f.write(f"{input_path}\n")
        
        # Rate limiting - Azure OpenAI has rate limits
        time.sleep(1)
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {successful}/{len(markdown_files)} files")
    print(f"Failed: {failed}/{len(markdown_files)} files")
    print(f"Results saved to: {run_dir}")
    print(f"  - Corrected files: {corrected_dir}")
    print(f"  - Correction logs: {log_dir}")
    
    if failed > 0:
        print(f"Check {failed_log} for failed files")

if __name__ == '__main__':
    main()