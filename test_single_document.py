#!/usr/bin/env python3
"""
Test Azure OpenAI postprocessing on a single document
"""

import os
import sys
import argparse
from pathlib import Path

# Add the tools directory to Python path
tools_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'model_infer')
sys.path.insert(0, tools_path)

try:
    from azure_openai_postprocess import azure_openai_postprocess
except ImportError as e:
    print(f"❌ Error importing azure_openai_postprocess: {e}")
    print(f"Looking for module in: {tools_path}")
    print("Make sure the file exists at: tools/model_infer/azure_openai_postprocess.py")
    sys.exit(1)

def list_available_files(directory, limit=10):
    """List available markdown files in the directory"""
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []
    
    md_files = [f for f in os.listdir(directory) if f.endswith('.md')]
    print(f"Found {len(md_files)} markdown files. Showing first {limit}:")
    
    for i, filename in enumerate(md_files[:limit]):
        file_path = os.path.join(directory, filename)
        file_size = os.path.getsize(file_path)
        print(f"  {i+1}. {filename} ({file_size} bytes)")
    
    if len(md_files) > limit:
        print(f"  ... and {len(md_files) - limit} more files")
    
    return md_files

def test_single_document(file_path, image_path=None, output_dir=None):
    """Test postprocessing on a single document"""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Get credentials from environment
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-2024-05-13')
    
    if not endpoint or not api_key:
        print("❌ Error: Missing Azure OpenAI credentials")
        print("Please set environment variables:")
        print("  AZURE_OPENAI_ENDPOINT")
        print("  AZURE_OPENAI_API_KEY")
        print("  AZURE_OPENAI_DEPLOYMENT (optional)")
        return False
    
    print(f"=== Testing Single Document Processing ===")
    print(f"Markdown file: {os.path.basename(file_path)}")
    print(f"Size: {os.path.getsize(file_path)} bytes")
    if image_path:
        if os.path.exists(image_path):
            print(f"Image file: {os.path.basename(image_path)}")
            print(f"Image size: {os.path.getsize(image_path)} bytes")
        else:
            print(f"⚠️  Image file not found: {image_path}")
            image_path = None
    else:
        print("No image provided - using text-only mode")
    print(f"Endpoint: {endpoint}")
    print(f"Deployment: {deployment}")
    print()
    
    try:
        # Read the original file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Show preview of original content
        print("Original content preview:")
        print("-" * 50)
        preview_lines = original_content.split('\n')[:10]
        for i, line in enumerate(preview_lines, 1):
            print(f"{i:2d}: {line}")
        if len(original_content.split('\n')) > 10:
            print("    ... (content truncated)")
        print("-" * 50)
        print()
        
        # Skip very large files
        if len(original_content) > 50000:
            print(f"⚠️  File is large ({len(original_content)} chars). This may hit token limits.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return False
        
        print("Processing with Azure OpenAI...")
        
        # Process the content
        result = azure_openai_postprocess(
            markdown_text=original_content,
            endpoint=endpoint,
            api_key=api_key,
            image_path=image_path,
            deployment_name=deployment
        )
        
        if result['success']:
            print("✅ Processing successful!")
            
            # Show corrections log if available
            if result.get('corrections_log') and result['corrections_log'].strip():
                print("\nCorrections made:")
                print("-" * 30)
                print(result['corrections_log'])
                print("-" * 30)
            else:
                print("\nNo corrections were needed or logged.")
            
            # Show preview of corrected content
            corrected_content = result['text']
            print("\nCorrected content preview:")
            print("-" * 50)
            preview_lines = corrected_content.split('\n')[:10]
            for i, line in enumerate(preview_lines, 1):
                print(f"{i:2d}: {line}")
            if len(corrected_content.split('\n')) > 10:
                print("    ... (content truncated)")
            print("-" * 50)
            
            # Save results to organized folders
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            if output_dir:
                # Create organized folder structure
                corrected_dir = os.path.join(output_dir, "corrected_gpt")
                log_dir = os.path.join(output_dir, "logs")
                os.makedirs(corrected_dir, exist_ok=True)
                os.makedirs(log_dir, exist_ok=True)
                
                corrected_path = os.path.join(corrected_dir, f"{base_name}.md")
                log_path = os.path.join(log_dir, f"{base_name}_corrections.log")
            else:
                # Default to current directory with organized folders
                corrected_dir = "corrected_gpt"
                log_dir = "logs"
                os.makedirs(corrected_dir, exist_ok=True)
                os.makedirs(log_dir, exist_ok=True)
                
                corrected_path = os.path.join(corrected_dir, f"{base_name}.md")
                log_path = os.path.join(log_dir, f"{base_name}_corrections.log")
            
            # Save corrected markdown
            with open(corrected_path, 'w', encoding='utf-8') as f:
                f.write(corrected_content)
            print(f"\n📁 Corrected file saved to: {corrected_path}")
            
            # Save corrections log if available
            if result.get('corrections_log') and result['corrections_log'].strip():
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(f"OCR Corrections for: {os.path.basename(file_path)}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(result['corrections_log'])
                print(f"📄 Corrections log saved to: {log_path}")
            
            # Show comparison stats
            original_lines = len(original_content.split('\n'))
            corrected_lines = len(corrected_content.split('\n'))
            print(f"\nComparison:")
            print(f"  Original:  {len(original_content)} chars, {original_lines} lines")
            print(f"  Corrected: {len(corrected_content)} chars, {corrected_lines} lines")
            
            return True
            
        else:
            print(f"❌ Processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test OCR postprocessing on a single document')
    parser.add_argument('--file', '-f', 
                       help='Specific file to process (filename only, not full path)')
    parser.add_argument('--image', '-i',
                       help='Path to original image file (optional)')
    parser.add_argument('--input-dir', 
                       default='demo_data/microsoft_ocr_results_markdownonly',
                       help='Input directory containing OCR markdown files')
    parser.add_argument('--output-dir', '-o',
                       help='Output directory for results (optional)')
    parser.add_argument('--list', '-l', 
                       action='store_true',
                       help='List available files')
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    
    # Make input directory absolute
    if not os.path.isabs(input_dir):
        input_dir = os.path.join(os.getcwd(), input_dir)
    
    print(f"Input directory: {input_dir}")
    
    if args.list or not args.file:
        md_files = list_available_files(input_dir)
        if not args.file and md_files:
            print(f"\nTo test a specific file, use:")
            print(f"python {sys.argv[0]} --file filename.md")
        return
    
    # Build full file path
    file_path = os.path.join(input_dir, args.file)
    
    # Test the document
    success = test_single_document(file_path, args.image, args.output_dir)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())