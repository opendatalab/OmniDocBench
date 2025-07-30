#!/usr/bin/env python3

import os
import base64
import requests
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure MistralOCR configuration
AZURE_ENDPOINT = os.environ.get('AZURE_MISTRAL_OCR_ENDPOINT', 'https://your-endpoint.openai.azure.com/')
AZURE_API_KEY = os.environ.get('AZURE_MISTRAL_OCR_API_KEY', 'your-api-key')
AZURE_API_VERSION = os.environ.get('AZURE_API_VERSION', '2024-02-01')
DEPLOYMENT_NAME = os.environ.get('MISTRAL_OCR_DEPLOYMENT_NAME', 'mistral-ocr')

def image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def mistral_ocr_predict(image_path, prompt="Convert this document image to markdown format. Extract all text, tables, formulas, and maintain the document structure and reading order."):
    """Call Azure MistralOCR API to process an image"""
    try:
        # Convert image to base64
        image_base64 = image_to_base64(image_path)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {AZURE_API_KEY}'
        }
        
        # Construct API URL for Azure Mistral OCR
        url = f"{AZURE_ENDPOINT.rstrip('/')}/v1/ocr"
        
        # Prepare payload for Azure Mistral OCR
        payload = {
            "model": DEPLOYMENT_NAME,
            "document": {
                "type": "document_url",
                "document_url": f"data:image/jpeg;base64,{image_base64}"
            },
            "include_image_base64": True
        }
        
        # Make API call
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # Debug output
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Length: {len(response.text)}")
        try:
            print(f"Response Text (first 200 chars): {response.text[:200]}")
        except UnicodeEncodeError:
            print("Response Text contains Unicode characters that cannot be displayed")
        
        response.raise_for_status()
        
        try:
            result = response.json()
        except:
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {response.text[:500]}',
                'status_code': response.status_code
            }
        
        # Check for OCR result in Mistral OCR response format
        if result and 'pages' in result and len(result['pages']) > 0:
            # Extract text from all pages
            all_text = ""
            for page in result['pages']:
                if 'markdown' in page:
                    all_text += page['markdown'] + "\n"
                elif 'text' in page:
                    all_text += page['text'] + "\n"
            
            if all_text.strip():
                return {
                    'success': True,
                    'text': all_text.strip(),
                    'usage': result.get('usage_info', {})
                }
        elif result and 'text' in result:
            return {
                'success': True,
                'text': result['text'],
                'usage': result.get('usage', {})
            }
        elif result and 'content' in result:
            return {
                'success': True,
                'text': result['content'],
                'usage': result.get('usage', {})
            }
        
        return {
            'success': False,
            'error': 'No text content in response',
            'raw_response': result
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_image(image_path, output_dir, max_retries=3):
    """Process a single image with retry logic"""
    img_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, img_name[:-4] + '.md')
    
    # Skip if already processed
    if os.path.exists(output_path):
        print(f"Skipping {img_name} - already processed")
        return True
    
    for attempt in range(max_retries):
        try:
            print(f"Processing {img_name} (attempt {attempt + 1}/{max_retries})")
            result = mistral_ocr_predict(image_path)
            
            if result['success'] and result.get('text'):
                # Save markdown output
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(result['text'])
                print(f"✅ Successfully processed: {img_name}")
                return True
            else:
                print(f"❌ Attempt {attempt + 1} failed: {result.get('error', 'No text returned')}")
                
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    # Log failed images
    with open(os.path.join(output_dir, 'failed_images.txt'), 'a', encoding='utf-8') as f:
        f.write(f"{image_path}\n")
    print(f"❌ Failed to process after {max_retries} attempts: {img_name}")
    return False

def main():
    """Main function to process all images"""
    
    # Configuration
    img_folder = './OmniDocBench_dataset/images'
    output_dir = '../../demo_data/mistral_ocr_results'
    
    # Make paths absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_folder = os.path.join(script_dir, img_folder)
    output_dir = os.path.join(script_dir, output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Check credentials
    if AZURE_API_KEY == 'your-api-key' or 'your-endpoint' in AZURE_ENDPOINT:
        print("❌ Please set your Azure credentials!")
        print("Set environment variables:")
        print("  $env:AZURE_MISTRAL_OCR_ENDPOINT='https://your-endpoint.openai.azure.com/'")
        print("  $env:AZURE_MISTRAL_OCR_API_KEY='your-api-key'")
        print("  $env:MISTRAL_OCR_DEPLOYMENT_NAME='mistral-ocr'")
        return
    
    # Get image files
    if not os.path.exists(img_folder):
        print(f"❌ Image folder not found: {img_folder}")
        return
        
    image_files = [f for f in os.listdir(img_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"❌ No image files found in: {img_folder}")
        return
    
    print(f"Found {len(image_files)} images to process")
    print(f"Input folder: {img_folder}")
    print(f"Output folder: {output_dir}")
    
    # Process images
    successful = 0
    for img_file in tqdm(image_files, desc="Processing images"):
        image_path = os.path.join(img_folder, img_file)
        if process_image(image_path, output_dir):
            successful += 1
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n🎉 Processing complete!")
    print(f"✅ Successfully processed: {successful}/{len(image_files)} images")
    print(f"📁 Results saved to: {output_dir}")
    
    if successful < len(image_files):
        print(f"❌ Check failed_images.txt for errors")

if __name__ == '__main__':
    main()