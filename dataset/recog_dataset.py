import re
from registry.registry import DATASET_REGISTRY
import json
import html
import unicodedata
import os
import uuid
import shutil
import subprocess
from bs4 import BeautifulSoup
from utils.ocr_utils import get_text_for_block


@DATASET_REGISTRY.register("recogition_text_dataset")
class RecognitionTextDataset():
    # 按照text block的粒度进行评测，不考虑bbox的一一匹配
    def __init__(self, cfg_task):
        gt_file = cfg_task['dataset']['ground_truth']['data_path']
        pred_folder = cfg_task['dataset']['prediction']['data_path']
        self.samples = self.load_data(gt_file, pred_folder)

    def load_data(self, gt_file, pred_folder):
        samples = []
        with open(gt_file, 'r') as f:
            gts = json.load(f)
        
        for gt in gts:
            img_name = os.path.basename(gt['image_path'])
            gt_text = gt['text']
            pred_file = os.path.join(pred_folder, img_name[:-4]+'.json')
            if not os.path.exists(pred_file):
                print(f'Cannot find pred for {img_name}')
                continue
            else:
                with open(pred_file, 'r') as f:
                    pred_spans = json.load(f)
                pred_text = get_text_for_block(gt, pred_spans)
            samples.append({
                "gt": gt_text,
                'pred': pred_text,
                'img_id': img_name
            })
        return samples

@DATASET_REGISTRY.register("recogition_formula_dataset")
class RecognitionFormulaDataset():
    def __init__(self, cfg_task):
        gt_file = cfg_task['dataset']['ground_truth']['data_path']
        pred_file = cfg_task['dataset']['prediction']['data_path']

        self.samples = self.load_data(gt_file, pred_file)
    
    def load_data(self, gt_file, pred_file):
        """
        Load a list of image paths and their corresponding formulas.
        The function skips empty lines and lines without corresponding images.

        Args:
            image_path (str): The path to the directory containing the image files.
            math_file (str): The path to the text file containing the formulas.

        Returns:
            list, list: A list of image paths and a list of corresponding formula
        """
        
        with open(gt_file, 'r') as f:
            math_gts = [line.strip() for line in f.readlines()]
        
        with open(pred_file, 'r') as f:
            math_preds = [line.strip() for line in f.readlines()]

        
        if len(math_preds) != len(math_gts):
            raise ValueError("The number of prediction does not match the number of ground truth.")

        norm_gts = [self.normalize_text(gt) for gt in math_gts]   # 公式的norm
        norm_preds = [self.normalize_text(pred) for pred in math_preds]

        samples = []
        img_id = 0
        for gt, pred in zip(norm_gts, norm_preds):
            samples.append({
                'gt': gt,
                'pred': pred,
                'img_id': img_id
            })
            img_id += 1
        
        return samples

    def normalize_text(self, text):
        """Remove unnecessary whitespace from LaTeX code."""
        text_reg = r'(\\(operatorname|mathrm|text|mathbf)\s?\*? {.*?})'
        letter = '[a-zA-Z]'
        noletter = '[\W_^\d]'
        names = [x[0].replace(' ', '') for x in re.findall(text_reg, text)]
        text = re.sub(text_reg, lambda match: str(names.pop(0)), text)
        news = text
        while True:
            text = news
            news = re.sub(r'(?!\\ )(%s)\s+?(%s)' % (noletter, noletter), r'\1\2', text)
            news = re.sub(r'(?!\\ )(%s)\s+?(%s)' % (noletter, letter), r'\1\2', news)
            news = re.sub(r'(%s)\s+?(%s)' % (letter, noletter), r'\1\2', news)
            if news == text:
                break
        return text
    
    def __getitem__(self, idx):
        return self.samples[idx]

@DATASET_REGISTRY.register("recogition_table_dataset")
class RecognitionTableDataset():
    def __init__(self, cfg_task):
        gt_file = cfg_task['dataset']['ground_truth']['data_path']
        pred_file = cfg_task['dataset']['prediction']['data_path']
        self.pred_table_format = cfg_task['dataset']['prediction'].get('table_format', 'html')

        references, predictions = self.load_data(gt_file), self.load_data(pred_file)
        self.samples = self.normalize_data(references, predictions)

    def normalize_data(self, references, predictions):
        samples = []
        for img in references.keys():
            r = references[img]['html']
            if predictions.get(img):
                if self.pred_table_format == 'latex':
                    raw_p = predictions[img]['latex']
                    p = self.convert_latex_to_html(raw_p)
                else:
                    p = predictions[img]['html']
            else:
                p = ""
            img_id = references[img]["anno_id"]
            _, p = self.process_table(p)
            _, r = self.process_table(r)
            # print('p:', p)
            # print('r:', r)
            samples.append({
                'gt': self.strcut_clean(self.clean_table(r)),
                'pred': self.strcut_clean(p),
                'img_id': img_id
            })
        return samples

    def __getitem__(self, idx):
        return self.samples[idx]
    
    def load_data(self, data_path):
        result_dict = {}
        with open(data_path, 'r') as f:
            samples = json.load(f)
        for sample in samples:
            result_dict[sample["image_path"]] = sample
        
        return result_dict
    
    def strcut_clean(self, input_str):
        input_str = re.sub('<colgroup>.*?</colgroup>','',input_str)
        return input_str
    
    def clean_table(self, input_str,flag=True):
        if flag:
            input_str = input_str.replace('<sup>', '').replace('</sup>', '')
            input_str = input_str.replace('<sub>', '').replace('</sub>', '')
            input_str = input_str.replace('<span>', '').replace('</span>', '')
            input_str = input_str.replace('<div>', '').replace('</div>', '')
            input_str = input_str.replace('<p>', '').replace('</p>', '')
            input_str = input_str.replace('<spandata-span-identity="">', '')
        return input_str

    # remove residuals and output two formats of the table
    def process_table(self, md_i):
        """
        pred_md format edit
        """
        def convert_th_to_td(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            th_tags = soup.find_all('th')
            for th in th_tags:
                th.name = 'td'
            return str(soup)
        # pred_md = pred_md["result"]["markdown"]
        # pred_md = pred_md.split("\n\n")
        # table_flow = []
        # table_flow_no_space = []
        # for idx, md_i in enumerate(pred_md):
        table_res=''
        table_res_no_space=''
        if '<table' in md_i.replace(" ","").replace("'",'"'):
            md_i = convert_th_to_td(md_i)
            table_res = html.unescape(md_i).replace('\\', '').replace('\n', '')
            table_res = unicodedata.normalize('NFKC', table_res).strip()
            pattern = r'<table\b[^>]*>(.*?)</table>'
            tables = re.findall(pattern, table_res, re.DOTALL | re.IGNORECASE)
            table_res = ''.join(tables)
            table_res = re.sub('<table.*?>','',table_res)
            table_res = re.sub('( style=".*?")', "", table_res)
            table_res = re.sub('( height=".*?")', "", table_res)
            table_res = re.sub('( width=".*?")', "", table_res)
            table_res = re.sub('( align=".*?")', "", table_res)
            table_res = re.sub('( class=".*?")', "", table_res)
            table_res = re.sub('</?tbody>',"",table_res)
            table_res_no_space = '<html><body><table border="1" >' + table_res.replace(' ','') + '</table></body></html>'
            # table_res_no_space = re.sub(' (style=".*?")',"",table_res_no_space)
            table_res_no_space = re.sub(r'[ $]', "", table_res_no_space)
            table_res_no_space = re.sub('colspan="', ' colspan="', table_res_no_space)
            table_res_no_space = re.sub('rowspan="', ' rowspan="', table_res_no_space)
            table_res_no_space = re.sub('border="', ' border="', table_res_no_space)

            table_res = '<html><body>' + table_res + '</body></html>'
            # table_flow.append(table_res)
            # table_flow_no_space.append(table_res_no_space)

        return table_res, table_res_no_space
    
    def convert_latex_to_html(self, latex_content):
        uuid_str = str(uuid.uuid1())
        os.makedirs(uuid_str, exist_ok=True)
        with open(f'{uuid_str}/temp.tex', 'w') as f:
            f.write(self.latex_template(latex_content))

        cmd = ['latexmlc', f'{uuid_str}/temp.tex', f'--dest={uuid_str}/output.html']
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(f'{uuid_str}/output.html', 'r') as f:
                html_content = f.read()

            pattern = r'<table\b[^>]*>(.*?)</table>'
            tables = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            tables = [f'<table>{table}</table>' for table in tables]
            html_content = '\n'.join(tables)
        
        except Exception as e:
            html_content = ''
        
        if os.path.exists(f'{uuid_str}'):
            shutil.rmtree(f'{uuid_str}')
        return html_content

    def latex_template(self, latex_code):  
        template = r'''
        \documentclass[border=20pt]{standalone}
        \usepackage{blindtext}%
        \usepackage{subcaption}
        \usepackage{url}
        \usepackage{graphicx}
        \usepackage{caption}
        \usepackage{multirow}
        \usepackage{booktabs}
        \usepackage{color}
        \usepackage{colortbl}
        \usepackage{xcolor,soul,framed}
        \usepackage{xeCJK}
        \usepackage{fontspec}
        %\usepackage[margin=1in]{geometry} 
        \usepackage{printlen}
        \usepackage{amsmath,amssymb,mathtools,bm,mathrsfs,textcomp}
        \setlength{\parindent}{0pt}''' + \
        r'''
        \begin{document}
        ''' + \
        latex_code + \
        r'''
        \end{document}'''
    
        return template