<h1 align="center">
OmniDocBench
</h1>

<div align="center">
English | <a href="./README_zh-CN.md">简体中文</a>

[\[📜 arXiv\]](https://arxiv.org/abs/2412.07626) | [[Dataset (🤗Hugging Face)]](https://huggingface.co/datasets/opendatalab/OmniDocBench) | [[Dataset (OpenDataLab)]](https://opendatalab.com/OpenDataLab/OmniDocBench)

</div>

**OmniDocBench** is a benchmark for evaluating diverse document parsing in real-world scenarios, featuring the following characteristics:
- **Diverse Document Types**: This benchmark includes 1355 PDF pages, covering 9 document types, 4 layout types, and 3 language types. It encompasses a wide range of content, including academic papers, financial reports, newspapers, textbooks, and handwritten notes.
- **Rich Annotation Information**: It contains **localization information** for 15 block-level (such as text paragraphs, headings, tables, etc., totaling over 20k) and 4 span-level (such as text lines, inline formulas, subscripts, etc., totaling over 80k) document elements. Each element's region includes **recognition results** (text annotations, LaTeX annotations for formulas, and both LaTeX and HTML annotations for tables). OmniDocBench also provides annotations for the **reading order** of document components. Additionally, it includes various attribute tags at the page and block levels, with annotations for 5 **page attribute tags**, 3 **text attribute tags**, and 6 **table attribute tags**.
- **High Annotation Quality**: The data quality is high, achieved through manual screening, intelligent annotation, manual annotation, and comprehensive expert and large model quality checks.
- **Supporting Evaluation Code**: It includes end-to-end and single-module evaluation code to ensure fairness and accuracy in assessments.

**OmniDocBench** is designed for Document Parsing, featuring rich annotations for evaluation across several dimensions:
<!-- : includes both end2end and md2md evaluation methods -->
- End-to-end evaluation
- Layout detection
- Table recognition
- Formula recognition
- Text OCR

Currently supported metrics include:
- Normalized Edit Distance
- BLEU
- METEOR
- TEDS
- COCODet (mAP, mAR, etc.)

## Table of Contents
- [Updates](#updates)
- [Benchmark Introduction](#benchmark-introduction)
  - [Dataset File Format](#dataset-file-format)
  - [Evaluation Categories](#evaluation-categories)
  - [Attribute Labels](#attribute-labels)
- [Evaluation](#evaluation)
  - [Environment Setup and Running](#environment-setup-and-running)
  - [End-to-End Evaluation](#end-to-end-evaluation)
    - [End-to-End Evaluation Method - end2end](#end-to-end-evaluation-method---end2end)
    - [End-to-end Evaluation Method - md2md](#end-to-end-evaluation-method---md2md)
  - [Formula Recognition Evaluation](#formula-recognition-evaluation)
  - [Text OCR Evaluation](#text-ocr-evaluation)
  - [Table Recognition Evaluation](#table-recognition-evaluation)
  - [Layout Detection](#layout-detection)
  - [Formula Detection](#formula-detection)
- [Tools](#tools)
- [The evaluation model information](#the-evaluation-model-information)
  - [end2end](#end2end)
  - [Layout](#layout)
  - [Formula](#formula)
  - [Table](#table)
- [TODO](#todo)
- [Known Issues](#known-issues)
- [Acknowledgement](#acknowledgement)
- [Copyright Statement](#copyright-statement)
- [Citation](#citation)

## Updates

[2025/09/25] **Major update**: Updated from **v1.0** to **v1.5**
  - Evaluation code: (1) Updated the **hybrid matching algorithm**, allowing formulas and text to be matched with each other, which alleviates score errors caused by models outputting formulas as unicode; (2) Integrated **CDM** calculation directly into the metric section, so users with a CDM environment can compute the metric directly by calling `CDM` in config file. The previous interface for outputting formula matching pairs as a JSON file is still retained, now named `CDM_plain` in config file.
  - Benchmark dataset: (1) Increased the image resolution for newspaper and note types from 72 DPI to **200 DPI**; (2) Added **374 new pages**, balanced the number of Chinese and English pages, and increased the proportion of pages containing formulas; (3) Formulas update language atrributes; (4) Fixed typos in some text and table annotations.
  - Leaderboard: (1) Removed the Chinese/English grouping, now calculating the average score across all pages; (2) The **Overall** metric is now calculated as ((1 - text Edit distance) * 100 + table TEDS + formula CDM) / 3;
  - Note: The `main` branch of evaludation code (this repo) and dataset in HuggingFace and OpenDataLab are now updated to Version **v1.5**, if you still want to evaluate your model in v1.0, please checkout to branch `v1_0`.
  
[2025/09/09] Updated Dolphin model evaluation with the latest inference script and model weights; Add Dolphin infer script;

[2025/08/20] Updated PP-StructureV3, MonkeyOCR-pro-1.2B model evaluation; Added Mistral OCR, Pix2text, phocr, Nanonets-OCR-s infer scripts;

[2025/07/31] Added MinerU2.0-vlm, Marker-1.7.1, PP-StructureV3, MonkeyOCR-pro-1.2B, Dolphin, Nanonets-OCR-s, OCRFlux-3B, Qwen2.5-VL-7B and InternVL3-78B model evaluation; Updated versions of MinerU.

[2025/03/27] Added Pix2Text, Unstructured, OpenParse, Gemini-2.0 Flash, Gemini-2.5 Pro, Mistral OCR, olmOCR, Qwen2.5-VL-72B model evaluation;

[2025/03/10] OmniDocBench has been accepted by CVPR 2025!

[2025/01/16] Updated versions of Marker, Tesseract OCR, and StructEqTable; Added Docling, OpenOCR, and EasyOCR evaluations; Changed the Edit Distance calculation for the Table section to use normalized GTs and Preds; Added evaluation model version information.

## Benchmark Introduction

This benchmark includes 1355 PDF pages, covering 9 document types, 4 layout types, and 3 language types. OmniDocBench features rich annotations, containing 15 block-level annotations (text paragraphs, headings, tables, etc.) and 4 span-level annotations (text lines, inline formulas, subscripts, etc.). All text-related annotation boxes include text recognition annotations, formulas contain LaTeX annotations, and tables include both LaTeX and HTML annotations. OmniDocBench also provides reading order annotations for document components. Additionally, it includes various attribute tags at the page and block levels, with annotations for 5 page attribute tags, 3 text attribute tags, and 6 table attribute tags.

![](https://github.com/user-attachments/assets/f3e53ba8-bb97-4ca9-b2e7-e2530865aaa9)

<details>
  <summary>【Dataset Format】</summary>

The dataset format is JSON, with the following structure and field explanations:

```json
[{
    "layout_dets": [    // List of page elements
        {
            "category_type": "text_block",  // Category name
            "poly": [
                136.0, // Position information, coordinates for top-left, top-right, bottom-right, bottom-left corners (x,y)
                781.0,
                340.0,
                781.0,
                340.0,
                806.0,
                136.0,
                806.0
            ],
            "ignore": false,        // Whether to ignore during evaluation
            "order": 0,             // Reading order
            "anno_id": 0,           // Special annotation ID, unique for each layout box
            "text": "xxx",          // Optional field, Text OCR results are written here
            "latex": "$xxx$",       // Optional field, LaTeX for formulas and tables is written here
            "html": "xxx",          // Optional field, HTML for tables is written here
            "attribute" {"xxx": "xxx"},         // Classification attributes for layout, detailed below
            "line_with_spans:": [   // Span level annotation boxes
                {
                    "category_type": "text_span",
                    "poly": [...],
                    "ignore": false,
                    "text": "xxx",   
                    "latex": "$xxx$",
                 },
                 ...
            ],
            "merge_list": [    // Only present in annotation boxes with merge relationships, merge logic depends on whether single line break separated paragraphs exist, like list types
                {
                    "category_type": "text_block", 
                    "poly": [...],
                    ...   // Same fields as block level annotations
                    "line_with_spans": [...]
                    ...
                 },
                 ...
            ]
        ...
    ],
    "page_info": {         
        "page_no": 0,            // Page number
        "height": 1684,          // Page height
        "width": 1200,           // Page width
        "image_path": "xx/xx/",  // Annotated page filename
        "page_attribute": {"xxx": "xxx"}     // Page attribute labels
    },
    "extra": {
        "relation": [ // Related annotations
            {  
                "source_anno_id": 1,
                "target_anno_id": 2, 
                "relation": "parent_son"  // Relationship label between figure/table and their corresponding caption/footnote categories
            },
            {  
                "source_anno_id": 5,
                "target_anno_id": 6,
                "relation_type": "truncated"  // Paragraph truncation relationship label due to layout reasons, will be concatenated and evaluated as one paragraph during evaluation
            },
        ]
    }
},
...
]
```

</details>

<details>
  <summary>【Evaluation Categories】</summary>

Evaluation categories include:

```
# Block level annotation boxes
'title'               # Title
'text_block'          # Paragraph level plain text
'figure',             # Figure type
'figure_caption',     # Figure description/title
'figure_footnote',    # Figure notes
'table',              # Table body
'table_caption',      # Table description/title
'table_footnote',     # Table notes
'equation_isolated',  # Display formula
'equation_caption',   # Formula number
'header'              # Header
'footer'              # Footer
'page_number'         # Page number
'page_footnote'       # Page notes
'abandon',            # Other discarded content (e.g. irrelevant information in middle of page)
'code_txt',           # Code block
'code_txt_caption',   # Code block description
'reference',          # References

# Span level annotation boxes
'text_span'           # Span level plain text
'equation_ignore',    # Formula to be ignored
'equation_inline',    # Inline formula
'footnote_mark',      # Document superscripts/subscripts
```

</details>

<details>
  <summary>【Attribute Labels】</summary>

Page classification attributes include:

```
'data_source': #PDF type classification
    academic_literature  # Academic literature
    PPT2PDF # PPT to PDF
    book # Black and white books and textbooks
    colorful_textbook # Colorful textbooks with images
    exam_paper # Exam papers
    note # Handwritten notes
    magazine # Magazines
    research_report # Research reports and financial reports
    newspaper # Newspapers

'language': #Language type
    en # English
    simplified_chinese # Simplified Chinese
    en_ch_mixed # English-Chinese mixed

'layout': #Page layout type
    single_column # Single column
    double_column # Double column
    three_column # Three column
    1andmore_column # One mixed with multiple columns, common in literature
    other_layout # Other layouts

'watermark': # Whether contains watermark
    true  
    false

'fuzzy_scan': # Whether blurry scanned
    true  
    false

'colorful_backgroud': # Whether contains colorful background, content to be recognized has more than two background colors
    true  
    false
```

Block level attribute - Table related attributes:

```
'table_layout': # Table orientation
    vertical # Vertical table
    horizontal # Horizontal table

'with_span': # Merged cells
    False
    True

'line': # Table borders
    full_line # Full borders
    less_line # Partial borders
    fewer_line # Three-line borders
    wireless_line # No borders

'language': # Table language
    table_en # English table
    table_simplified_chinese # Simplified Chinese table
    table_en_ch_mixed # English-Chinese mixed table

'include_equation': # Whether table contains formulas
    False
    True

'include_backgroud': # Whether table contains background color
    False
    True

'table_vertical' # Whether table is rotated 90 or 270 degrees
    False
    True
```

Block level attribute - Text paragraph related attributes:

```
'text_language': # Text language
    text_en  # English
    text_simplified_chinese # Simplified Chinese
    text_en_ch_mixed  # English-Chinese mixed

'text_background':  # Text background color
    white # Default value, white background
    single_colored # Single background color other than white
    multi_colored  # Multiple background colors

'text_rotate': # Text rotation classification within paragraphs
    normal # Default value, horizontal text, no rotation
    rotate90  # Rotation angle, 90 degrees clockwise
    rotate180 # 180 degrees clockwise
    rotate270 # 270 degrees clockwise
    horizontal # Text is normal but layout is vertical
```

Block level attribute - Formula related attributes:

```
'formula_type': # Formula type
    print  # Print
    handwriting # Handwriting

'equation_language' # Formula language
    equation_en  # English
    equation_ch # Chinese
```

</details>


## Evaluation

OmniDocBench has developed an evaluation methodology based on document component segmentation and matching. It provides corresponding metric calculations for four major modules: text, tables, formulas, and reading order. In addition to overall accuracy results, the evaluation also provides fine-grained evaluation results by page and attributes, precisely identifying pain points in model document parsing.

![](https://github.com/user-attachments/assets/95c88aaa-75dc-432e-891e-17a7d73e024a)

### Environment Setup and Running

To set up the environment, simply run the following commands in the project directory:

```bash
conda create -n omnidocbench python=3.10
conda activate omnidocbench
pip install -r requirements.txt
```

If your model parsing table in LaTeX format, you need to install the [LaTeXML](https://math.nist.gov/~BMiller/LaTeXML/) package. It will automatically convert LaTeX tables to HTML during evaluation process. We have not included the installation of this package in the *requirements.txt*. If needed, please install it separately.

Please download the OmniDocBench dataset from [Hugging Face](https://huggingface.co/datasets/opendatalab/OmniDocBench) or [OpenDataLab](https://opendatalab.com/OpenDataLab/OmniDocBench). The folder structure should be as follows:

```
OmniDocBench/
├── images/     // Image files
│   ├── xxx.jpg
│   ├── ...
├── pdfs/       // Same page as images but in PDF format
│   ├── xxx.pdf
│   ├── ...
├── OmniDocBench.json // OmniDocBench ground truth
```

Run the model inference with images or pdfs is all allowed. The model inference results should be in `markdown format` and stored in the directory with the ***file name same as the image filename*** but with the `.md` extension.

All evaluation inputs are configured through config files. We provide templates for each task under the [configs](./configs) directory, and we will explain the contents of the config files in detail in the following sections. 

Simply, for end2end evaluation, you should provide the path to `OmniDocBench.json` in `data_path` of `ground_truth` and the path to the directory containing the model inference results in `data_path` of `prediction` in [end2end.yaml](./configs/end2end.yaml) as follows:

```yaml
 # ----- Here are the lines to be modifed -----
 dataset:
    dataset_name: end2end_dataset
    ground_truth:
      data_path: ./OmniDocBench.json
    prediction:
      data_path: path/to/your/model/result/dir
```

After configuring the config file, simply pass it as a parameter and run the following code to perform the evaluation:

```bash
python pdf_validation.py --config <config_path>
```

After running the evaluation, the results will be stored in the [result](./result) directory. You can use the [tools/generate_result_tables.ipynb](./tools/generate_result_tables.ipynb) to generate the result leaderboard.

<details>
  <summary>【The information of result folder】</summary>

The result folder contains the following information:

```
result/
├── <model_name>_<match_method>_metric_result.json
├── <model_name>_<match_method>_<element>_per_page_edit.json
├── <model_name>_<match_method>_<element>_result.json
```

The `<model_name>` is the name of the model (it is the same as the folder name of prediction results in the config file). `<match_method>` is the method used for matching, for example, `quick_match` or `simple_match`. `<element>` is the element type, including `text`, `dispaly_formula`, `table`, and `reading_order`.

The `<model_name>_<match_method>_metric_result.json` file contains the evaluation metrics, including edit distance, TEDS, etc.

The `<model_name>_<match_method>_<element>_per_page_edit.json` file contains the edit distance of each page for each element.

The `<model_name>_<match_method>_<element>_result.json` file contains the matched pairs of ground truth and predictions for each element.

</details>

### End-to-End Evaluation

End-to-end evaluation assesses the model's accuracy in parsing PDF page content. The evaluation uses the model's Markdown output of the entire PDF page parsing results as the prediction. The Overall metric is calculated as:

$$\text{Overall} = \frac{(1-\textit{Text Edit Distance}) \times 100 + \textit{Table TEDS} +\textit{Formula CDM}}{3}$$

<table style="width:100%; border-collapse: collapse;">
    <caption>Comprehensive evaluation of document parsing on OmniDocBench (v1.5)</caption>
    <thead>
        <tr>
            <th>Model Type</th>
            <th>Methods</th>
            <th>Size</th>
            <th>Overall&#x2191;</th>
            <th>Text<sup>Edit</sup>&#x2193;</th>
            <th>Formula<sup>CDM</sup>&#x2191;</th>
            <th>Table<sup>TEDS</sup>&#x2191;</th>
            <th>Table<sup>TEDS-S</sup>&#x2191;</th>
            <th>Read Order<sup>Edit</sup>&#x2193;</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="11"><strong>Specialized</strong><br><strong>VLMs</strong></td>
            <td>MinerU2.5</td>
            <td>1.2B</td>
            <td><strong>90.67</strong></td>
            <td><strong>0.047</strong></td>
            <td><strong>88.46</strong></td>
            <td><strong>88.22</strong></td>
            <td><strong>92.38</strong></td>
            <td><strong>0.044</strong></td>
        </tr>
        <tr>
            <td>dots.ocr</td>
            <td>3B</td>
            <td><ins>88.41</ins></td>
            <td><ins>0.048</ins></td>
            <td>83.22</td>
            <td><ins>86.78</ins></td>
            <td><ins>90.62</ins></td>
            <td><ins>0.053</ins></td>
        </tr>
        <tr>
            <td>MonkeyOCR-pro-3B</td>
            <td>3B</td>
            <td>87.13</td>
            <td>0.075</td>
            <td>87.45</td>
            <td>81.39</td>
            <td>85.92</td>
            <td>0.129</td>
        </tr>
        <tr>
            <td>MonkeyOCR-pro-1.2B</td>
            <td>1.2B</td>
            <td>86.96</td>
            <td>0.084</td>
            <td>85.02</td>
            <td>84.24</td>
            <td>89.02</td>
            <td>0.130</td>
        </tr>
        <tr>
            <td>Nanonets-OCR-s</td>
            <td>3B</td>
            <td>85.59</td>
            <td>0.093</td>
            <td>85.90</td>
            <td>80.14</td>
            <td>85.57</td>
            <td>0.108</td>
        </tr>
        <tr>
            <td>MinerU2-VLM</td>
            <td>0.9B</td>
            <td>85.56</td>
            <td>0.078</td>
            <td>80.95</td>
            <td>83.54</td>
            <td>87.66</td>
            <td>0.086</td>
        </tr>
        <tr>
            <td>olmOCR</td>
            <td>7B</td>
            <td>81.79</td>
            <td>0.096</td>
            <td>86.04</td>
            <td>68.92</td>
            <td>74.77</td>
            <td>0.121</td>
        </tr>
        <tr>
            <td>POINTS-Reader</td>
            <td>3B</td>
            <td>80.98</td>
            <td>0.134</td>
            <td>79.20</td>
            <td>77.13</td>
            <td>81.66</td>
            <td>0.145</td>
        </tr>
        <tr>
            <td>Mistral OCR</td>
            <td>-</td>
            <td>78.83</td>
            <td>0.164</td>
            <td>82.84</td>
            <td>70.03</td>
            <td>78.04</td>
            <td>0.144</td>
        </tr>
        <tr>
            <td>OCRFlux</td>
            <td>3B</td>
            <td>74.82</td>
            <td>0.193</td>
            <td>68.03</td>
            <td>75.75</td>
            <td>80.23</td>
            <td>0.202</td>
        </tr>
        <tr>
            <td>Dolphin</td>
            <td>322M</td>
            <td>74.67</td>
            <td>0.125</td>
            <td>67.85</td>
            <td>68.70</td>
            <td>77.77</td>
            <td>0.124</td>
        </tr>
        <tr>
            <td rowspan="5"><strong>General</strong><br><strong>VLMs</strong></td>
            <td>Gemini-2.5 Pro</td>
            <td>-</td>
            <td>88.03</td>
            <td>0.075</td>
            <td>85.82</td>
            <td>85.71</td>
            <td>90.29</td>
            <td>0.097</td>
        </tr>
        <tr>
            <td>Qwen2.5-VL</td>
            <td>72B</td>
            <td>87.02</td>
            <td>0.094</td>
            <td><ins>88.27</ins></td>
            <td>82.15</td>
            <td>86.22</td>
            <td>0.102</td>
        </tr>
        <tr>
            <td>InternVL3.5</td>
            <td>241B</td>
            <td>82.67</td>
            <td>0.142</td>
            <td>87.23</td>
            <td>75.00</td>
            <td>81.28</td>
            <td>0.125</td>
        </tr>
        <tr>
            <td>InternVL3</td>
            <td>78B</td>
            <td>80.33</td>
            <td>0.131</td>
            <td>83.42</td>
            <td>70.64</td>
            <td>77.74</td>
            <td>0.113</td>
        </tr>
        <tr>
            <td>GPT-4o</td>
            <td>-</td>
            <td>75.02</td>
            <td>0.217</td>
            <td>79.70</td>
            <td>67.07</td>
            <td>76.09</td>
            <td>0.148</td>
        </tr>
        <tr>
            <td rowspan="4"><strong>Pipeline</strong><br><strong>Tools</strong></td>
            <td>PP-StructureV3</td>
            <td>-</td>
            <td>86.73</td>
            <td>0.073</td>
            <td>85.79</td>
            <td>81.68</td>
            <td>89.48</td>
            <td>0.073</td>
        </tr>
        <tr>
            <td>Mineru2-pipeline</td>
            <td>-</td>
            <td>75.51</td>
            <td>0.209</td>
            <td>76.55</td>
            <td>70.90</td>
            <td>79.11</td>
            <td>0.225</td>
        </tr>
        <tr>
            <td>Marker-1.8.2</td>
            <td>-</td>
            <td>71.30</td>
            <td>0.206</td>
            <td>76.66</td>
            <td>57.88</td>
            <td>71.17</td>
            <td>0.250</td>
        </tr>
    </tbody>
</table>

More detailed attribute-level evaluation results are shown in the paper. Or you can use the [tools/generate_result_tables.ipynb](./tools/generate_result_tables.ipynb) to generate the result leaderboard.

#### End-to-End Evaluation Method - end2end

End-to-end evaluation consists of two approaches:
- `end2end`: This method uses OmniDocBench's JSON files as Ground Truth. For config file reference, see: [end2end](./configs/end2end.yaml)
- `md2md`: This method uses OmniDocBench's markdown format as Ground Truth. Details will be discussed in the next section *markdown-to-markdown evaluation*.

We recommend using the `end2end` evaluation approach since it preserves the category and attribute information of samples, enabling special category ignore operations and attribute-level result output.

The `end2end` evaluation can assess four dimensions. We provide an example of end2end evaluation results in [result](./result), including:
- Text paragraphs
- Display formulas
- Tables
- Reading order

<details>
  <summary>【Field explanations for end2end.yaml】</summary>

The configuration of `end2end.yaml` is as follows:

```YAML
end2end_eval:          # Specify task name, common for end-to-end evaluation
  metrics:             # Configure metrics to use
    text_block:        # Configuration for text paragraphs
      metric:
        - Edit_dist    # Normalized Edit Distance
        - BLEU         
        - METEOR
    display_formula:   # Configuration for display formulas
      metric:
        - Edit_dist
        - CDM          # Only supports exporting format required for CDM evaluation, stored in results
    table:             # Configuration for tables
      metric:
        - TEDS
        - Edit_dist
    reading_order:     # Configuration for reading order
      metric:
        - Edit_dist
  dataset:                                       # Dataset configuration
    dataset_name: end2end_dataset                # Dataset name, no need to modify
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json  # Path to OmniDocBench
    prediction:
      data_path: ./demo_data/end2end            # Folder path for model's PDF page parsing markdown results
    match_method: quick_match                    # Matching method, options: no_split/no_split/quick_match
    filter:                                      # Page-level filtering
      language: english                          # Page attributes and corresponding tags to evaluate
```

The `data_path` under `prediction` is the folder path containing the model's PDF page parsing results. The folder contains markdown files for each page, with filenames matching the image names but replacing the `.jpg` extension with `.md`.

[CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm) now supports direct evaluation, which requires you to set up the CDM environment according to the [README](./metrics/cdm/README.md) and then call `CDM` directly in the config file. In addition, we still support exporting the JSON format required for CDM evaluation as before: simply add the `CDM_plain` field in the metric configuration, and the output will be organized into the CDM input format and stored in the [result](./result) directory.

For end-to-end evaluation, the config allows selecting different matching methods. There are three matching approaches:
- `no_split`: Does not split or match text blocks, but rather combines them into a single markdown for calculation. This method will not output attribute-level results or reading order results.
- `simple_match`: Performs only paragraph segmentation using double line breaks, then directly matches one-to-one with GT without any truncation or merging.
- `quick_match`: Builds on paragraph segmentation by adding truncation and merging operations to reduce the impact of paragraph segmentation differences on final results, using *Adjacency Search Match* for truncation and merging. In version 1.5, the evaluation method has been fully upgraded to a *Hybrid Matching* approach, allowing formulas and text to be matched with each other, which reduces the score impact caused by models outputting formulas in unicode format.

We recommend using `quick_match` for better matching results. However, if the model's paragraph segmentation is accurate, `simple_match` can be used for faster evaluation. The matching method is configured through the `match_method` field under `dataset` in the config.

The `filter` field allows filtering the dataset. For example, setting `filter` to `language: english` under `dataset` will evaluate only pages in English. See the *Dataset Introduction* section for more page attributes. Comment out the `filter` fields to evaluate the full dataset.

</details>


#### End-to-end Evaluation Method - md2md

The markdown-to-markdown evaluation uses the model's markdown output of the entire PDF page parsing as the Prediction, and OmniDocBench's markdown format as the Ground Truth. Please refer to the config file: [md2md](./configs/md2md.yaml). We recommend using the `end2end` approach from the previous section to evaluate with OmniDocBench, as it preserves rich attribute annotations and ignore logic. However, we still provide the `md2md` evaluation method to align with existing evaluation approaches.

The `md2md` evaluation can assess four dimensions:
- Text paragraphs
- Display formulas  
- Tables
- Reading order

<details>
  <summary>【Field explanations for md2md.yaml】</summary>

The configuration of `md2md.yaml` is as follows:

```YAML
end2end_eval:          # Specify task name, common for end-to-end evaluation
  metrics:             # Configure metrics to use
    text_block:        # Configuration for text paragraphs
      metric:
        - Edit_dist    # Normalized Edit Distance
        - BLEU         
        - METEOR
    display_formula:   # Configuration for display formulas
      metric:
        - Edit_dist
        - CDM          # Only supports exporting format required for CDM evaluation, stored in results
    table:             # Configuration for tables
      metric:
        - TEDS
        - Edit_dist
    reading_order:     # Configuration for reading order
      metric:
        - Edit_dist
  dataset:                                               # Dataset configuration
    dataset_name: md2md_dataset                          # Dataset name, no need to modify
    ground_truth:                                        # Configuration for ground truth dataset
      data_path: ./demo_data/omnidocbench_demo/mds       # Path to OmniDocBench markdown folder
      page_info: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json          # Path to OmniDocBench JSON file, mainly used to get page-level attributes
    prediction:                                          # Configuration for model predictions
      data_path: ./demo_data/end2end                     # Folder path for model's PDF page parsing markdown results
    match_method: quick_match                            # Matching method, options: no_split/no_split/quick_match
    filter:                                              # Page-level filtering
      language: english                                  # Page attributes and corresponding tags to evaluate
```

The `data_path` under `prediction` is the folder path for the model's PDF page parsing results, which contains markdown files corresponding to each page. The filenames match the image names, with only the `.jpg` extension replaced with `.md`.

The `data_path` under `ground_truth` is the path to OmniDocBench's markdown folder, with filenames corresponding one-to-one with the model's PDF page parsing markdown results. The `page_info` path under `ground_truth` is the path to OmniDocBench's JSON file, mainly used to obtain page-level attributes. If page-level attribute evaluation results are not needed, this field can be commented out. However, without configuring the `page_info` field under `ground_truth`, the `filter` related functionality cannot be used.

For explanations of other fields in the config, please refer to the *End-to-end Evaluation - end2end* section.

</details>

### Formula Recognition Evaluation

OmniDocBench contains bounding box information for formulas on each PDF page along with corresponding formula recognition annotations, making it suitable as a benchmark for formula recognition evaluation. Formulas include display formulas (`equation_isolated`) and inline formulas (`equation_inline`). Currently, this repo provides examples for evaluating display formulas.

<table style="width: 47%;">
  <thead>
    <tr>
      <th>Models</th>
      <th>CDM</th>
      <th>ExpRate@CDM</th>
      <th>BLEU</th>
      <th>Norm Edit</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GOT-OCR</td>
      <td>74.1</td>
      <td>28.0</td>
      <td>55.07</td>
      <td>0.290</td>
    </tr>
    <tr>
      <td>Mathpix</td>
      <td><ins>86.6</ins></td>
      <td>2.8</td>
      <td><b>66.56</b></td>
      <td>0.322</td>
    </tr>
    <tr>
      <td>Pix2Tex</td>
      <td>73.9</td>
      <td>39.5</td>
      <td>46.00</td>
      <td>0.337</td>
    </tr>
    <tr>
      <td>UniMERNet-B</td>
      <td>85.0</td>
      <td><ins>60.2</ins></td>
      <td><ins>60.84</ins></td>
      <td><b>0.238</b></td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><b>86.8</b></td>
      <td><b>65.5</b></td>
      <td>45.17</td>
      <td><ins>0.282</ins></td>
    </tr>
    <tr>
      <td>InternVL2-Llama3-76B</td>
      <td>67.4</td>
      <td>54.5</td>
      <td>47.63</td>
      <td>0.308</td>
    </tr>
    <tr>
      <td>Qwen2-VL-72B</td>
      <td>83.8</td>
      <td>55.4</td>
      <td>53.71</td>
      <td>0.285</td>
    </tr>
  </tbody>
</table>
<p>Component-level formula recognition evaluation on OmniDocBench (v1.0) formula subset.</p>


Formula recognition evaluation can be configured according to [formula_recognition](./configs/formula_recognition.yaml).

<details>
  <summary>【Field explanations for formula_recognition.yaml】</summary>

The configuration of `formula_recognition.yaml` is as follows:

```YAML
recogition_eval:      # Specify task name, common for all recognition-related tasks
  metrics:            # Configure metrics to use
    - Edit_dist       # Normalized Edit Distance
    - CDM             # Only supports exporting formats required for CDM evaluation, stored in results
  dataset:                                                                   # Dataset configuration
    dataset_name: omnidocbench_single_module_dataset                         # Dataset name, no need to modify if following specified input format
    ground_truth:                                                            # Ground truth dataset configuration  
      data_path: ./demo_data/recognition/OmniDocBench_demo_formula.json      # JSON file containing both ground truth and model prediction results
      data_key: latex                                                        # Field name storing Ground Truth, for OmniDocBench, formula recognition results are stored in latex field
      category_filter: ['equation_isolated']                                 # Categories used for evaluation, in formula recognition, the category_name is equation_isolated
    prediction:                                                              # Model prediction configuration
      data_key: pred                                                         # Field name storing model prediction results, this is user-defined
    category_type: formula                                                   # category_type is mainly used for selecting data preprocessing strategy, options: formula/text
```

For the `metrics` section, in addition to the supported metrics, it also supports exporting formats required for [CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm) evaluation. Simply configure the CDM field in metrics to organize the output into CDM input format, which will be stored in [result](./result).

For the `dataset` section, the data format in the `ground_truth` `data_path` remains consistent with OmniDocBench, with just a custom field added under the corresponding formula sample to store the model's prediction results. The field storing prediction information is specified through the `data_key` under the `prediction` field in `dataset`, such as `pred`. For more details about OmniDocBench's file structure, please refer to the "Dataset Introduction" section. The input format for model results can be found in [OmniDocBench_demo_formula](./demo_data/recognition/OmniDocBench_demo_formula.json), which follows this format:

```JSON
[{
    "layout_dets": [    // List of page elements
        {
            "category_type": "equation_isolated",  // OmniDocBench category name
            "poly": [    // OmniDocBench position info, coordinates for top-left, top-right, bottom-right, bottom-left corners (x,y)
                136.0, 
                781.0,
                340.0,
                781.0,
                340.0,
                806.0,
                136.0,
                806.0
            ],
            ...   // Other OmniDocBench fields
            "latex": "$xxx$",  // LaTeX formula will be written here
            "pred": "$xxx$",   // !! Model prediction result stored here, user-defined new field at same level as ground truth
            
        ...
    ],
    "page_info": {...},        // OmniDocBench page information
    "extra": {...}             // OmniDocBench annotation relationship information
},
...
]
```

Here is a model inference script for reference:

```PYTHON
import os
import json
from PIL import Image

def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

question = "<image>\nPlease convert this cropped image directly into latex."

with open('./demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r') as f:
    samples = json.load(f)
    
for sample in samples:
    img_name = os.path.basename(sample['page_info']['image_path'])
    img_path = os.path.join('./Docparse/images', img_name)
    img = Image.open(img_path)

    if not os.path.exists(img_path):
        print('No exist: ', img_name)
        continue

    for i, anno in enumerate(sample['layout_dets']):
        if anno['category_type'] != 'equation_isolated':   # Filter out equation_isolated category for evaluation
            continue

        bbox = poly2bbox(anno['poly'])
        im = img.crop(bbox).convert('RGB')
        response = model.chat(im, question)  # Modify the way the image is passed in according to the model
        anno['pred'] = response              # Directly add a new field to store the model's inference results under the corresponding annotation

with open('./demo_data/recognition/OmniDocBench_demo_formula.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False)
```

</details>

### Text OCR Evaluation

OmniDocBench contains bounding box information and corresponding text recognition annotations for all text in each PDF page, making it suitable as a benchmark for OCR evaluation. The text annotations include both block-level and span-level annotations, both of which can be used for evaluation. This repo currently provides an example of block-level evaluation, which evaluates OCR at the text paragraph level.

<table style="width: 90%; margin: auto; border-collapse: collapse; font-size: small;">
  <thead>
    <tr>
      <th rowspan="2">Model Type</th>
      <th rowspan="2">Model</th>
      <th colspan="3">Language</th>
      <th colspan="3">Text background</th>
      <th colspan="4">Text Rotate</th>
    </tr>
    <tr>
      <th><i>EN</i></th>
      <th><i>ZH</i></th>
      <th><i>Mixed</i></th>
      <th><i>White</i></th>
      <th><i>Single</i></th>
      <th><i>Multi</i></th>
      <th><i>Normal</i></th>
      <th><i>Rotate90</i></th>
      <th><i>Rotate270</i></th>
      <th><i>Horizontal</i></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="7" style="text-align: center;">Pipeline Tools<br>&<br>Expert Vision<br>Models</td>
      <td>PaddleOCR</td>
      <td>0.071</td>
      <td><b>0.055</b></td>
      <td><ins>0.118</ins></td>
      <td><b>0.060</b></td>
      <td><b>0.038</b></td>
      <td><ins>0.085</ins></td>
      <td><b>0.060</b></td>
      <td><b>0.015</b></td>
      <td><ins>0.285</ins></td>
      <td><b>0.021</b></td>
    </tr>
    <tr>
      <td>OpenOCR</td>
      <td>0.07</td>
      <td><ins>0.068</ins></td>
      <td><b>0.106</b></td>
      <td><ins>0.069</ins></td>
      <td>0.058</td>
      <td><b>0.081</b></td>
      <td><ins>0.069</ins></td>
      <td><ins>0.038</ins></td>
      <td>0.891</td>
      <td><ins>0.025</ins></td>
    </tr>
    <tr>
      <td>Tesseract-OCR</td>
      <td>0.096</td>
      <td>0.551</td>
      <td>0.250</td>
      <td>0.439</td>
      <td>0.328</td>
      <td>0.331</td>
      <td>0.426</td>
      <td>0.117</td>
      <td>0.969</td>
      <td>0.984</td>
    </tr>
    <tr>
      <td>EasyOCR</td>
      <td>0.26</td>
      <td>0.398</td>
      <td>0.445</td>
      <td>0.366</td>
      <td>0.287</td>
      <td>0.388</td>
      <td>0.36</td>
      <td>0.97</td>
      <td>0.997</td>
      <td>0.926</td>
    </tr>
    <tr>
      <td>Surya</td>
      <td>0.057</td>
      <td>0.123</td>
      <td>0.164</td>
      <td>0.093</td>
      <td>0.186</td>
      <td>0.235</td>
      <td>0.104</td>
      <td>0.634</td>
      <td>0.767</td>
      <td>0.255</td>
    </tr>
    <tr>
      <td>Mathpix</td>
      <td><ins>0.033</ins></td>
      <td>0.240</td>
      <td>0.261</td>
      <td>0.185</td>
      <td>0.121</td>
      <td>0.166</td>
      <td>0.180</td>
      <td><ins>0.038</ins></td>
      <td><b>0.185</b></td>
      <td>0.638</td>
    </tr>
    <tr>
      <td>GOT-OCR</td>
      <td>0.041</td>
      <td>0.112</td>
      <td>0.135</td>
      <td>0.092</td>
      <td><ins>0.052</ins></td>
      <td>0.155</td>
      <td>0.091</td>
      <td>0.562</td>
      <td>0.966</td>
      <td>0.097</td>
    </tr>
    <tr>
      <td rowspan="3" style="text-align: center;">Vision Language<br>Models</td>
      <td>Qwen2-VL-72B</td>
      <td>0.072</td>
      <td>0.274</td>
      <td>0.286</td>
      <td>0.234</td>
      <td>0.155</td>
      <td>0.148</td>
      <td>0.223</td>
      <td>0.273</td>
      <td>0.721</td>
      <td>0.067</td>
    </tr>
    <tr>
      <td>InternVL2-76B</td>
      <td>0.074</td>
      <td>0.155</td>
      <td>0.242</td>
      <td>0.113</td>
      <td>0.352</td>
      <td>0.269</td>
      <td>0.132</td>
      <td>0.610</td>
      <td>0.907</td>
      <td>0.595</td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><b>0.020</b></td>
      <td>0.224</td>
      <td>0.125</td>
      <td>0.167</td>
      <td>0.140</td>
      <td>0.220</td>
      <td>0.168</td>
      <td>0.115</td>
      <td>0.718</td>
      <td>0.132</td>
    </tr>
  </tbody>
</table>
<p>Component-level OCR text recognition evaluation on OmniDocBench (v1.0) text subset.</p>

OCR text recognition evaluation can be configured according to [ocr](./configs/ocr.yaml). 

<details>
  <summary>【The field explanation of ocr.yaml】</summary>

The configuration file for `ocr.yaml` is as follows:

```YAML
recogition_eval:      # Specify task name, common for all recognition-related tasks
  metrics:            # Configure metrics to use
    - Edit_dist       # Normalized Edit Distance
    - BLEU
    - METEOR
  dataset:                                                                   # Dataset configuration
    dataset_name: omnidocbench_single_module_dataset                         # Dataset name, no need to modify if following the specified input format
    ground_truth:                                                            # Ground truth dataset configuration
      data_path: ./demo_data/recognition/OmniDocBench_demo_text_ocr.json     # JSON file containing both ground truth and model prediction results
      data_key: text                                                         # Field name storing Ground Truth, for OmniDocBench, text recognition results are stored in the text field, all block level annotations containing text field will participate in evaluation
    prediction:                                                              # Model prediction configuration
      data_key: pred                                                         # Field name storing model prediction results, this is user-defined
    category_type: text                                                      # category_type is mainly used for selecting data preprocessing strategy, options: formula/text
```

For the `dataset` section, the input `ground_truth` `data_path` follows the same data format as OmniDocBench, with just a new custom field added under samples containing the text field to store the model's prediction results. The field storing prediction information is specified through the `data_key` under the `prediction` field in `dataset`, for example `pred`. The input format of the dataset can be referenced in [OmniDocBench_demo_text_ocr](./demo_data/recognition/OmniDocBench_demo_text_ocr.json), and the meanings of various fields can be found in the examples provided in the *Formula Recognition Evaluation* section.

Here is a reference model inference script for your consideration:

```PYTHON
import os
import json
from PIL import Image

def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

question = "<image>\nPlease convert this cropped image directly into latex."

with open('./demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r') as f:
    samples = json.load(f)
    
for sample in samples:
    img_name = os.path.basename(sample['page_info']['image_path'])
    img_path = os.path.join('./Docparse/images', img_name)
    img = Image.open(img_path)

    if not os.path.exists(img_path):
        print('No exist: ', img_name)
        continue

    for i, anno in enumerate(sample['layout_dets']):
        if not anno.get('text'):             # Filter out annotations containing the text field from OmniDocBench for model inference
            continue

        bbox = poly2bbox(anno['poly'])
        im = img.crop(bbox).convert('RGB')
        response = model.chat(im, question)  # Modify the way the image is passed in according to the model
        anno['pred'] = response              # Directly add a new field to store the model's inference results under the corresponding annotation

with open('./demo_data/recognition/OmniDocBench_demo_text_ocr.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False)
```

</details>

### Table Recognition Evaluation

OmniDocBench contains bounding box information for tables on each PDF page along with corresponding table recognition annotations, making it suitable as a benchmark for table recognition evaluation. The table annotations are available in both HTML and LaTeX formats, with this repository currently providing examples for HTML format evaluation.

<table style="width: 100%; margin: auto; border-collapse: collapse; font-size: small;">
  <thead>
    <tr>
      <th rowspan="2">Model Type</th>
      <th rowspan="2">Model</th>
      <th colspan="3">Language</th>
      <th colspan="4">Table Frame Type</th>
      <th colspan="4">Special Situation</th>
      <th rowspan="2">Overall</th>
    </tr>
    <tr>
      <th><i>EN</i></th>
      <th><i>ZH</i></th>
      <th><i>Mixed</i></th>
      <th><i>Full</i></th>
      <th><i>Omission</i></th>
      <th><i>Three</i></th>
      <th><i>Zero</i></th>
      <th><i>Merge Cell</i>(+/-)</th>
      <th><i>Formula</i>(+/-)</th>
      <th><i>Colorful</i>(+/-)</th>
      <th><i>Rotate</i>(+/-)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2" style="text-align: center;">OCR-based Models</td>
      <td>PaddleOCR</td>
      <td><ins>76.8</ins></td>
      <td>71.8</td>
      <td>80.1</td>
      <td>67.9</td>
      <td>74.3</td>
      <td><ins>81.1</ins></td>
      <td>74.5</td>
      <td><ins>70.6/75.2</ins></td>
      <td><ins>71.3/74.1</ins></td>
      <td><ins>72.7/74.0</ins></td>
      <td>23.3/74.6</td>
      <td>73.6</td>
    </tr>
    <tr>
      <td>RapidTable</td>
      <td><b>80.0</b></td>
      <td><b>83.2</b></td>
      <td><b>91.2</b></td>
      <td><b>83.0</b></td>
      <td><b>79.7</b></td>
      <td><b>83.4</b></td>
      <td>78.4</td>
      <td><b>77.1/85.4</b></td>
      <td><b>76.7/83.9</b></td>
      <td><b>77.6/84.9</b></td>
      <td><ins>25.2/83.7</ins></td>
      <td><b>82.5</b></td>
    </tr>
    <tr>
      <td rowspan="2" style="text-align: center;">Expert VLMs</td>
      <td>StructEqTable</td>
      <td>72.8</td>
      <td><ins>75.9</ins></td>
      <td>83.4</td>
      <td>72.9</td>
      <td><ins>76.2</ins></td>
      <td>76.9</td>
      <td><b>88</b></td>
      <td>64.5/81</td>
      <td>69.2/76.6</td>
      <td>72.8/76.4</td>
      <td><b>30.5/76.2</b></td>
      <td><ins>75.8</ins></td>
    </tr>
    <tr>
      <td>GOT-OCR</td>
      <td>72.2</td>
      <td>75.5</td>
      <td><ins>85.4</ins></td>
      <td><ins>73.1</ins></td>
      <td>72.7</td>
      <td>78.2</td>
      <td>75.7</td>
      <td>65.0/80.2</td>
      <td>64.3/77.3</td>
      <td>70.8/76.9</td>
      <td>8.5/76.3</td>
      <td>74.9</td>
    </tr>
    <tr>
      <td rowspan="2" style="text-align: center;">General VLMs</td>
      <td>Qwen2-VL-7B</td>
      <td>70.2</td>
      <td>70.7</td>
      <td>82.4</td>
      <td>70.2</td>
      <td>62.8</td>
      <td>74.5</td>
      <td><ins>80.3</ins></td>
      <td>60.8/76.5</td>
      <td>63.8/72.6</td>
      <td>71.4/70.8</td>
      <td>20.0/72.1</td>
      <td>71.0</td>
    </tr>
    <tr>
      <td>InternVL2-8B</td>
      <td>70.9</td>
      <td>71.5</td>
      <td>77.4</td>
      <td>69.5</td>
      <td>69.2</td>
      <td>74.8</td>
      <td>75.8</td>
      <td>58.7/78.4</td>
      <td>62.4/73.6</td>
      <td>68.2/73.1</td>
      <td>20.4/72.6</td>
      <td>71.5</td>
    </tr>
  </tbody>
</table>
<p>Component-level Table Recognition evaluation on OmniDocBench(v1.0) table subset. <i>(+/-)</i> means <i>with/without</i> special situation.</p>


Table recognition evaluation can be configured according to [table_recognition](./configs/table_recognition.yaml). 

**For tables predicted to be in LaTeX format, the [latexml](https://math.nist.gov/~BMiller/LaTeXML/) tool will be used to convert LaTeX to HTML before evaluation. The evaluation code will automatically perform format conversion, and users need to preinstall [latexml](https://math.nist.gov/~BMiller/LaTeXML/)**

<details>
  <summary>【The field explanation of table_recognition.yaml】</summary>

The configuration file for `table_recognition.yaml` is as follows:

```YAML
recogition_eval:      # Specify task name, common for all recognition-related tasks
  metrics:            # Configure metrics to use
    - TEDS            # Tree Edit Distance based Similarity
    - Edit_dist       # Normalized Edit Distance
  dataset:                                                                   # Dataset configuration
    dataset_name: omnidocbench_single_module_dataset                         # Dataset name, no need to modify if following specified input format
    ground_truth:                                                            # Configuration for ground truth dataset
      data_path: ./demo_data/recognition/OmniDocBench_demo_table.json        # JSON file containing both ground truth and model prediction results
      data_key: html                                                         # Field name storing Ground Truth, for OmniDocBench, table recognition results are stored in html and latex fields, change to latex when evaluating latex format tables
      category_filter: table                                                 # Category for evaluation, in table recognition, the category_name is table
    prediction:                                                              # Configuration for model prediction results
      data_key: pred                                                         # Field name storing model prediction results, this is user-defined
    category_type: table                                                     # category_type is mainly used for data preprocessing strategy selection
```

For the `dataset` section, the data format in the `ground_truth`'s `data_path` remains consistent with OmniDocBench, with only a custom field added under the corresponding table sample to store the model's prediction result. The field storing prediction information is specified through `data_key` under the `prediction` field in `dataset`, such as `pred`. For more details about OmniDocBench's file structure, please refer to the "Dataset Introduction" section. The input format for model results can be found in [OmniDocBench_demo_table](./demo_data/recognition/OmniDocBench_demo_table.json), which follows this format:

```JSON
[{
    "layout_dets": [    // List of page elements
        {
            "category_type": "table",  // OmniDocBench category name
            "poly": [    // OmniDocBench position info: x,y coordinates for top-left, top-right, bottom-right, bottom-left corners
                136.0, 
                781.0,
                340.0,
                781.0,
                340.0,
                806.0,
                136.0,
                806.0
            ],
            ...   // Other OmniDocBench fields
            "latex": "$xxx$",  // Table LaTeX annotation goes here
            "html": "$xxx$",  // Table HTML annotation goes here
            "pred": "$xxx$",   // !! Model prediction result stored here, user-defined new field at same level as ground truth
            
        ...
    ],
    "page_info": {...},        // OmniDocBench page information
    "extra": {...}             // OmniDocBench annotation relationship information
},
...
]
```

Here is a model inference script for reference:

```PYTHON
import os
import json
from PIL import Image

def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

question = "<image>\nPlease convert this cropped image directly into html format of table."

with open('./demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r') as f:
    samples = json.load(f)
    
for sample in samples:
    img_name = os.path.basename(sample['page_info']['image_path'])
    img_path = os.path.join('./demo_data/omnidocbench_demo/images', img_name)
    img = Image.open(img_path)

    if not os.path.exists(img_path):
        print('No exist: ', img_name)
        continue

    for i, anno in enumerate(sample['layout_dets']):
        if anno['category_type'] != 'table':   # Filter out the table category for evaluation
            continue

        bbox = poly2bbox(anno['poly'])
        im = img.crop(bbox).convert('RGB')
        response = model.chat(im, question)  # Need to modify the way the image is passed in depending on the model
        anno['pred'] = response              # Directly add a new field to store the model's inference result at the same level as the ground truth

with open('./demo_data/recognition/OmniDocBench_demo_table.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False)
```

</details>


### Layout Detection

OmniDocBench contains bounding box information for all document components on each PDF page, making it suitable as a benchmark for layout detection task evaluation.

<table style="width: 95%; margin: auto; border-collapse: collapse;">
  <thead>
    <tr>
      <th>Model</th>
      <th>Backbone</th>
      <th>Params</th>
      <th>Book</th>
      <th>Slides</th>
      <th>Research<br>Report</th>
      <th>Textbook</th>
      <th>Exam<br>Paper</th>
      <th>Magazine</th>
      <th>Academic<br>Literature</th>
      <th>Notes</th>
      <th>Newspaper</th>
      <th>Average</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>DiT-L</sup></td>
      <td>ViT-L</td>
      <td>361.6M</td>
      <td><ins>43.44</ins></td>
      <td>13.72</td>
      <td>45.85</td>
      <td>15.45</td>
      <td>3.40</td>
      <td>29.23</td>
      <td><strong>66.13</strong></td>
      <td>0.21</td>
      <td>23.65</td>
      <td>26.90</td>
    </tr>
    <tr>
      <td>LayoutLMv3</sup></td>
      <td>RoBERTa-B</td>
      <td>138.4M</td>
      <td>42.12</td>
      <td>13.63</td>
      <td>43.22</td>
      <td>21.00</td>
      <td>5.48</td>
      <td>31.81</td>
      <td><ins>64.66</ins></td>
      <td>0.80</td>
      <td>30.84</td>
      <td>28.84</td>
    </tr>
    <tr>
      <td>DocLayout-YOLO</sup></td>
      <td>v10m</td>
      <td>19.6M</td>
      <td><strong>43.71</strong></td>
      <td><strong>48.71</strong></td>
      <td><strong>72.83</strong></td>
      <td><strong>42.67</strong></td>
      <td><strong>35.40</strong></td>
      <td><ins>51.44</ins></td>
      <td><ins>64.64</ins></td>
      <td><ins>9.54</ins></td>
      <td><strong>57.54</strong></td>
      <td><strong>47.38</strong></td>
    </tr>
    <tr>
      <td>SwinDocSegmenter</sup></td>
      <td>Swin-L</td>
      <td>223M</td>
      <td>42.91</td>
      <td><ins>28.20</ins></td>
      <td><ins>47.29</ins></td>
      <td><ins>32.44</ins></td>
      <td><ins>20.81</ins></td>
      <td><strong>52.35</strong></td>
      <td>48.54</td>
      <td><strong>12.38</strong></td>
      <td><ins>38.06</ins></td>
      <td><ins>35.89</ins></td>
    </tr>
    <tr>
      <td>GraphKD</sup></td>
      <td>R101</td>
      <td>44.5M</td>
      <td>39.03</td>
      <td>16.18</td>
      <td>39.92</td>
      <td>22.82</td>
      <td>14.31</td>
      <td>37.61</td>
      <td>44.43</td>
      <td>5.71</td>
      <td>23.86</td>
      <td>27.10</td>
    </tr>
    <tr>
      <td>DOCX-Chain</sup></td>
      <td>-</td>
      <td>-</td>
      <td>30.86</td>
      <td>11.71</td>
      <td>39.62</td>
      <td>19.23</td>
      <td>10.67</td>
      <td>23.00</td>
      <td>41.60</td>
      <td>1.80</td>
      <td>16.96</td>
      <td>21.27</td>
    </tr>
  </tbody>
</table>

<p>Component-level layout detection evaluation on OmniDocBench (v1.0) layout subset: mAP results by PDF page type.</p>



Layout detection config file reference [layout_detection](./configs/layout_detection.yaml), data format reference [detection_prediction](./demo_data/detection/detection_prediction.json).

<details>
  <summary>【The field explanation of layout_detection.yaml】</summary>

Here is the configuration file for `layout_detection.yaml`:

```YAML
detection_eval:   # Specify task name, common for all detection-related tasks
  metrics:
    - COCODet     # Detection task related metrics, mainly mAP, mAR etc.
  dataset: 
    dataset_name: detection_dataset_simple_format       # Dataset name, no need to modify if following specified input format
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json               # Path to OmniDocBench JSON file
    prediction:
      data_path: ./demo_data/detection/detection_prediction.json                    # Path to model prediction result JSON file
    filter:                                             # Page level filtering
      data_source: exam_paper                           # Page attributes and corresponding tags to be evaluated
  categories:
    eval_cat:                # Categories participating in final evaluation
      block_level:           # Block level categories, see OmniDocBench evaluation set introduction for details
        - title              # Title
        - text               # Text  
        - abandon            # Includes headers, footers, page numbers, and page annotations
        - figure             # Image
        - figure_caption     # Image caption
        - table              # Table
        - table_caption      # Table caption
        - table_footnote     # Table footnote
        - isolate_formula    # Display formula (this is a layout display formula, lower priority than 14)
        - formula_caption    # Display formula label
    gt_cat_mapping:          # Mapping table from ground truth to final evaluation categories, key is ground truth category, value is final evaluation category name
      figure_footnote: figure_footnote
      figure_caption: figure_caption 
      page_number: abandon 
      header: abandon 
      page_footnote: abandon
      table_footnote: table_footnote 
      code_txt: figure 
      equation_caption: formula_caption 
      equation_isolated: isolate_formula
      table: table 
      refernece: text 
      table_caption: table_caption 
      figure: figure 
      title: title 
      text_block: text 
      footer: abandon
    pred_cat_mapping:       # Mapping table from prediction to final evaluation categories, key is prediction category, value is final evaluation category name
      title : title
      plain text: text
      abandon: abandon
      figure: figure
      figure_caption: figure_caption
      table: table
      table_caption: table_caption
      table_footnote: table_footnote
      isolate_formula: isolate_formula
      formula_caption: formula_caption
```

The `filter` field can be used to filter the dataset. For example, setting the `filter` field under `dataset` to `data_source: exam_paper` will filter for pages with data type exam_paper. For more page attributes, please refer to the "Evaluation Set Introduction" section. If you want to evaluate the full dataset, comment out the `filter` related fields.

The `data_path` under the `prediction` section in `dataset` takes the model's prediction as input, with the following data format:

```JSON
{
    "results": [
        {
            "image_name": "docstructbench_llm-raw-scihub-o.O-adsc.201190003.pdf_6",                     // image name
            "bbox": [53.892921447753906, 909.8675537109375, 808.5555419921875, 1006.2714233398438],     // bounding box coordinates, representing x,y coordinates of top-left and bottom-right corners
            "category_id": 1,                                                                           // category ID number
            "score": 0.9446213841438293                                                                 // confidence score
        }, 
        ...                                                                                             // all bounding boxes are flattened in a single list
    ],
    "categories": {"0": "title", "1": "plain text", "2": "abandon", ...}                                // mapping between category IDs and category names
```

</details>

### Formula Detection

OmniDocBench contains bounding box information for each formula on each PDF page, making it suitable as a benchmark for formula detection task evaluation.

The format for formula detection is essentially the same as layout detection. Formulas include both inline and display formulas. In this section, we provide a config example that can evaluate detection results for both display formulas and inline formulas simultaneously. Formula detection can be configured according to [formula_detection](./configs/formula_detection.yaml).

<details>
  <summary>【The field explanation of formula_detection.yaml】</summary>

Here is the configuration file for `formula_detection.yaml`:

```YAML
detection_eval:   # Specify task name, common for all detection-related tasks
  metrics:
    - COCODet     # Detection task related metrics, mainly mAP, mAR etc.
  dataset: 
    dataset_name: detection_dataset_simple_format       # Dataset name, no need to modify if following specified input format
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json               # Path to OmniDocBench JSON file
    prediction:
      data_path: ./demo_data/detection/detection_prediction.json                     # Path to model prediction JSON file
    filter:                                             # Page-level filtering
      data_source: exam_paper                           # Page attributes and corresponding tags to evaluate
  categories:
    eval_cat:                                  # Categories participating in final evaluation
      block_level:                             # Block level categories, see OmniDocBench dataset intro for details
        - isolate_formula                      # Display formula
      span_level:                              # Span level categories, see OmniDocBench dataset intro for details
        - inline_formula                       # Inline formula
    gt_cat_mapping:                            # Mapping table from ground truth to final evaluation categories, key is ground truth category, value is final evaluation category name
      equation_isolated: isolate_formula
      equation_inline: inline_formula
    pred_cat_mapping:                          # Mapping table from prediction to final evaluation categories, key is prediction category, value is final evaluation category name
      interline_formula: isolate_formula
      inline_formula: inline_formula
```

Please refer to the `Layout Detection` section for parameter explanations and dataset format. The main difference between formula detection and layout detection is that under the `eval_cat` category that participates in the final evaluation, a `span_level` category `inline_formula` has been added. Both span_level and block_level categories will participate together in the evaluation.

</details>

## Tools

We provide several tools in the `tools` directory:
- [json2md](./tools/json2md.py) for converting OmniDocBench from JSON format to Markdown format;
- [visualization](./tools/visualization.py) for visualizing OmniDocBench JSON files;
- [generate_result_tables](./tools/generate_result_tables.py) for generating the result leaderboard of the evaluation;
- The [model_infer](./tools/model_infer) folder provides some model inference scripts for reference. Please use after configuring the model environment. Including:
  - `<model_name>_img2md.py` for calling the models to convert images to Markdown format;
  - `<model_name>_ocr.py` is to invoke the models for text recognition of block-level document text paragraphs;
  - `<model_name>_formula.py` is used to call the models for formula recognition of display formulas (`equation_isolated`);

## The evaluation model information

### End2End
<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Official Website</th>
      <th>Evaluation Version/Model Weights</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>MinerU</td>
      <td><a href="https://mineru.org.cn/">MinerU</a></td>
      <td>2.1.1</td>
    </tr>
    <tr>
      <td>Marker</td>
      <td><a href="https://github.com/VikParuchuri/marker">Marker</a></td>
      <td>1.8.2</td>
    </tr>
    <tr>
      <td>Mathpix</td>
      <td><a href="https://mathpix.com/">Mathpix</a></td>
      <td>———</td>
    </tr>
    <tr>
      <td>PaddleOCR PP-StructureV3</td>
      <td><a href="https://github.com/PaddlePaddle/PaddleOCR">PaddleOCR</a></td>
      <td><a href="https://www.paddleocr.ai/latest/version3.x/pipeline_usage/PP-StructureV3.html">PP-StructureV3</a></td>
    </tr>
    <tr>
      <td>Docling</td>
      <td><a href="https://ds4sd.github.io/docling/">Docling</a></td>
      <td>2.14.0</td>
    </tr>
    <tr>
      <td>Pix2Text</td>
      <td><a href="https://github.com/breezedeus/Pix2Text">Pix2Text</a></td>
      <td>1.1.2.3</td>
    </tr>
    <tr>
      <td>Unstructured</td>
      <td><a href="https://github.com/Unstructured-IO/unstructured">Unstructured</a></td>
      <td>0.16.23</td>
    </tr>
    <tr>
      <td>OpenParse</td>
      <td><a href="https://github.com/Filimoa/open-parse">OpenParse</a></td>
      <td>0.7.0</td>
    </tr>
    <tr>
      <td>MinerU2-VLM</td>
      <td><a href="https://github.com/opendatalab/MinerU">MinerU</a></td>
      <td><a href="https://huggingface.co/opendatalab/MinerU2.0-2505-0.9B">MinerU2.0-2505-0.9B</a></td>
    </tr>
    <tr>
      <td>MonkeyOCR-pro-1.2B</td>
      <td><a href="https://github.com/Yuliang-Liu/MonkeyOCR">MonkeyOCR</a></td>
      <td><a href="https://huggingface.co/echo840/MonkeyOCR-pro-1.2B">HuggingFace MonkeyOCR-pro-1.2B</a></td>
    </tr>
    <tr>
      <td>Dolphin</td>
      <td><a href="https://github.com/bytedance/Dolphin">Dolphin</a></td>
      <td><a href="https://huggingface.co/ByteDance/Dolphin">HuggingFace Dolphin</a></td>
    </tr>
    <tr>
      <td>Nanonets-OCR-s</td>
      <td><a href="https://nanonets.com/research/nanonets-ocr-s/">Nanonets-OCR-s</a></td>
      <td><a href="https://huggingface.co/nanonets/Nanonets-OCR-s">HuggingFace Nanonets-OCR-s</a></td>
    </tr>
    <tr>
      <td>OCRFlux</td>
      <td><a href="https://github.com/chatdoc-com/OCRFlux">OCRFlux</a></td>
      <td><a href="https://huggingface.co/ChatDOC/OCRFlux-3B">HuggingFace OCRFlux-3B</a></td>
    </tr>
    <tr>
      <td>Mistral OCR</td>
      <td><a href="https://mistral.ai/news/mistral-ocr?utm_source=ai-bot.cn">Mistral OCR</a></td>
      <td>2503</td>
    </tr>
    <tr>
      <td>GOT-OCR</td>
      <td><a href="https://github.com/Ucas-HaoranWei/GOT-OCR2.0">GOT-OCR</a></td>
      <td><a href="https://huggingface.co/stepfun-ai/GOT-OCR2_0">Hugging Face GOT-OCR2_0</a></td>
    </tr>
    <tr>
      <td>Nougat</td>
      <td><a href="https://github.com/facebookresearch/nougat">Nougat</a></td>
      <td><a href="https://huggingface.co/docs/transformers/main/en/model_doc/nougat">Hugging Face Nougat base</a></td>
    </tr>
    <tr>
      <td>olmOCR</td>
      <td><a href="https://github.com/allenai/olmocr">olmOCR</a></td>
      <td>Sglang</td>
    </tr>
    <tr>
      <td>SmolDocling</td>
      <td><a href="https://huggingface.co/ds4sd/SmolDocling-256M-preview">SmolDocling-256M-Preview-transformer</a></td>
      <td>256M-Preview-transformer</td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><a href="https://openai.com/index/hello-gpt-4o/">OpenAI GPT4o</a></td>
      <td>2024-08-06</td>
    </tr>
    <tr>
      <td>Gemini-2.0 Flash</td>
      <td><a href="https://deepmind.google/technologies/gemini/flash/">Gemini-2.0 Flash</a></td>
      <td>-</td>
    </tr>
    <tr>
      <td>Gemini-2.5 Pro</td>
      <td><a href="https://deepmind.google/technologies/gemini/pro/">Gemini-2.5 Pro</a></td>
      <td>-</td>
    </tr>
    <tr>
      <td>Qwen2-VL-72B</td>
      <td><a href="https://qwenlm.github.io/zh/blog/qwen2-vl/">Qwen2-VL</a></td>
      <td><a href="https://huggingface.co/Qwen/Qwen2-VL-72B-Instruct">Hugging Face Qwen2-VL-72B-Instruct</a>
      </td>
    <tr>
      <td>Qwen2.5-VL-7B</td>
      <td><a href="https://github.com/QwenLM/Qwen2.5">Qwen2.5-VL</a></td>
      <td><a href="https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct">Hugging Face Qwen2.5-VL-7B-Instruct</a>    </td>
    </tr>
    <tr>
      <td>Qwen2.5-VL-72B</td>
      <td><a href="https://github.com/QwenLM/Qwen2.5">Qwen2.5-VL</a></td>
      <td><a href="https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct">Hugging Face Qwen2.5-VL-72B-Instruct</a>    </td>
    </tr>
    <tr>
      <td>InternVL2-Llama3-76B</td>
      <td><a href="https://github.com/OpenGVLab/InternVL">InternVL</a></td>
      <td><a href="https://huggingface.co/OpenGVLab/InternVL2-Llama3-76B">Hugging Face InternVL2-Llama3-76B</a></td>
    </tr>
    <tr>
      <td>InternVL3-78B</td>
      <td><a href="https://github.com/OpenGVLab/InternVL">InternVL</a></td>
      <td><a href="https://huggingface.co/OpenGVLab/InternVL3-78B">Hugging Face InternVL3-78B</a></td>
    </tr>
  </tbody>
</table>

### Text Recognition

<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Official Website</th>
      <th>Evaluation Version/Model Weights</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>PaddleOCR</td>
      <td><a href="https://www.paddlepaddle.org.cn/hub/scene/ocr">PaddlePaddle OCR</a></td>
      <td>2.9.1</td>
    </tr>
    <tr>
      <td>Tesseract</td>
      <td><a href="https://tesseract-ocr.github.io/tessdoc/">Tesseract OCR</a></td>
      <td>5.5</td>
    </tr>
    <tr>
      <td>OpenOCR</td>
      <td><a href="https://github.com/Topdu/OpenOCR">OpenOCR GitHub</a></td>
      <td>0.0.6</td>
    </tr>
    <tr>
      <td>EasyOCR</td>
      <td><a href="https://www.easyproject.cn/easyocr/">EasyOCR</a></td>
      <td>1.7.2</td>
    </tr>
    <tr>
      <td>Surya</td>
      <td><a href="https://github.com/VikParuchuri/surya">Surya GitHub</a></td>
      <td>0.5.0</td>
    </tr>
  </tbody>
</table>

### Layout

<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Official Website</th>
      <th>Evaluation Version/Model Weights</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>DiT-L</td>
      <td><a href="https://github.com/facebookresearch/DiT">DiT-L</a></td>
      <td><a href="https://huggingface.co/docs/transformers/model_doc/dit">Hugging Face DiT</a></td>
    </tr>
    <tr>
      <td>LayoutMv3</td>
      <td><a href="https://github.com/microsoft/unilm/tree/master/layoutlmv3">LayoutMv3</a></td>
      <td><a href="https://huggingface.co/docs/transformers/model_doc/layoutlmv3">Hugging Face LayoutMv3</a></td>
    </tr>
    <tr>
      <td>DOCX-Chain</td>
      <td><a href="https://github.com/AlibabaResearch/AdvancedLiterateMachinery/tree/main/Applications/DocXChain">DOCX-Chain</a></td>
      <td><a href="https://github.com/AlibabaResearch/AdvancedLiterateMachinery/releases/download/v1.2.0-docX-release/DocXLayout_231012.pth">DocXLayout_231012.pth</a></td>
    </tr>
    <tr>
      <td>DocLayout-YOLO</td>
      <td><a href="https://github.com/opendatalab/DocLayout-YOLO">DocLayout-YOLO</a></td>
      <td><a href="https://huggingface.co/spaces/opendatalab/DocLayout-YOLO">Hugging Face DocLayout-YOLO</a></td>
    </tr>
    <tr>
      <td>SwinDocSegmenter</td>
      <td><a href="https://github.com/ayanban011/SwinDocSegmenter">SwinDocSegmenter</a></td>
      <td><a href="https://drive.google.com/file/d/1DCxG2MCza_z-yB3bLcaVvVR4Jik00Ecq/view?usp=share_link">model weights</a></td>
    </tr>
    <tr>
      <td>GraphKD</td>
      <td><a href="https://github.com/ayanban011/GraphKD">GraphKD</a></td>
      <td><a href="https://drive.google.com/file/d/1oOzy7D6J0yb0Z_ALwpPZMbIZf_AmekvE/view?usp=sharing">model weights</a></td>
    </tr>
  </tbody>
</table>

### Formula
<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Official Website</th>
      <th>Evaluation Version/Model Weights</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GOT_OCR</td>
      <td><a href="https://github.com/Ucas-HaoranWei/GOT-OCR2.0">GOT_OCR</a></td>
      <td><a href="https://huggingface.co/stepfun-ai/GOT-OCR2_0">Hugging Face GOT-OCR2_0</a></td>
    </tr>
    <tr>
      <td>Mathpix</td>
      <td><a href="https://mathpix.com/">Mathpix</a></td>
      <td>———</td>
    </tr>
    <tr>
      <td>Pix2Tex</td>
      <td><a href="https://github.com/lukas-blecher/LaTeX-OCR">Pix2Tex</a></td>
      <td>0.1.2</td>
    </tr>
    <tr>
      <td>UniMERNet-B</td>
      <td><a href="https://github.com/opendatalab/UniMERNet">UniMERNet-B</a></td>
      <td><a href="https://huggingface.co/datasets/wanderkid/UniMER_Dataset">Hugging Face UniMERNet-B</a></td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><a href="https://openai.com/index/hello-gpt-4o/">GPT4o</a></td>
      <td>2024-08-06</td>
    </tr>
    <tr>
      <td>InternVL2-Llama3-76B</td>
      <td><a href="https://github.com/OpenGVLab/InternVL">InternVL2-Llama3-76B</a></td>
      <td><a href="https://huggingface.co/OpenGVLab/InternVL2-Llama3-76B">Huggingface Face InternVL2-Llama3-76B</a></td>
    </tr>
    <tr>
      <td>Qwen2-VL-72B</td>
      <td><a href="https://qwenlm.github.io/zh/blog/qwen2-vl/">Qwen2-VL-72B</a></td>
      <td><a href="https://huggingface.co/Qwen/Qwen2-VL-72B-Instruct">Hugging Face Qwen2-VL-72B-Instruct</a></td>
    </tr>
  </tbody>
</table>

### Table
<table>
  <thead>
    <tr>
      <th>Model Name</th>
      <th>Official Website</th>
      <th>Evaluation Version/Model Weights</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>PaddleOCR</td>
      <td><a href="https://github.com/PaddlePaddle/PaddleOCR">PaddleOCR</a></td>
      <td><a href="https://paddlepaddle.github.io/PaddleOCR/latest/model/index.html">PaddleOCR</a></td>
    </tr>
    <tr>
      <td>RapidTable</td>
      <td><a href="https://github.com/RapidAI/RapidTable">RapidTable</a></td>
      <td><a href="https://www.modelscope.cn/models/RapidAI/RapidTable/files">ModelScope RapidTable</a></td>
    </tr>
    <tr>
      <td>StructEqTable</td>
      <td><a href="https://github.com/Alpha-Innovator/StructEqTable-Deploy/blob/main/README.md">StructEqTable</a></td>
      <td><a href="https://huggingface.co/U4R/StructTable-base">Hugging Face StructEqTable</a></td>
    </tr>
    <tr>
      <td>GOT-OCR</td>
      <td><a href="https://github.com/Ucas-HaoranWei/GOT-OCR2.0">GOT-OCR</a></td>
      <td><a href="https://huggingface.co/stepfun-ai/GOT-OCR2_0">Hugging Face GOT-OCR</a></td>
    </tr>
    <tr>
      <td>Qwen2-VL-7B</td>
      <td><a href="https://github.com/QwenLM/Qwen2-VL">Qwen2-VL-7B</a></td>
      <td><a href="https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct">Hugging Face Qwen2-VL-7B-Instruct</a></td>
    </tr>
    <tr>
      <td>InternVL2-8B</td>
      <td><a href="https://github.com/OpenGVLab/InternVL">InternVL2-8B</a></td>
      <td><a href="https://huggingface.co/OpenGVLab/InternVL2-8B">Hugging Face InternVL2-8B</a></td>
    </tr>
  </tbody>
</table>

## TODO

- [ ] Integration of `match_full` algorithm
- [ ] Optimization of matching post-processing for model-specific output formats
- [ ] Addition of Unicode mapping table for special characters

## Known Issues

- Some models occasionally produce non-standard output formats (e.g., recognizing multi-column text as tables, or formulas as Unicode text), leading to matching failures. This can be optimized through post-processing of model output formats
- Due to varying symbol recognition capabilities across different models, some symbols are recognized inconsistently (e.g., list identifiers). Currently, only Chinese and English text are included in text evaluation. A Unicode mapping table will be added later for optimization

We welcome everyone to use the OmniDocBench dataset and provide valuable feedback and suggestions to help us continuously improve the dataset quality and evaluation tools. For any comments or suggestions, please feel free to open an issue and we will respond promptly. If you have evaluation scheme optimizations, you can submit a PR and we will review and update in a timely manner.

## Acknowledgement

- Thank [Abaka AI](https://abaka.ai) for supporting the dataset annotation.
- [PubTabNet](https://github.com/ibm-aur-nlp/PubTabNet) for TEDS metric calculation
- [latexml](https://github.com/brucemiller/LaTeXML) LaTeX to HTML conversion tool
- [Tester](https://github.com/intsig-textin/markdown_tester) Markdown table to HTML conversion tool

## Copyright Statement

The PDFs are collected from public online channels and community user contributions. Content that is not allowed for distribution has been removed. The dataset is for research purposes only and not for commercial use. If there are any copyright concerns, please contact OpenDataLab@pjlab.org.cn.

## Citation

```bibtex
@misc{ouyang2024omnidocbenchbenchmarkingdiversepdf,
      title={OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations}, 
      author={Linke Ouyang and Yuan Qu and Hongbin Zhou and Jiawei Zhu and Rui Zhang and Qunshu Lin and Bin Wang and Zhiyuan Zhao and Man Jiang and Xiaomeng Zhao and Jin Shi and Fan Wu and Pei Chu and Minghao Liu and Zhenxiang Li and Chao Xu and Bo Zhang and Botian Shi and Zhongying Tu and Conghui He},
      year={2024},
      eprint={2412.07626},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2412.07626}, 
}
```