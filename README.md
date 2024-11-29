# OmniDocBench

English | [简体中文](./README.zh.md)

[[Dataset (🤗Hugging Face)]]() | [[Dataset (OpenDataLab)]]()

**OmniDocBench** is a benchmark for evaluating diverse document parsing in real-world scenarios, featuring the following characteristics:
- **Diverse Document Types**: This benchmark includes 981 PDF pages, covering 9 document types, 4 layout types, and 3 language types. It encompasses a wide range of content, including academic papers, financial reports, newspapers, textbooks, and handwritten notes.
- **Rich Annotation Information**: It contains **localization information** for 15 block-level (such as text paragraphs, headings, tables, etc., totaling over 20k) and 4 span-level (such as text lines, inline formulas, subscripts, etc., totaling over 80k) document elements. Each element's region includes **recognition results** (text annotations, LaTeX annotations for formulas, and both LaTeX and HTML annotations for tables). OmniDocBench also provides annotations for the **reading order** of document components. Additionally, it includes various attribute tags at the page and block levels, with annotations for 5 **page attribute tags**, 3 **text attribute tags**, and 6 **table attribute tags**.
- **High Annotation Quality**: The data quality is high, achieved through manual screening, intelligent annotation, manual annotation, and comprehensive expert and large model quality checks.
- **Supporting Evaluation Code**: It includes end-to-end and single-module evaluation code to ensure fairness and accuracy in assessments.

**OmniDocBench** is a benchmark designed for Document Parsing, featuring rich annotations for evaluation across several dimensions:
- End-to-end evaluation: includes both end2end and md2md evaluation methods
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

## Download

xxx

## Benchmark Introduction

This benchmark includes 981 PDF pages, covering 9 document types, 4 layout types, and 3 language types. OmniDocBench features rich annotations, containing 15 block-level annotations (text paragraphs, headings, tables, etc.) and 4 span-level annotations (text lines, inline formulas, subscripts, etc.). All text-related annotation boxes include text recognition annotations, formulas contain LaTeX annotations, and tables include both LaTeX and HTML annotations. OmniDocBench also provides reading order annotations for document components. Additionally, it includes various attribute tags at the page and block levels, with annotations for 5 page attribute tags, 3 text attribute tags, and 6 table attribute tags.

![](https://github.com/user-attachments/assets/f3e53ba8-bb97-4ca9-b2e7-e2530865aaa9)

<details>
  <summary>Dataset Format</summary>

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
  <summary>Evaluation Categories</summary>

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
  <summary>Attribute Labels</summary>

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
```

</details>


## Evaluation

OmniDocBench has developed an evaluation methodology based on document component segmentation and matching. It provides corresponding metric calculations for four major modules: text, tables, formulas, and reading order. In addition to overall accuracy results, the evaluation also provides fine-grained evaluation results by page and attributes, precisely identifying pain points in model document parsing.

![](https://github.com/user-attachments/assets/95c88aaa-75dc-432e-891e-17a7d73e024a)

### Environment Setup and Running

To set up the environment, simply run the following commands in the project directory:

```bash
conda create --name omnidocbench python=3.8 --file requirements.txt
conda activate omnidocbench
```

All evaluation inputs are configured through config files. We provide templates for each task under the [configs](./configs) directory, and we will explain the contents of the config files in detail in the following sections.

After configuring the config file, simply pass it as a parameter and run the following code to perform the evaluation:

```bash
python pdf_validation.py --config <config_path>
```

### End-to-End Evaluation

End-to-end evaluation assesses the model's accuracy in parsing PDF page content. The evaluation uses the model's Markdown output of the entire PDF page parsing results as the prediction.

<table style="width: 92%; border-collapse: collapse; margin: 0 auto;">
  <caption>Comprehensive evaluation of document parsing algorithms on OmniDocBench: performance metrics for text, formula, table, and reading order extraction, with overall scores derived from ground truth comparisons.</caption>
  <thead>
    <tr>
      <th rowspan="2">Method Type</th>
      <th rowspan="2">Methods</th>
      <th colspan="2">Text<sup>Edit</sup>↓</th>
      <th colspan="2">Formula<sup>Edit</sup>↓</th>
      <th colspan="2">Formula<sup>CDM</sup>↑</th>
      <th colspan="2">Table<sup>TEDS</sup>↑</th>
      <th colspan="2">Table<sup>Edit</sup>↓</th>
      <th colspan="2">Read Order<sup>Edit</sup>↓</th>
      <th colspan="2">Overall<sup>Edit</sup>↓</th>
    </tr>
    <tr>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
      <th>EN</th>
      <th>ZH</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="3">Pipeline Tools</td>
      <td>MinerU</td>
      <td><strong>0.058</strong></td>
      <td><strong>0.211</strong></td>
      <td><strong>0.278</strong></td>
      <td>0.577</td>
      <td>66.9</td>
      <td>49.5</td>
      <td><strong>79.4</strong></td>
      <td>62.7</td>
      <td><strong>0.305</strong></td>
      <td><u>0.461</u></td>
      <td><strong>0.079</strong></td>
      <td>0.288</td>
      <td><strong>0.180</strong></td>
      <td><u>0.384</u></td>
    </tr>
    <tr>
      <td>Marker</td>
      <td>0.141</td>
      <td>0.303</td>
      <td>0.667</td>
      <td>0.868</td>
      <td>18.4</td>
      <td>12.7</td>
      <td>54.0</td>
      <td>45.8</td>
      <td>0.718</td>
      <td>0.763</td>
      <td>0.138</td>
      <td>0.306</td>
      <td>0.416</td>
      <td>0.560</td>
    </tr>
    <tr>
      <td>Mathpix</td>
      <td><u>0.101</u></td>
      <td>0.358</td>
      <td><u>0.306</u></td>
      <td><strong>0.454</strong></td>
      <td>71.4</td>
      <td><strong>72.7</strong></td>
      <td><u>77.9</u></td>
      <td><strong>68.2</strong></td>
      <td><u>0.322</u></td>
      <td><strong>0.416</strong></td>
      <td><u>0.105</u></td>
      <td>0.275</td>
      <td><u>0.209</u></td>
      <td><strong>0.376</strong></td>
    </tr>
    <tr>
      <td rowspan="2">Expert VLMs</td>
      <td>GOT-OCR</td>
      <td>0.187</td>
      <td>0.315</td>
      <td>0.360</td>
      <td><u>0.528</u></td>
      <td><strong>81.8</strong></td>
      <td>51.4</td>
      <td>53.5</td>
      <td>48.0</td>
      <td>0.521</td>
      <td>0.594</td>
      <td>0.141</td>
      <td>0.28</td>
      <td>0.302</td>
      <td>0.429</td>
    </tr>
    <tr>
      <td>Nougat</td>
      <td>0.365</td>
      <td>0.998</td>
      <td>0.488</td>
      <td>0.941</td>
      <td>17.4</td>
      <td>16.9</td>
      <td>40.3</td>
      <td>0.0</td>
      <td>0.622</td>
      <td>1.000</td>
      <td>0.382</td>
      <td>0.954</td>
      <td>0.464</td>
      <td>0.973</td>
    </tr>
    <tr>
      <td rowspan="3">General VLMs</td>
      <td>GPT4o</td>
      <td>0.144</td>
      <td>0.409</td>
      <td>0.425</td>
      <td>0.606</td>
      <td><u>76.4</u></td>
      <td>48.2</td>
      <td>72.75</td>
      <td>63.7</td>
      <td>0.363</td>
      <td>0.474</td>
      <td>0.128</td>
      <td>0.251</td>
      <td>0.265</td>
      <td>0.435</td>
    </tr>
    <tr>
      <td>Qwen2-VL</td>
      <td>0.252</td>
      <td><u>0.251</u></td>
      <td>0.468</td>
      <td>0.572</td>
      <td>54.9</td>
      <td><u>60.9</u></td>
      <td>59.9</td>
      <td><u>66.8</u></td>
      <td>0.591</td>
      <td>0.587</td>
      <td>0.255</td>
      <td><strong>0.223</strong></td>
      <td>0.392</td>
      <td>0.408</td>
    </tr>
    <tr>
      <td>InternVL2</td>
      <td>0.353</td>
      <td>0.290</td>
      <td>0.543</td>
      <td>0.701</td>
      <td>69.8</td>
      <td>49.6</td>
      <td>63.8</td>
      <td>61.1</td>
      <td>0.616</td>
      <td>0.638</td>
      <td>0.317</td>
      <td><u>0.228</u></td>
      <td>0.457</td>
      <td>0.464</td>
    </tr>
  </tbody>
</table>

$^*$More detailed attribute-level evaluation results are shown in the paper.

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
  <summary>Field explanations for [end2end.yaml](./configs/end2end.yaml)</summary>

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

In addition to the supported metrics, the system also supports exporting formats required for [CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm) evaluation. Simply configure the CDM field in the metrics section to format the output for CDM input and store it in [result](./result).

For end-to-end evaluation, the config allows selecting different matching methods. There are three matching approaches:
- `no_split`: Does not split or match text blocks, but rather combines them into a single markdown for calculation. This method will not output attribute-level results or reading order results.
- `simple_match`: Performs only paragraph segmentation using double line breaks, then directly matches one-to-one with GT without any truncation or merging.
- `quick_match`: Builds on paragraph segmentation by adding truncation and merging operations to reduce the impact of paragraph segmentation differences on final results, using *Adjacency Search Match* for truncation and merging.

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
  <summary>Field explanations for [md2md.yaml](./configs/md2md.yaml)</summary>

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
      <td><u>86.6</u></td>
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
      <td><u>60.2</u></td>
      <td><u>60.84</u></td>
      <td><b>0.238</b></td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><b>86.8</b></td>
      <td><b>65.5</b></td>
      <td>45.17</td>
      <td><u>0.282</u></td>
    </tr>
    <tr>
      <td>InternVL2</td>
      <td>67.4</td>
      <td>54.5</td>
      <td>47.63</td>
      <td>0.308</td>
    </tr>
    <tr>
      <td>Qwen2-VL</td>
      <td>83.8</td>
      <td>55.4</td>
      <td>53.71</td>
      <td>0.285</td>
    </tr>
  </tbody>
</table>
<p>Component-level formula recognition evaluation on OmniDocBench formula subset.</p>


Formula recognition evaluation can be configured according to [formula_recognition](./configs/formula_recognition.yaml).

<details>
  <summary>Field explanations for [formula_recognition.yaml](./configs/formula_recognition.yaml)</summary>

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

### OCR Text Recognition Evaluation

OmniDocBench contains bounding box information and corresponding text recognition annotations for all text in each PDF page, making it suitable as a benchmark for OCR evaluation. The text annotations include both block-level and span-level annotations, both of which can be used for evaluation. This repo currently provides an example of block-level evaluation, which evaluates OCR at the text paragraph level.

<table style="width: 90%; font-size: small; margin: 0 auto; border-collapse: collapse;">
    <caption style="caption-side: bottom; padding-top: 4px;">Component-level evaluation on OmniDocBench OCR subset: results grouped by text attributes using the edit distance metric.</caption>
    <thead>
        <tr>
            <th rowspan="2" style="border-bottom: 1px solid #000;">Model Type</th>
            <th rowspan="2" style="border-bottom: 1px solid #000;">Model</th>
            <th colspan="3" style="border-bottom: 1px solid #000;">Language</th>
            <th colspan="3" style="border-bottom: 1px solid #000;">Text background</th>
            <th colspan="4" style="border-bottom: 1px solid #000;">Text Rotate</th>
        </tr>
        <tr>
            <th style="border-bottom: 1px solid #000;">EN</th>
            <th style="border-bottom: 1px solid #000;">ZH</th>
            <th style="border-bottom: 1px solid #000;">Mixed</th>
            <th style="border-bottom: 1px solid #000;">White</th>
            <th style="border-bottom: 1px solid #000;">Single</th>
            <th style="border-bottom: 1px solid #000;">Multi</th>
            <th style="border-bottom: 1px solid #000;">Normal</th>
            <th style="border-bottom: 1px solid #000;">Rotate90</th>
            <th style="border-bottom: 1px solid #000;">Rotate270</th>
            <th style="border-bottom: 1px solid #000;">Horizontal</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5">Expert Vision Models</td>
            <td>PaddleOCR</td>
            <td>0.071</td>
            <td><strong>0.055</strong></td>
            <td><strong>0.118</strong></td>
            <td><strong>0.060</strong></td>
            <td><strong>0.038</strong></td>
            <td><strong>0.0848</strong></td>
            <td><strong>0.060</strong></td>
            <td><strong>0.015</strong></td>
            <td style="text-decoration: underline;">0.285</td>
            <td><strong>0.021</strong></td>
        </tr>
        <tr>
            <td>Tesseract OCR</td>
            <td>0.179</td>
            <td>0.553</td>
            <td>0.553</td>
            <td>0.453</td>
            <td>0.463</td>
            <td>0.394</td>
            <td>0.448</td>
            <td>0.369</td>
            <td>0.979</td>
            <td>0.982</td>
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
            <td>GOT-OCR</td>
            <td>0.041</td>
            <td style="text-decoration: underline;">0.112</td>
            <td>0.135</td>
            <td style="text-decoration: underline;">0.092</td>
            <td style="text-decoration: underline;">0.052</td>
            <td>0.155</td>
            <td style="text-decoration: underline;">0.091</td>
            <td>0.562</td>
            <td>0.966</td>
            <td>0.097</td>
        </tr>
        <tr>
            <td>Mathpix</td>
            <td style="text-decoration: underline;">0.033</td>
            <td>0.240</td>
            <td>0.261</td>
            <td>0.185</td>
            <td>0.121</td>
            <td>0.166</td>
            <td>0.180</td>
            <td style="text-decoration: underline;">0.038</td>
            <td><strong>0.185</strong></td>
            <td>0.638</td>
        </tr>
        <tr>
            <td rowspan="3">Vision Language Models</td>
            <td>Qwen2-VL</td>
            <td>0.072</td>
            <td>0.274</td>
            <td>0.286</td>
            <td>0.234</td>
            <td>0.155</td>
            <td style="text-decoration: underline;">0.148</td>
            <td>0.223</td>
            <td>0.273</td>
            <td>0.721</td>
            <td style="text-decoration: underline;">0.067</td>
        </tr>
        <tr>
            <td>InternVL2</td>
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
            <td><strong>0.020</strong></td>
            <td>0.224</td>
            <td style="text-decoration: underline;">0.125</td>
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


OCR text recognition evaluation can be configured according to [ocr](./configs/ocr.yaml). 

<details>
  <summary>The field explanation of [ocr.yaml](./configs/ocr.yaml)</summary>

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

<table style="width:100%; border-collapse: collapse;">
  <thead>
    <tr>
      <th rowspan="2">Model Type</th>
      <th rowspan="2">Model</th>
      <th colspan="3">Language</th>
      <th colspan="4">Table Frame Type</th>
      <th colspan="4">Special Situation</th>
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
      <td rowspan="2"><strong>OCR-based Models</strong></td>
      <td>PaddleOCR</td>
      <td><u>77.0</u></td>
      <td>73.0</td>
      <td>80.9</td>
      <td>69.0</td>
      <td><u>75.0</u></td>
      <td><u>80.8</u></td>
      <td>76.2</td>
      <td><u>73.3/75.0</u></td>
      <td><u>72.7/74.7</u></td>
      <td><u>72.7/75.1</u></td>
      <td>23.3/75.4</td>
    </tr>
    <tr>
      <td>RapidTable</td>
      <td><strong>80.1</strong></td>
      <td><strong>82.8</strong></td>
      <td><strong>90.9</strong></td>
      <td><strong>83.5</strong></td>
      <td><strong>80.3</strong></td>
      <td><strong>81.9</strong></td>
      <td><u>79.5</u></td>
      <td><strong>78.8/84.6</strong></td>
      <td><strong>77.9/83.4</strong></td>
      <td><strong>77.4/84.6</strong></td>
      <td><u>25.2/83.5</u></td>
    </tr>
    <tr>
      <td rowspan="2"><strong>Expert VLMs</strong></td>
      <td>StructEqTable</td>
      <td>72.2</td>
      <td>72.2</td>
      <td>82.5</td>
      <td>68.8</td>
      <td>64.6</td>
      <td>79.5</td>
      <td><strong>83.7</strong></td>
      <td>67.1/76.0</td>
      <td>69.9/73.2</td>
      <td>66.7/75.2</td>
      <td><strong>44.1/73.1</strong></td>
    </tr>
    <tr>
      <td>GOT-OCR</td>
      <td>72.3</td>
      <td><u>76.8</u></td>
      <td><u>85.9</u></td>
      <td><u>74.4</u></td>
      <td>73.9</td>
      <td>78.5</td>
      <td>76.6</td>
      <td>69.7/79.7</td>
      <td>66.2/78.0</td>
      <td>70.9/78.1</td>
      <td>8.5/77.2</td>
    </tr>
    <tr>
      <td rowspan="2"><strong>General VLMs</strong></td>
      <td>Qwen2-VL-7B</td>
      <td>70.4</td>
      <td>67.9</td>
      <td>82.6</td>
      <td>68.3</td>
      <td>62.2</td>
      <td>72.0</td>
      <td>78.4</td>
      <td>58.8/75.5</td>
      <td>62.8/70.5</td>
      <td>71.1/68.2</td>
      <td>20.0/70.0</td>
    </tr>
    <tr>
      <td>InternVL2-8B</td>
      <td>70.9</td>
      <td>69.9</td>
      <td>77.9</td>
      <td>68.5</td>
      <td>68.1</td>
      <td>73.5</td>
      <td>75.5</td>
      <td>58.6/77.8</td>
      <td>62.2/72.3</td>
      <td>67.8/71.7</td>
      <td>20.4/71.4</td>
    </tr>
  </tbody>
</table>
<p>Component-level Table Recognition evaluation on OmniDocBench table subset. <i>(+/-)</i> means <i>with/without</i> special situation.</p>


Table recognition evaluation can be configured according to [table_recognition](./configs/table_recognition.yaml). 

**For tables predicted to be in LaTeX format, the [latexml](https://math.nist.gov/~BMiller/LaTeXML/) tool will be used to convert LaTeX to HTML before evaluation. The evaluation code will automatically perform format conversion, and users need to preinstall [latexml](https://math.nist.gov/~BMiller/LaTeXML/)**

<details>
  <summary>[table_recognition.yaml](./configs/table_recognition.yaml)的字段解释</summary>

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

<table style="width: 90%; margin: auto; border-collapse: collapse;">
  <caption>Component-level layout detection evaluation on OmniDocBench layout subset: mAP results by PDF page type.</caption>
  <thead>
    <tr>
      <th style="border-bottom: 2px solid black;">Model</th>
      <th style="border-bottom: 2px solid black;">Book</th>
      <th style="border-bottom: 2px solid black;">Slides</th>
      <th style="border-bottom: 2px solid black;">Research Report</th>
      <th style="border-bottom: 2px solid black;">Textbook</th>
      <th style="border-bottom: 2px solid black;">Exam Paper</th>
      <th style="border-bottom: 2px solid black;">Magazine</th>
      <th style="border-bottom: 2px solid black;">Academic Literature</th>
      <th style="border-bottom: 2px solid black;">Notes</th>
      <th style="border-bottom: 2px solid black;">Newspaper</th>
      <th style="border-bottom: 2px solid black;">Average mAP</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border-top: 1px solid black;">DiT-L</td>
      <td style="border-top: 1px solid black; text-decoration: underline;">43.44</td>
      <td style="border-top: 1px solid black; text-decoration: underline;">13.72</td>
      <td style="border-top: 1px solid black; text-decoration: underline;">45.85</td>
      <td style="border-top: 1px solid black;">15.45</td>
      <td style="border-top: 1px solid black;">3.40</td>
      <td style="border-top: 1px solid black; text-decoration: underline;">29.23</td>
      <td style="border-top: 1px solid black; text-decoration: underline;">66.13</td>
      <td style="border-top: 1px solid black;">0.21</td>
      <td style="border-top: 1px solid black;">23.65</td>
      <td style="border-top: 1px solid black;">26.90</td>
    </tr>
    <tr>
      <td>LayoutLMv3</td>
      <td>42.12</td>
      <td>13.63</td>
      <td>43.22</td>
      <td style="text-decoration: underline;">21.00</td>
      <td>5.48</td>
      <td>31.81</td>
      <td>64.66</td>
      <td>0.80</td>
      <td style="text-decoration: underline;">30.84</td>
      <td style="text-decoration: underline;">28.84</td>
    </tr>
    <tr>
      <td>DOCX-Chain</td>
      <td>30.86</td>
      <td>11.71</td>
      <td>39.62</td>
      <td style="text-decoration: underline;">19.23</td>
      <td style="text-decoration: underline;">10.67</td>
      <td>23.00</td>
      <td>41.60</td>
      <td style="text-decoration: underline;">1.80</td>
      <td>16.96</td>
      <td>21.27</td>
    </tr>
    <tr>
      <td style="font-weight: bold;">DocLayout-YOLO</td>
      <td style="font-weight: bold;">43.71</td>
      <td style="font-weight: bold;">48.71</td>
      <td style="font-weight: bold;">72.83</td>
      <td style="font-weight: bold;">42.67</td>
      <td style="font-weight: bold;">35.40</td>
      <td style="font-weight: bold;">51.44</td>
      <td style="font-weight: bold;">66.84</td>
      <td style="font-weight: bold;">9.54</td>
      <td style="font-weight: bold;">57.54</td>
      <td style="font-weight: bold;">48.71</td>
    </tr>
  </tbody>
</table>


Layout detection config file reference [layout_detection](./configs/layout_detection.yaml), data format reference [detection_prediction](./demo_data/detection/detection_prediction.json).

<details>
  <summary>The field explanation of [layout_detection.yaml](./configs/layout_detection.yaml)</summary>

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
      <td><u>86.6</u></td>
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
      <td><u>60.2</u></td>
      <td><u>60.84</u></td>
      <td><b>0.238</b></td>
    </tr>
    <tr>
      <td>GPT4o</td>
      <td><b>86.8</b></td>
      <td><b>65.5</b></td>
      <td>45.17</td>
      <td><u>0.282</u></td>
    </tr>
    <tr>
      <td>InternVL2</td>
      <td>67.4</td>
      <td>54.5</td>
      <td>47.63</td>
      <td>0.308</td>
    </tr>
    <tr>
      <td>Qwen2-VL</td>
      <td>83.8</td>
      <td>55.4</td>
      <td>53.71</td>
      <td>0.285</td>
    </tr>
  </tbody>
</table>
<p>Component-level formula recognition evaluation on OmniDocBench formula subset.</p>


The format for formula detection is essentially the same as layout detection. Formulas include both inline and display formulas. In this section, we provide a config example that can evaluate detection results for both display formulas and inline formulas simultaneously. Formula detection can be configured according to [formula_detection](./configs/formula_detection.yaml).

<details>
  <summary>The field explanation of [formula_detection.yaml](./configs/formula_detection.yaml)</summary>

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
- The [model_infer](./tools/model_infer) folder provides some model inference scripts for reference, including:
  - [mathpix_img2md.py](./tools/model_infer/mathpix_img2md.py) for calling [mathpix](https://mathpix.com/) API to convert images to Markdown format;
  - [internvl2_test_img2md.py](./tools/model_infer/internvl2_test_img2md.py) for using [InternVL2](https://github.com/OpenGVLab/InternVL) model to convert images to Markdown format, please use after configuring the InternVL2 model environment;
  - [GOT_img2md.py](./tools/model_infer/GOT_img2md.py) for using [GOT-OCR](https://github.com/Ucas-HaoranWei/GOT-OCR2.0) model to convert images to Markdown format, please use after configuring the GOT-OCR model environment;

## LICENSE

xxx

## Acknowledgement

- [PubTabNet](https://github.com/ibm-aur-nlp/PubTabNet) for TEDS metric calculation
- [latexml](https://github.com/brucemiller/LaTeXML) LaTeX to HTML conversion tool
- [Tester](https://github.com/intsig-textin/markdown_tester) Markdown table to HTML conversion tool
- Thank [Abaka AI](https://abaka.ai) for supporting the dataset annotation.
![](https://github.com/user-attachments/assets/4dc644cd-0edd-46de-a1c0-620067e1ab50)

## Citation

xxx