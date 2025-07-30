#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from tools.model_infer.mistral_ocr import mistral_ocr_predict

# Load environment variables from .env file
load_dotenv()

def test_single_image():
    """Test MistralOCR with a single image"""
    
    # Pick the first image from demo data
    img_folder = './demo_data/omnidocbench_demo/images'
    image_files = [f for f in os.listdir(img_folder) if f.lower().endswith('.jpg')]
    
    if not image_files:
        print("[ERROR] No images found in demo data")
        return
    
    test_image = os.path.join(img_folder, image_files[0])
    print(f"Testing with image: {test_image}")
    
    # Test API call
    result = mistral_ocr_predict(test_image)
    
    if result['success']:
        print("[SUCCESS] API call successful!")
        print(f"Response length: {len(result['text'])} characters")
        print(f"Usage: {result.get('usage', 'N/A')}")
        print("\n--- Sample Output ---")
        try:
            sample_text = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
            print(sample_text)
        except UnicodeEncodeError:
            print("Sample output contains Unicode characters that cannot be displayed in console")
        
        # Save test result
        with open('./test_mistral_output.md', 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"\nFull output saved to: test_mistral_output.md")
        
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

if __name__ == '__main__':
    test_single_image()