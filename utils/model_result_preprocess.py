import os
import json

# marker&mineru: copy md to one folder
path = '/mnt/petrelfs/ouyanglinke/CDM_match/result/mineru_v2/demo_output'
for root,folders,files in os.walk(path):
    for file in files:
        if file.endswith('.md'):
            file_path = os.path.join(root, file)
            os.system(f"cp '{file_path}' /mnt/petrelfs/ouyanglinke/CDM_match/result/mineru")

# # marker改名
# root_path = '/mnt/petrelfs/ouyanglinke/CDM_match/result/marker'

# for file_name in os.listdir(root_path):
#     new_filename = '_'.join(file_name.split('_')[:-1]) + '.pdf_' + file_name.split('_')[-1]
#     old_path = os.path.join(root_path, file_name)
#     new_path = os.path.join(root_path, new_filename)
#     os.system(f"mv '{old_path}' '{new_path}'")

# # mathpix, json2md
# def convert_json_to_md(pred_path, output_dir):

#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)

#     with open(pred_path, 'r') as infile:
#         for line in infile:
#             data = json.loads(line.strip())
#             pdf_name = os.path.splitext(os.path.basename(data['image path:']))[0]
#             with open(os.path.join(output_dir, pdf_name+'.md'), 'w', encoding='utf-8') as outfile:
#                     outfile.write(data['API results:']['text'])

# convert_json_to_md("/mnt/petrelfs/ouyanglinke/CDM_match/result/mathpix/demo_val_mathpix_result_v2.jsonl", "/mnt/petrelfs/ouyanglinke/CDM_match/result/mathpix")