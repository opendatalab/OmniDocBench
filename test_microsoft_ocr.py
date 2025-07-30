#!/usr/bin/env python3

import os
from tools.model_infer.microsoft_ocr import microsoft_ocr_predict

def test_single_image():
    """Test Microsoft OCR with a single image"""
    
    # Pick the first image from demo data
    img_folder = './demo_data/omnidocbench_demo/images'
    
    if not os.path.exists(img_folder):
        print(f"[ERROR] Image folder not found: {img_folder}")
        return
    
    image_files = [f for f in os.listdir(img_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("[ERROR] No images found in demo data")
        return
    
    # Use the first image for testing
    test_image = os.path.join(img_folder, image_files[0])
    print(f"Testing with image: {test_image}")
    print(f"Image size: {os.path.getsize(test_image)} bytes")
    
    # Test API call
    result = microsoft_ocr_predict(test_image)
    
    if result['success']:
        print("[SUCCESS] API call successful!")
        print(f"Response length: {len(result['text'])} characters")
        print("\n--- Sample Output ---")
        try:
            sample_text = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
            print(sample_text)
        except UnicodeEncodeError:
            print("Sample output contains Unicode characters that cannot be displayed in console")
        
        # Save test result
        with open('./test_microsoft_ocr_output.md', 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"\nFull output saved to: test_microsoft_ocr_output.md")
        
    else:
        print(f"[ERROR] API call failed: {result['error']}")
        if 'raw_response' in result:
            try:
                print(f"Raw response type: {type(result['raw_response'])}")
                if isinstance(result['raw_response'], dict):
                    print(f"Response keys: {list(result['raw_response'].keys())}")
                else:
                    print(f"Raw response: {str(result['raw_response'])[:200]}")
            except UnicodeEncodeError:
                print("Raw response contains Unicode characters")

def test_curl_example():
    """Show equivalent curl command for the API call"""
    
    img_folder = './tools/model_infer/OmniDocBench_dataset/images'
    
    if not os.path.exists(img_folder):
        print(f"[ERROR] Image folder not found: {img_folder}")
        return
    
    image_files = [f for f in os.listdir(img_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("[ERROR] No images found in demo data")
        return
    
    test_image = os.path.join(img_folder, image_files[0])
    abs_path = os.path.abspath(test_image)
    
    print("\n--- Equivalent curl command ---")
    print(f"curl --request POST \\")
    print(f"  --url 'http://oneocr-a10.northcentralus.cloudapp.azure.com:5000/contentunderstanding/layout/syncAnalyze?_outputContentFormat=MarkdownOnly&_usePipeTable=true' \\")
    print(f"  --header 'Content-Type: application/octet-stream' \\")
    print(f"  --data-binary '@{abs_path}'")

if __name__ == '__main__':
    print("Testing Microsoft OCR API...")
    test_single_image()
    test_curl_example()