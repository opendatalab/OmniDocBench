import os
import time
from paddleocr import PaddleOCR, PPStructureV3
from tqdm import tqdm 

def process_folder(folder_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pipeline  = PPStructureV3()

    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    image_files = [f for f in os.listdir(folder_path) 
                  if os.path.splitext(f)[1].lower() in image_extensions]

    processing_stats = []
    
    for img_file in tqdm(image_files, desc="Processing images"):
        img_path = os.path.join(folder_path, img_file)

        start_time = time.time()
        
        try:
            result = pipeline.predict(img_path,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation = False,
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            base_name = os.path.splitext(img_file)[0]
            oupt_file = os.path.join(output_dir, base_name)
            for res in result:
                res.save_to_json(oupt_file)
                res.save_to_markdown(oupt_file, pretty=False)
            
            print(f"Result save to {oupt_file}")

            processing_stats.append({
                "image": img_file,
                "processing_time": processing_time,
                "status": "success"
            })
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            processing_stats.append({
                "image": img_file,
                "processing_time": processing_time,
                "status": f"failed: {str(e)}"
            })
    

    print("\nProcessing Statistics:")
    print("=" * 50)
    for stat in processing_stats:
        print(f"Image: {stat['image']}")
        print(f"Status: {stat['status']}")
        print(f"Processing Time: {stat['processing_time']:.2f} seconds")
        print("-" * 50)
    

    total_time = sum(stat['processing_time'] for stat in processing_stats)
    success_count = sum(1 for stat in processing_stats if stat['status'] == 'success')
    failed_count = len(processing_stats) - success_count
    
    print("\nSummary:")
    print("=" * 50)
    print(f"Total Images Processed: {len(processing_stats)}")
    print(f"Successfully Processed: {success_count}")
    print(f"Failed to Process: {failed_count}")
    print(f"Total Processing Time: {total_time:.2f} seconds")
    print(f"Average Processing Time: {total_time/len(processing_stats):.2f} seconds per image")
    
    return processing_stats

if __name__ == "__main__":
    input_img_folder = "./images"
    output_md_folder = "./outputs"

    stats = process_folder(input_img_folder, output_md_folder)