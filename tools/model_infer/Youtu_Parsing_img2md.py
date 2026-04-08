import os
from youtu_hf_parser import YoutuOCRParserHF

model_path="./hf_model/Youtu-Parsing"
angle_correct_model_path = None

parser = YoutuOCRParserHF(
    model_path=model_path,                    # Path to downloaded model weights
    enable_angle_correct=True,                # Set to False to disable angle correction
    angle_correct_model_path=angle_correct_model_path  # If None, model will auto-download to default path; if custom path, manually download https://github.com/TencentCloudADP/youtu-parsing/releases/download/v1.0.0/model.pth to specified location
)

input_folder = "./image"
output_dir = "./output"

for filename in os.listdir(input_folder):
    if filename.endswith((".jpg", ".png", ".jpeg", ".pdf")): 
        image_path = os.path.join(input_folder, filename)
        
        parser.parse_file(
            input_path=image_path,
            output_dir=output_dir
        )
        print(f"{filename} 处理完成!")