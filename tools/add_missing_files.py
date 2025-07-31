#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

def add_missing_files_to_run(original_dir, postprocessed_dir):
    """
    Add missing unchanged files from original directory to postprocessed directory
    """
    
    print(f"Adding missing files to postprocessed run...")
    print(f"Original directory: {original_dir}")
    print(f"Postprocessed directory: {postprocessed_dir}")
    
    if not os.path.exists(original_dir):
        print(f"Error: Original directory not found: {original_dir}")
        return
    
    if not os.path.exists(postprocessed_dir):
        print(f"Error: Postprocessed directory not found: {postprocessed_dir}")
        return
    
    # Get all files from original directory
    original_files = set(f for f in os.listdir(original_dir) if f.endswith('.md'))
    
    # Get all files from postprocessed directory
    postprocessed_files = set(f for f in os.listdir(postprocessed_dir) if f.endswith('.md'))
    
    # Find missing files
    missing_files = original_files - postprocessed_files
    
    print(f"\nFile counts:")
    print(f"  Original files: {len(original_files)}")
    print(f"  Postprocessed files: {len(postprocessed_files)}")
    print(f"  Missing files: {len(missing_files)}")
    
    if not missing_files:
        print("\nNo missing files - all files are already present!")
        return
    
    # Copy missing files
    copied_count = 0
    for filename in sorted(missing_files):
        src_path = os.path.join(original_dir, filename)
        dst_path = os.path.join(postprocessed_dir, filename)
        
        try:
            shutil.copy2(src_path, dst_path)
            copied_count += 1
            print(f"  Copied: {filename}")
        except Exception as e:
            print(f"  Error copying {filename}: {e}")
    
    print(f"\nCompleted! Copied {copied_count} missing files.")
    print(f"Total files in postprocessed directory: {len(os.listdir(postprocessed_dir))}")

def main():
    """Main function"""
    
    # Default paths - update these to match your specific run
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    original_dir = os.path.join(base_dir, 'demo_data', 'microsoft_ocr_results_markdownonly')
    
    # You'll need to update this to your specific run directory
    postprocessed_dir = os.path.join(base_dir, 'demo_data', 'microsoft_ocr_results_gpt_processed', 'run_2025-07-30_17-22-35')
    
    print("Add Missing Files to Postprocessed Run")
    print("=" * 50)
    print()
    print("This script will copy unchanged files from the original Microsoft OCR")
    print("results to your postprocessed run directory, making it complete for")
    print("benchmark evaluation.")
    print()
    
    # Check if default postprocessed directory exists
    if not os.path.exists(postprocessed_dir):
        print(f"Default postprocessed directory not found: {postprocessed_dir}")
        print()
        print("Available runs:")
        runs_base = os.path.join(base_dir, 'demo_data', 'microsoft_ocr_results_gpt_processed')
        if os.path.exists(runs_base):
            runs = [d for d in os.listdir(runs_base) if d.startswith('run_')]
            for run in sorted(runs):
                print(f"  {run}")
        print()
        print("Please update the postprocessed_dir path in this script or provide as argument.")
        return
    
    add_missing_files_to_run(original_dir, postprocessed_dir)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 3:
        # Command line arguments provided
        original_dir = sys.argv[1]
        postprocessed_dir = sys.argv[2]
        add_missing_files_to_run(original_dir, postprocessed_dir)
    else:
        main()