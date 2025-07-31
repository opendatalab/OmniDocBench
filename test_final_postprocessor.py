#!/usr/bin/env python3

import os
import sys
from datetime import datetime

# Add the tools directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools', 'model_infer'))

from final_ocr_postprocessor import FinalOCRPostprocessor

def test_single_file(markdown_file: str):
    """Test the final postprocessor on a single file"""
    
    # Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://vdi-openai-eastus.openai.azure.com')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
    DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-2024-05-13')
    
    if not AZURE_OPENAI_API_KEY:
        print("Error: AZURE_OPENAI_API_KEY environment variable not set")
        return
    
    print("Final OCR Postprocessor Test")
    print("=" * 50)
    print("Approach: Image-based detection + Ultra-conservative correction + Validation")
    print()
    
    # Initialize processor
    processor = FinalOCRPostprocessor(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, DEPLOYMENT_NAME)
    
    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_path = os.path.join(base_dir, 'demo_data', 'microsoft_ocr_results_markdownonly', markdown_file)
    
    # Try to find corresponding image
    image_file = markdown_file.replace('.md', '.jpg')
    possible_image_paths = [
        os.path.join(base_dir, 'tools', 'model_infer', 'OmniDocBench_dataset', 'images', image_file),
        os.path.join(base_dir, 'demo_data', 'images', image_file),
        os.path.join(base_dir, 'images', image_file),
        # Add more possible image locations if needed
    ]
    
    image_path = None
    for img_path in possible_image_paths:
        if os.path.exists(img_path):
            image_path = img_path
            break
    
    if not os.path.exists(markdown_path):
        print(f"Markdown file not found: {markdown_path}")
        return
    
    if not image_path:
        print(f"Warning: No corresponding image found for {markdown_file}")
        print("Processing without image (will use fallback detection)")
    else:
        print(f"Found corresponding image: {image_path}")
    
    print(f"Processing: {markdown_file}")
    print()
    
    # Create output path
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(base_dir, 'demo_data', 'test_final_postprocessor', timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(markdown_file)[0]
    output_path = os.path.join(output_dir, f"{base_name}_final_postprocessed.md")
    
    # Process file
    result = processor.process_single_file(markdown_path, image_path, output_path)
    
    print()
    print("=" * 50)
    print("RESULTS:")
    print("=" * 50)
    
    if result['success']:
        print(f"Status: SUCCESS - {result['message']}")
        print(f"Changes made: {result['changes_made']}")
        
        print(f"\nDetected errors ({len(result['detected_errors'])}):")
        for i, error in enumerate(result['detected_errors'], 1):
            print(f"  {i}. '{error.get('ocr_text', '')}' → '{error.get('should_be', '')}'")
            print(f"     Type: {error.get('error_type', 'unknown')}, Confidence: {error.get('confidence', 'unknown')}")
            print(f"     Reason: {error.get('reason', 'N/A')}")
        
        if 'validation' in result:
            validation = result['validation']
            print(f"\nValidation ({validation['validation_method']}):")
            print(f"  Approved: {validation['approved']}")
            
            if validation['validation_method'] == 'ground_truth':
                print(f"  Original edit distance: {validation['original_edit_distance']:.4f}")
                print(f"  Corrected edit distance: {validation['corrected_edit_distance']:.4f}")
                print(f"  Improvement: {validation['improvement_percent']:+.2f}%")
                if validation['improvement'] > 0:
                    print(f"  ✓ Edit distance improved by {validation['improvement']:.4f}")
                elif validation['improvement'] < 0:
                    print(f"  ✗ Edit distance degraded by {abs(validation['improvement']):.4f}")
                else:
                    print(f"  - No change in edit distance")
            elif validation['validation_method'] == 'heuristic':
                print(f"  Reason: {validation.get('reason', 'N/A')}")
        
        if result['changes_made']:
            print(f"\nOutput saved to: {output_path}")
            
            # Show file size comparison
            with open(markdown_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            print(f"\nFile size comparison:")
            print(f"  Original: {len(original_text)} characters")
            print(f"  Corrected: {len(result['corrected_text'])} characters")
            
            # Show first 200 chars if changed
            if len(result['detected_errors']) > 0:
                print(f"\nFirst 200 characters:")
                print(f"  Original: {original_text[:200]}...")
                print(f"  Corrected: {result['corrected_text'][:200]}...")
        else:
            print(f"\nNo changes made - original file preserved")
            
    else:
        print(f"Status: FAILED")
        print(f"Error: {result['error']}")

def test_batch_processing():
    """Test batch processing on a few files"""
    
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://vdi-openai-eastus.openai.azure.com')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
    DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-2024-05-13')
    
    if not AZURE_OPENAI_API_KEY:
        print("Error: AZURE_OPENAI_API_KEY environment variable not set")
        return
    
    print("Final OCR Postprocessor Batch Test")
    print("=" * 50)
    
    processor = FinalOCRPostprocessor(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, DEPLOYMENT_NAME)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'demo_data', 'microsoft_ocr_results_markdownonly')
    image_dir = os.path.join(base_dir, 'tools', 'model_infer', 'OmniDocBench_dataset', 'images')
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(base_dir, 'demo_data', 'test_final_batch_postprocessor', f'run_{timestamp}')
    
    # Process just 5 files for testing
    results = processor.process_batch(input_dir, output_dir, image_dir, max_files=20)
    
    print(f"\nBatch processing results:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Processed: {results['processed']}")
    print(f"  Improved: {results['improved']}")
    print(f"  No change: {results['no_change']}")
    print(f"  Failed: {results['failed']}")
    
    # Print edit distance improvement stats
    eds = results.get('edit_distance_stats', {})
    if eds.get('files_with_improvement', 0) > 0:
        print(f"\nEdit Distance Improvements:")
        print(f"  Files with improvement: {eds['files_with_improvement']}")
        print(f"  Average improvement: {eds['avg_improvement_percent']:.2f}%")
        print(f"  Best improvement: {eds['best_improvement']:.2f}%")
        if eds.get('worst_degradation', 0) < 0:
            print(f"  Worst degradation: {eds['worst_degradation']:.2f}%")
    
    # Print per-file improvements for test batch
    print(f"\nPer-file Edit Distance Results:")
    print("=" * 80)
    improved_files = [f for f in results['files'] if f.get('improvement_percent', 0) > 0]
    no_change_files = [f for f in results['files'] if f.get('improvement_percent', 0) == 0 and f['success']]
    degraded_files = [f for f in results['files'] if f.get('improvement_percent', 0) < 0]
    
    if improved_files:
        print(f"\nIMPROVED FILES ({len(improved_files)}):")
        for f in sorted(improved_files, key=lambda x: x.get('improvement_percent', 0), reverse=True):
            print(f"  {f['file']:<50} {f['original_edit_distance']:.4f}→{f['corrected_edit_distance']:.4f} ({f['improvement_percent']:+.1f}%)")
    
    if degraded_files:
        print(f"\nDEGRADED FILES ({len(degraded_files)}):")
        for f in sorted(degraded_files, key=lambda x: x.get('improvement_percent', 0)):
            print(f"  {f['file']:<50} {f['original_edit_distance']:.4f}→{f['corrected_edit_distance']:.4f} ({f['improvement_percent']:+.1f}%)")
    
    if no_change_files:
        print(f"\nNO CHANGE FILES ({len(no_change_files)}):")
        for f in no_change_files:
            print(f"  {f['file']:<50} {f.get('message', 'No errors detected')}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'batch':
            test_batch_processing()
        else:
            markdown_file = sys.argv[1]
            test_single_file(markdown_file)
    else:
        print("Usage:")
        print("  python test_final_postprocessor.py <markdown_file>")
        print("  python test_final_postprocessor.py batch")
        print()
        print("Example:")
        print("  python test_final_postprocessor.py jiaocaineedrop_eng-45646.pdf_30.md")
        print("  python test_final_postprocessor.py batch")