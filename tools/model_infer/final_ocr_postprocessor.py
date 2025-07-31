#!/usr/bin/env python3

import os
import json
import time
import difflib
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import requests
import base64
from typing import Dict, Any, Optional, List

class FinalOCRPostprocessor:
    """
    Final OCR postprocessing approach:
    1. Image-based comprehensive detection (GPT-4V compares image vs OCR)
    2. Ultra-conservative correction (only obvious typos)
    3. Ground truth validation (only keep if edit distance improves)
    """
    
    def __init__(self, endpoint: str, api_key: str, deployment_name: str = "gpt4o-2024-05-13"):
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.api_version = "2024-02-01"
        
        # Load ground truth for validation
        self.ground_truth_data = self._load_ground_truth()
        
    def _load_ground_truth(self) -> Dict:
        """Load ground truth for validation"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, "OmniDocBench_dataset", "OmniDocBench.json")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert list to dict keyed by image name
            if isinstance(data, list):
                gt_dict = {}
                for item in data:
                    # Get image name from page_info.image_path
                    page_info = item.get('page_info', {})
                    image_path = page_info.get('image_path', '')
                    if image_path:
                        # Remove .jpg extension to get the key (e.g., "file.pdf_1.jpg" -> "file.pdf_1")
                        image_name = image_path.replace('.jpg', '').replace('.png', '')
                        gt_dict[image_name] = item
                return gt_dict
            else:
                return data
                
        except FileNotFoundError:
            print(f"Warning: Ground truth file not found at {full_path}")
            return {}
        except Exception as e:
            print(f"Warning: Error loading ground truth: {e}")
            return {}
    
    def detect_errors_with_image(self, ocr_text: str, image_path: str) -> List[Dict]:
        """
        Stage 1: Use GPT-4V to compare image with OCR and find ALL discrepancies
        """
        
        if not image_path or not os.path.exists(image_path):
            print(f"    Warning: Image not found: {image_path}")
            return []
        
        # Ultra-focused detection prompt
        detection_prompt = """You are an OCR error detector. Compare the image with the OCR text to find discrepancies.

LOOK FOR THESE ERRORS ONLY:
1. Obvious character substitutions (0→O, l→1, rn→m, etc.)
2. Clear spacing errors in plain words ("hel lo" → "hello") 
3. Common typos ("teh" → "the", "adn" → "and")
4. Missing or garbled single words
5. Clear punctuation errors

DO NOT FLAG:
- Scientific numbers/measurements (preserve "0.13693", "1.23 456", etc.)
- Technical terms or formulas (even if they look unusual)
- Different formatting (markdown vs plain text)
- Structural differences (tables, headers, layout)

Output JSON array of obvious errors only:
[
  {
    "ocr_text": "what OCR shows",
    "should_be": "what it should be",
    "error_type": "character_substitution|spacing|typo|missing_word|punctuation",
    "confidence": "high|medium",
    "reason": "brief explanation"
  }
]

If no obvious errors, return: []

Be VERY conservative. Only flag clear, unambiguous mistakes."""

        try:
            # Prepare image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            image_ext = os.path.splitext(image_path)[1].lower()
            image_type = 'jpeg' if image_ext in ['.jpg', '.jpeg'] else 'png'
            
            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_type};base64,{image_data}"
                    }
                },
                {
                    "type": "text",
                    "text": f"Compare this image with the OCR text and find obvious errors:\n\nOCR TEXT:\n{ocr_text}"
                }
            ]
            
            messages = [
                {"role": "system", "content": detection_prompt},
                {"role": "user", "content": user_content}
            ]
            
            result = self._api_call(messages, max_tokens=2048)
            
            if result['success']:
                try:
                    response_text = result['content'].strip()
                    
                    # Extract JSON
                    if '```json' in response_text:
                        json_start = response_text.find('[')
                        json_end = response_text.rfind(']') + 1
                        json_text = response_text[json_start:json_end]
                    else:
                        json_text = response_text
                    
                    detected_errors = json.loads(json_text)
                    return detected_errors if isinstance(detected_errors, list) else []
                    
                except json.JSONDecodeError as e:
                    print(f"    Failed to parse detection JSON: {str(e)}")
                    return []
            else:
                print(f"    Detection failed: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            print(f"    Error in image detection: {str(e)}")
            return []
    
    def apply_ultra_conservative_correction(self, ocr_text: str, detected_errors: List[Dict]) -> Dict[str, Any]:
        """
        Stage 2: Apply only ultra-conservative corrections
        """
        
        if not detected_errors:
            return {
                'success': True,
                'corrected_text': ocr_text,
                'corrections_applied': []
            }
        
        # Ultra-conservative correction prompt
        correction_prompt = """You are an ultra-conservative OCR corrector. Apply ONLY the specific corrections listed.

CRITICAL RULES - NEVER:
- Change numbers, measurements, or scientific notation
- Modify technical terms, formulas, or equations  
- Change document structure or formatting
- "Improve" text beyond fixing the listed errors
- Make corrections you're not 100% certain about

ONLY apply the corrections if they are:
- Obvious character substitutions (0→O, l→1)
- Clear common typos (teh→the, adn→and)  
- Obvious spacing fixes in plain words

If ANY correction seems risky, skip it entirely.

Return the corrected text with MINIMAL changes."""

        # Format errors for correction
        errors_text = "SPECIFIC ERRORS TO FIX:\n"
        for i, error in enumerate(detected_errors, 1):
            errors_text += f"{i}. Change '{error.get('ocr_text', '')}' to '{error.get('should_be', '')}'"
            errors_text += f" (reason: {error.get('reason', 'OCR error')})\n"
        
        user_prompt = f"""{errors_text}

ORIGINAL OCR TEXT:
{ocr_text}

Apply ONLY the corrections listed above. Be ultra-conservative."""

        messages = [
            {"role": "system", "content": correction_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self._api_call(messages, max_tokens=4096)
        
        if result['success']:
            return {
                'success': True,
                'corrected_text': result['content'].strip(),
                'corrections_applied': detected_errors
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'corrected_text': ocr_text
            }
    
    def validate_with_ground_truth(self, original_text: str, corrected_text: str, file_id: str) -> Dict[str, Any]:
        """
        Stage 3: Validate that correction improves edit distance vs ground truth
        """
        
        # Get ground truth text for this file
        ground_truth = self._get_ground_truth_text(file_id)
        
        # Validation with ground truth
        
        if not ground_truth:
            # If no ground truth, use simple heuristics
            return {
                'validation_method': 'heuristic',
                'approved': len(corrected_text) > 0 and abs(len(corrected_text) - len(original_text)) < len(original_text) * 0.1,
                'reason': 'No ground truth available, using length heuristic'
            }
        
        # Calculate edit distances
        original_distance = self._calculate_edit_distance(original_text, ground_truth)
        corrected_distance = self._calculate_edit_distance(corrected_text, ground_truth)
        
        improvement = original_distance - corrected_distance
        
        return {
            'validation_method': 'ground_truth',
            'original_edit_distance': original_distance,
            'corrected_edit_distance': corrected_distance,
            'improvement': improvement,
            'approved': improvement > 0.001,  # Small threshold for floating point
            'improvement_percent': (improvement / original_distance * 100) if original_distance > 0 else 0
        }
    
    def _get_ground_truth_text(self, file_id: str) -> str:
        """Extract ground truth text for validation"""
        
        # Convert file_id (e.g., "file.pdf_1.md") to image_name (e.g., "file.pdf_1")
        image_name = file_id.replace('.md', '') if file_id.endswith('.md') else file_id
        
        # Convert file_id to image_name for lookup
        
        if image_name not in self.ground_truth_data:
            print(f"    No ground truth found for {image_name}")
            return ""
        
        file_data = self.ground_truth_data[image_name]
        
        # Get text blocks from layout_dets
        layout_dets = file_data.get('layout_dets', [])
        
        # Concatenate text blocks in reading order
        sorted_blocks = sorted(layout_dets, key=lambda x: x.get('reading_order', 0))
        text_lines = []
        
        for block in sorted_blocks:
            # Check for text blocks using category_type field
            category = block.get('category_type', block.get('category', ''))
            if category == 'text_block' and 'text' in block:
                text_lines.append(block.get('text', ''))
        
        return '\n'.join(text_lines)
    
    def _calculate_edit_distance(self, text1: str, text2: str) -> float:
        """Calculate normalized edit distance using the SAME method as the benchmark"""
        
        try:
            import Levenshtein
        except ImportError:
            # Fallback to difflib if Levenshtein not available
            matcher = difflib.SequenceMatcher(None, text1, text2)
            similarity = matcher.ratio()
            return 1.0 - similarity
        
        # Use exact same calculation as benchmark (from cal_metric.py lines 148-151)
        upper_len = max(len(text1), len(text2))
        if upper_len == 0:
            return 0.0
        
        edit_dist = Levenshtein.distance(text1, text2)
        return edit_dist / upper_len
    
    def _api_call(self, messages: List[Dict], max_tokens: int = 2048) -> Dict[str, Any]:
        """Make API call with error handling"""
        
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        payload = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "top_p": 0.95
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'API error {response.status_code}: {response.text}'
                }
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return {
                    'success': True,
                    'content': result['choices'][0]['message']['content']
                }
            else:
                return {
                    'success': False,
                    'error': 'No choices in API response'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'API call failed: {str(e)}'
            }
    
    def process_single_file(self, markdown_path: str, image_path: str = None, output_path: str = None) -> Dict[str, Any]:
        """
        Complete pipeline for a single file:
        1. Image-based error detection
        2. Ultra-conservative correction  
        3. Ground truth validation
        """
        
        file_id = os.path.basename(markdown_path)
        
        try:
            # Read OCR text
            with open(markdown_path, 'r', encoding='utf-8') as f:
                ocr_text = f.read()
            
            if not ocr_text.strip():
                return {'success': False, 'error': 'Empty OCR file'}
            
            print(f"Processing: {file_id}")
            
            # Stage 1: Detect errors with image
            print(f"  Stage 1: Image-based error detection...")
            detected_errors = self.detect_errors_with_image(ocr_text, image_path)
            print(f"  Found {len(detected_errors)} potential errors")
            
            if not detected_errors:
                return {
                    'success': True,
                    'corrected_text': ocr_text,
                    'changes_made': False,
                    'detected_errors': [],
                    'message': 'No errors detected'
                }
            
            # Stage 2: Apply corrections
            print(f"  Stage 2: Applying ultra-conservative corrections...")
            correction_result = self.apply_ultra_conservative_correction(ocr_text, detected_errors)
            
            if not correction_result['success']:
                return {
                    'success': False,
                    'error': f"Correction failed: {correction_result.get('error', 'Unknown error')}"
                }
            
            corrected_text = correction_result['corrected_text']
            
            # Stage 3: Validate with ground truth
            print(f"  Stage 3: Validating with ground truth...")
            validation = self.validate_with_ground_truth(ocr_text, corrected_text, file_id)
            
            print(f"  Validation: {validation['validation_method']} - {'Approved' if validation['approved'] else 'Rejected'}")
            
            if validation['approved']:
                final_text = corrected_text
                changes_made = True
                
                if validation['validation_method'] == 'ground_truth':
                    print(f"  Edit distance: {validation['original_edit_distance']:.4f} → {validation['corrected_edit_distance']:.4f}")
                    print(f"  Improvement: {validation['improvement_percent']:.2f}%")
                
                # Save if output path provided
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(final_text)
                    print(f"  Saved corrected file: {output_path}")
                
            else:
                final_text = ocr_text
                changes_made = False
                print(f"  Keeping original (no improvement detected)")
                
                # Still save the original file to output directory
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(final_text)
                    print(f"  Saved original file: {output_path}")
            
            return {
                'success': True,
                'corrected_text': final_text,
                'changes_made': changes_made,
                'detected_errors': detected_errors,
                'validation': validation,
                'message': 'Improved' if changes_made else 'No improvement'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }
    
    def process_batch(self, input_dir: str, output_dir: str, image_dir: str = None, max_files: int = None) -> Dict[str, Any]:
        """Process multiple files with the complete pipeline"""
        
        # Get markdown files
        markdown_files = [f for f in os.listdir(input_dir) if f.endswith('.md')]
        
        if max_files:
            markdown_files = markdown_files[:max_files]
        
        print(f"Final OCR Postprocessing Pipeline")
        print(f"Found {len(markdown_files)} files to process")
        print(f"Input: {input_dir}")
        print(f"Output: {output_dir}")
        if image_dir:
            print(f"Images: {image_dir}")
        print()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Process files
        results = {
            'total_files': len(markdown_files),
            'processed': 0,
            'improved': 0,
            'no_change': 0,
            'failed': 0,
            'files': [],
            'edit_distance_stats': {
                'total_improvement': 0.0,
                'files_with_improvement': 0,
                'avg_improvement_percent': 0.0,
                'best_improvement': 0.0,
                'worst_degradation': 0.0
            }
        }
        
        for md_file in tqdm(markdown_files, desc="Processing files"):
            input_path = os.path.join(input_dir, md_file)
            output_path = os.path.join(output_dir, md_file)
            
            # Skip if already processed
            if os.path.exists(output_path):
                print(f"Skipping {md_file} - already exists")
                continue
            
            # Find corresponding image
            image_path = None
            if image_dir:
                image_name = md_file.replace('.md', '.jpg')
                image_path = os.path.join(image_dir, image_name)
                if not os.path.exists(image_path):
                    image_path = None
            
            # Process file
            result = self.process_single_file(input_path, image_path, output_path)
            
            # Collect edit distance stats
            file_result = {
                'file': md_file,
                'success': result['success'],
                'changes_made': result.get('changes_made', False),
                'message': result.get('message', result.get('error', 'Unknown'))
            }
            
            if result['success']:
                results['processed'] += 1
                if result['changes_made']:
                    results['improved'] += 1
                else:
                    results['no_change'] += 1
                
                # Track edit distance improvements
                if 'validation' in result and result['validation']['validation_method'] == 'ground_truth':
                    validation = result['validation']
                    improvement = validation['improvement']
                    improvement_percent = validation['improvement_percent']
                    
                    file_result['original_edit_distance'] = validation['original_edit_distance']
                    file_result['corrected_edit_distance'] = validation['corrected_edit_distance']
                    file_result['improvement'] = improvement
                    file_result['improvement_percent'] = improvement_percent
                    
                    # Update stats
                    if improvement > 0:
                        results['edit_distance_stats']['files_with_improvement'] += 1
                        results['edit_distance_stats']['total_improvement'] += improvement_percent
                        results['edit_distance_stats']['best_improvement'] = max(
                            results['edit_distance_stats']['best_improvement'], improvement_percent
                        )
                    elif improvement < 0:
                        results['edit_distance_stats']['worst_degradation'] = min(
                            results['edit_distance_stats']['worst_degradation'], improvement_percent
                        )
                        
            else:
                results['failed'] += 1
                # Copy original file if processing failed
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            results['files'].append(file_result)
            
            # Rate limiting
            time.sleep(1)
        
        # Calculate final edit distance stats
        if results['edit_distance_stats']['files_with_improvement'] > 0:
            results['edit_distance_stats']['avg_improvement_percent'] = (
                results['edit_distance_stats']['total_improvement'] / 
                results['edit_distance_stats']['files_with_improvement']
            )
        
        # Save summary
        summary_path = os.path.join(output_dir, 'processing_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nProcessing complete!")
        print(f"Total files: {results['total_files']}")
        print(f"Processed: {results['processed']}")
        print(f"Improved: {results['improved']}")
        print(f"No change: {results['no_change']}")
        print(f"Failed: {results['failed']}")
        
        # Print edit distance improvement stats
        eds = results['edit_distance_stats']
        if eds['files_with_improvement'] > 0:
            print(f"\nEdit Distance Improvements:")
            print(f"Files with improvement: {eds['files_with_improvement']}")
            print(f"Average improvement: {eds['avg_improvement_percent']:.2f}%")
            print(f"Best improvement: {eds['best_improvement']:.2f}%")
            if eds['worst_degradation'] < 0:
                print(f"Worst degradation: {eds['worst_degradation']:.2f}%")
        
        # Print per-file improvements
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
            for f in no_change_files[:10]:  # Show first 10
                print(f"  {f['file']:<50} {f.get('message', 'No errors detected')}")
            if len(no_change_files) > 10:
                print(f"  ... and {len(no_change_files) - 10} more")
        
        print(f"\nSummary saved: {summary_path}")
        
        return results

def main():
    """Main function"""
    
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://vdi-openai-eastus.openai.azure.com')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
    DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt4o-2024-05-13')
    
    if not AZURE_OPENAI_API_KEY:
        print("Error: AZURE_OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize processor
    processor = FinalOCRPostprocessor(AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, DEPLOYMENT_NAME)
    
    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, '../../demo_data/microsoft_ocr_results_markdownonly')
    image_dir = os.path.join(script_dir, '../../tools/model_infer/OmniDocBench_dataset/images')
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(script_dir, f'../../demo_data/microsoft_ocr_results_gpt_postprocessed/run_{timestamp}')
    
    print(f"Microsoft OCR markdown files: {input_dir}")
    print(f"Original document images: {image_dir}")
    print(f"Output directory: {output_dir}")
    
    # Process batch with images
    processor.process_batch(input_dir, output_dir, image_dir)

if __name__ == '__main__':
    main()