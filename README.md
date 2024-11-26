# OmniDocBench

![](https://github.com/user-attachments/assets/f3e53ba8-bb97-4ca9-b2e7-e2530865aaa9)

![](https://github.com/user-attachments/assets/ea389904-c130-410e-b05f-676882cc973c)

OmniDocBench is a benchmark designed for Document Parsing, featuring rich annotations for evaluation across several dimensions:
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

## Download

xxx

## How to use

All evaluation inputs are organized through config files. We provide templates for each task in the [configs](./configs) directory.

Once the config file is set up, simply pass it as a parameter and run the following code:

```bash
python pdf_validation.py --config <config_path>
```

## End-to-End Evaluation

End-to-end evaluation assesses the accuracy of a model in Document Parsing. The model's output, which is the parsed result of the entire PDF page in Markdown, is used as the prediction.

There are two methods for end-to-end evaluation:
- `end2end`: This method uses OmniDocBench's JSON files as Ground Truth. Refer to the config file: [end2end](./configs/end2end.yaml).
- `md2md`: This method uses OmniDocBench's markdown format as Ground Truth. Refer to the config file: [md2md](./configs/md2md.yaml).

We recommend using the `end2end` method because it preserves the sample's category and attribute information, allowing for operations like ignoring specific categories and outputting results by attribute.

In addition, the config allows you to choose different matching methods for end-to-end evaluation. There are three matching methods:

- `no_split`: Does not split and match text blocks but merges them into a single markdown for calculation. This method does not output results by attribute or reading order.
- `simple_match`: Does not perform any truncation or merging operations. It only splits paragraphs with double line breaks and matches them one-to-one with the ground truth.
- `quick_match`: It splits paragraphs with double line breaks, then using Adjacency Search Match for truncation and merging. It can reduce the impact of paragraph segmentation differences on the final result.

We recommend using `quick_match` for better matching results. However, if the model's paragraph segmentation is accurate, you can use `simple_match` for faster evaluation. The matching method is configured in the `match_method` field under the `dataset` section in the config.

You can use the `filter` field to filter the dataset. For example, setting the `filter` field under `dataset` to `data_source: exam_paper` will only evaluate on pages of the `exam_paper` type. For more page attributes, please refer to the "Dataset" section.

## Formula Recognition Evaluation

For configuring formula recognition evaluation, refer to [formula_omidocbench](./configs/formula_omidocbench.yaml). The input format remains consistent with OmniDocBench. The model's predictions are stored in a custom field under the corresponding formula sample. Specify the field storing prediction information using the `data_key` under the `prediction` section of `dataset`.

In addition to the supported metrics, you can export the format required for [CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm) evaluation. Simply configure the CDM field in the metrics to organize the output into the CDM input format and store it in the [result](./result).

## Text OCR Evaluation

For configuring text OCR evaluation, refer to [ocr_omidocbench](./configs/ocr_omidocbench.yaml). The input format remains consistent with OmniDocBench. The model's predictions are stored in a custom field under the corresponding text sample. Specify the field storing prediction information using the `data_key` under the `prediction` section of `dataset`.

## Table Recognition Evaluation

[Content to be provided]

## Layout Detection

For configuring layout detection, refer to [layout_detection](./configs/layout_detection.yaml). The input format supports the same format as OmniDocBench (see [omni_det](./check_data/layout_omni/pred.json)).

A simplified format is also supported, refer to config [layout_detection_simple](./configs/layout_detection_simple.yaml) and data format [simple_det](./check_data/layout_simple/predictions.json).

You can use the `filter` field to filter the dataset. For example, setting the `filter` field under `dataset` to `data_source: exam_paper` will only evaluate on pages of the `exam_paper` type. For more page attributes, please refer to the "Dataset" section.

## Formula Detection

For configuring formula detection, refer to [formula_detection](./configs/formula_detection.yaml). The input format is the same as for layout detection.

## Dataset

The OmniDocBench is formatted in JSON. The structure and explanation of each field are as follows:

```json
[{
    "layout_dets": [    // List of page elements
        {
            "category_type": "text_block",  // Category name
            "poly": [
                136.0, // Position information: x, y coordinates for top-left, top-right, bottom-right, bottom-left
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
            "anno_id": 0,           // Unique annotation ID for each layout box
            "text": "xxx",          // Optional field, OCR results will be written here
            "latex": "$xxx",        // Optional field, LaTeX for formulas and tables will be written here
            "html": "xxx",          // Optional field, HTML for tables will be written here
            "attribute": {"xxx": "xxx"}, // Classification attributes of the layout, detailed later
            "line_with_spans": [   // Span level annotation boxes
                {
                    "category_type": "text_span",
                    "poly": [...],
                    "ignore": false,
                    "text": "xxx",   
                    "latex": "$xxx"
                },
                ...
            ],
            "merge_list": [    // Present only in annotation boxes with merge relations; includes logic for single line break separation for lists, etc.
                {
                    "category_type": "text_block", 
                    "poly": [...],
                    ...   // Same fields as block-level annotations
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
        "image_path": "xxx",  // Annotated page file name
        "page_attribute": {"xxx": "xxx"} // Page attribute tags
    },
    "extra": {
        "relation": [ // Annotations with relationships
            {  
                "source_anno_id": 1,
                "target_anno_id": 2, 
                "relation": "parent_son"  // Relationship tags between figures/tables and their captions/footnotes
            },
            {  
                "source_anno_id": 5,
                "target_anno_id": 6,
                "relation_type": "truncated"  // Tags for paragraphs truncated due to layout; evaluated as a whole after merging
            }
        ]
    }
},
...
]
```

The validation set categories include:

```plaintext
# Block-level annotation boxes
'title'               # Title
'text_block'          # Paragraph-level plain text
'figure'              # Image
'figure_caption'      # Image caption or title
'figure_footnote'     # Image footnote
'table'               # Table body
'table_caption'       # Table caption or title
'table_footnote'      # Table footnote
'equation_isolated'   # Display equation
'equation_caption'    # Equation number
'header'              # Header
'footer'              # Footer
'page_number'         # Page number
'page_footnote'       # Page footnote
'abandon'             # Other discardable items (e.g., irrelevant information in the middle of the page)
'code_txt'            # Code block
'code_txt_caption'    # Code block description
'reference'           # References

# Span-level annotation boxes
'text_span'           # Span-level plain text
'equation_ignore'     # Equations to be ignored
'equation_inline'     # Inline equations
'footnote_mark'       # Superscript or subscript in the text
```

Page attributes include:

```plaintext
'data_source': # PDF type classification
    academic_literature  # Academic literature
    PPT2PDF  # Slides converted to PDF
    book  # Black and white books and textbooks
    colorful_textbook  # Colorful illustrated textbooks
    exam_paper  # Exam papers
    note  # Handwritten notes
    magazine  # Magazines
    research_report  # Research and financial reports
    newspaper  # Newspapers

'language': # Language
    en  # English
    simplified_chinese  # Simplified Chinese
    en_ch_mixed  # Mixed English and Chinese

'layout': # Page layout type
    single_column  # Single column
    double_column  # Double column
    three_column  # Three column
    1andmore_column  # Mixed layout, common in literature
    other_layout  # Other

'watermark': # Presence of watermark
    true  
    false

'fuzzy_scan': # Fuzzy scan
    true  
    false

'colorful_background': # Presence of colorful background, involving more than two colors in the background of the content to be recognized
    true  
    false
```

Annotation box-level attributes - Table-related attributes:

```plaintext
'table_layout': # Table orientation
    vertical  # Vertical table
    horizontal  # Horizontal table

'with_span': # Merged cells
    False
    True

'line': # Table frames
    full_line  # Full frame
    less_line  # Omission-line Frame
    fewer_line  # Three-line Frame
    wireless_line  # No Frame

'language': # Table language
    table_en  # English
    table_simplified_chinese  # Simplified Chinese
    table_en_ch_mixed  # Mixed English and Chinese

'include_equation': # Presence of equations in the table
    False
    True

'include_background': # Presence of background color in the table
    False
    True

'table_vertical': # Table rotated 90 or 270 degrees
    False
    True
```

Annotation box-level attributes - Text paragraph-related attributes:

```plaintext
'text_language': # Language within text paragraph
    text_en  # English
    text_simplified_chinese  # Simplified Chinese
    text_en_ch_mixed  # Mixed English and Chinese

'text_background': # Text background color
    white  # Default, white background
    single_colored  # Single background color other than white
    multi_colored  # Mixed background colors

'text_rotate': # Text rotation within paragraph
    normal  # Default, horizontal text, no rotation
    rotate90  # Rotated 90 degrees clockwise
    rotate180  # Rotated 180 degrees clockwise
    rotate270  # Rotated 270 degrees clockwise
    horizontal  # Text is normal, layout is vertical
```

Annotation box-level attributes - Formula-related attributes:

```plaintext
'formula_type': # Formula type
    print  # Printed
    handwriting  # Handwritten
```