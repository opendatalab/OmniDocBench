import mathpix
import json
import os
import pickle
import time
import io
import fitz
import base64
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["http_proxy"] = "xxx"
os.environ["https_proxy"] = "xxx"


# def mathpix_predict(pdf_file):
#     # r = mathpix.text({
#     r = mathpix.pdf({
#         "enable_tables_fallback": True,
#         "conversion_formats": {
#             "docx": False,
#             "tex.zip": False
#         }
#     }, file=pdf_file)
#     return r

# def mathpix_predict(image_path):
#     # r = mathpix.text({
#     r = mathpix.latex({
#         'src': mathpix.image_uri(image_path),
#         'formats': ['text'],
#         'math_inline_delimiters': ["$", "$"],
#         'math_display_delimiters': ["$$", "$$"],
#         'enable_tables_fallback': True,
#     })
#     return r

def mathpix_predict(image_str):
    r = mathpix.text({
    # r = mathpix.latex({
        'src': "data:image/jpg;base64," + image_str,
        'formats': ['text'],
        'math_inline_delimiters': ["$", "$"],
        'math_display_delimiters': ["$$", "$$"],
        'enable_tables_fallback': True,
    })
    return r


def mathpix_pdf_predict(pdf_file):
    # r = mathpix.text({
    r = mathpix.pdf({
        "enable_tables_fallback": True,
        'math_inline_delimiters': ["$", "$"],
        'math_display_delimiters': ["$$", "$$"],
        "rm_spaces": True,
        "conversion_formats": {
            "docx": False,
            "tex.zip": False
        }
    }, file=pdf_file)
    return r

def load_pdf_image(pdf_path, dpi=100):
    images = []
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        image_bytes = pix.tobytes("png")
        image_str = base64.b64encode(image_bytes).decode()

        images.append(image_str)

    return images


def process_pdf_img(pdf_path):
    results = []
    pdf_images = load_pdf_image(pdf_path)
    for page_no, image in enumerate(pdf_images):
        result = mathpix_predict(image)
        results.append({
            "path": pdf_path,
            "page_no": page_no,
            **result
        })
        basename = os.path.basename(pdf_path).replace(".pdf", "")
        json.dump(results, open("./tmp.json".format(basename), "w"), indent=4)

def process_img(image_path, output_dir):
    with open(image_path, "rb") as file:
        image_str = base64.b64encode(file.read()).decode()
    results = mathpix_predict(image_str)
    img_name = os.path.basename(image_path)
    if results.get('text'):
        with open(os.path.join(output_dir, img_name[:-4]+'.md'), 'w', encoding='utf-8') as outfile:
            outfile.write(results['text'])
    else:
        print(results)
        with open(os.path.join(output_dir, 'no_result.txt'), 'a') as f:
            f.write(image_path)
            f.write('\n')


def process_pdf(pdf_path):
    basename = os.path.basename(pdf_path).replace(".pdf", "")
    if os.path.exists(output_dir + "/{}_pdf.json".format(basename)):
        data = json.load(open(output_dir + "/{}_pdf.json".format(basename)))
        if "pdf_id" in data:
            return
    file = open(pdf_path, "rb")
    results = mathpix_pdf_predict(file)
    json.dump(results, open(output_dir + "/{}_pdf.json".format(basename), "w"), indent=4)


if __name__ == '__main__':
    output_dir = 'xxx'

    os.makedirs(output_dir, exist_ok=True)

    from glob import glob

    # paths = list(glob(data_root + "/*.pdf"))
    img_folder = '../../demo_data/omnidocbench_demo/images'
    paths = [os.path.join(img_folder, _) for _ in os.listdir(img_folder) if _.endswith('.jpg')]
    with open('./no_result.txt', 'r') as f:
        paths = [_.strip() for _ in f.readlines()]

    for path in tqdm(paths):
        process_img(path, output_dir)
    # with ThreadPoolExecutor(max_workers=25) as executor:
        # futures = [executor.submit(process_pdf_img, path) for path in paths]
        # for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
        #     future.result()  # Get the result to handle any exceptions