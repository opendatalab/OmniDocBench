#!/usr/bin/env python3
"""
OCR Postprocessing Pipeline
Processes OCR markdown results using Azure OpenAI GPT to fix common errors
"""

import os
import sys
import argparse
from pathlib import Path

# Add the tools directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'model_infer'))

from azure_openai_postprocess import main as azure_postprocess_main

def setup_environment():
    """Load environment variables from .env file if it exists"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file):
        print(f"Loading environment from: {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print(f"No .env file found at: {env_file}")
        print("Please create a .env file based on .env.example")

def main():
    parser = argparse.ArgumentParser(description='Postprocess OCR results using Azure OpenAI GPT')
    parser.add_argument('--input-dir', 
                       default='demo_data/microsoft_ocr_results_markdownonly',
                       help='Input directory containing OCR markdown files')
    parser.add_argument('--output-dir', 
                       default='demo_data/microsoft_ocr_results_gpt_corrected',
                       help='Output directory for corrected markdown files')
    parser.add_argument('--endpoint', 
                       help='Azure OpenAI endpoint URL (overrides .env)')
    parser.add_argument('--api-key', 
                       help='Azure OpenAI API key (overrides .env)')
    parser.add_argument('--deployment', 
                       default='gpt-4o',
                       help='Azure OpenAI deployment name')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show configuration without processing files')
    
    args = parser.parse_args()
    
    # Load environment variables
    setup_environment()
    
    # Override environment variables with command line arguments
    if args.endpoint:
        os.environ['AZURE_OPENAI_ENDPOINT'] = args.endpoint
    if args.api_key:
        os.environ['AZURE_OPENAI_API_KEY'] = args.api_key
    if args.deployment:
        os.environ['AZURE_OPENAI_DEPLOYMENT'] = args.deployment
    
    # Show configuration
    print("=== OCR Postprocessing Configuration ===")
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Azure OpenAI endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'NOT SET')}")
    print(f"API key: {'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET'}")
    print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT', 'NOT SET')}")
    print("=" * 40)
    
    if args.dry_run:
        print("Dry run mode - no files will be processed")
        return
    
    # Validate configuration
    if not os.getenv('AZURE_OPENAI_API_KEY'):
        print("\n❌ Error: Azure OpenAI API key not configured")
        print("Please either:")
        print("1. Set AZURE_OPENAI_API_KEY in your .env file")
        print("2. Use --api-key argument")
        return 1
    
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        print("\n❌ Error: Azure OpenAI endpoint not configured")
        print("Please either:")
        print("1. Set AZURE_OPENAI_ENDPOINT in your .env file")
        print("2. Use --endpoint argument")
        return 1
    
    # Update the paths in the azure_openai_postprocess module
    import azure_openai_postprocess
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Override the input/output directories
    azure_openai_postprocess.input_dir = os.path.join(script_dir, '..', args.input_dir)
    azure_openai_postprocess.output_dir = os.path.join(script_dir, '..', args.output_dir)
    
    # Run the postprocessing
    try:
        azure_postprocess_main()
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())