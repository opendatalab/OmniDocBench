#!/usr/bin/env python3

import os
import requests
import json
import time
from tqdm import tqdm
from pathlib import Path

def microsoft_ocr_predict(image_path, endpoint_url="http://oneocr-a10.northcentralus.cloudapp.azure.com:5000/contentunderstanding/layout/syncAnalyze"):
    """Call Microsoft OCR API to process an image"""
    try:
        # Use the pipe table endpoint for pure markdown with tables
        url = f"{endpoint_url}?_outputContentFormat=MarkdownOnly&_usePipeTable=true"
        
        # Prepare headers for binary data
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        
        # Read image file as binary
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Make API call
        response = requests.post(url, headers=headers, data=image_data, timeout=120)
        
        # Debug output
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        response.raise_for_status()
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            # If response is not JSON, treat as plain text
            return {
                'success': True,
                'text': response.text,
                'raw_response': response.text
            }
        
        # Handle different response formats
        if isinstance(result, dict):
            # Check for markdown content
            if 'content' in result:
                return {
                    'success': True,
                    'text': result['content'],
                    'raw_response': result
                }
            elif 'markdown' in result:
                return {
                    'success': True,
                    'text': result['markdown'],
                    'raw_response': result
                }
            elif 'text' in result:
                return {
                    'success': True,
                    'text': result['text'],
                    'raw_response': result
                }
            else:
                # Return the entire result as text if no specific field found
                return {
                    'success': True,
                    'text': json.dumps(result, indent=2),
                    'raw_response': result
                }
        else:
            # If result is not a dict, convert to string
            return {
                'success': True,
                'text': str(result),
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
            result = microsoft_ocr_predict(image_path)
            
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
    output_dir = '../../demo_data/microsoft_ocr_results'
    
    # Make paths absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_folder = os.path.join(script_dir, img_folder)
    output_dir = os.path.join(script_dir, output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
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
    print(f"Endpoint: http://oneocr-a10.northcentralus.cloudapp.azure.com:5000/contentunderstanding/layout/syncAnalyze")
    
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