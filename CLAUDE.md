# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

OmniDocBench is a comprehensive benchmark for evaluating document parsing in real-world scenarios. It supports evaluation of multiple document parsing tasks including end-to-end document parsing, layout detection, table recognition, formula recognition, and text OCR across 981 PDF pages covering 9 document types, 4 layout types, and 3 language types.

## Environment Setup and Development Commands

### Environment Setup
```bash
conda create -n omnidocbench python=3.10
conda activate omnidocbench
pip install -r requirements.txt
```

### Running Evaluations
The main evaluation entry point is through `pdf_validation.py`:
```bash
python pdf_validation.py --config <config_path>
```

Common evaluation configurations are in the `configs/` directory:
- `end2end.yaml` - End-to-end document parsing evaluation
- `formula_detection.yaml` - Formula detection evaluation
- `formula_recognition.yaml` - Formula recognition evaluation
- `layout_detection.yaml` - Layout detection evaluation
- `table_recognition.yaml` - Table recognition evaluation
- `ocr.yaml` - Text OCR evaluation
- `md2md.yaml` - Markdown-to-Markdown evaluation

### Show Results
After evaluation, view results using:
```bash
python -m metrics.show_result
```

Generate result tables using the Jupyter notebook:
```bash
jupyter notebook tools/generate_result_tables.ipynb
```

### Data Conversion Tools
Convert JSON annotations to Markdown format:
```bash
python tools/json2md.py
```

## Code Architecture

### Core Components

**Registry System** (`registry/`): 
- Centralized registry for datasets, metrics, and evaluation tasks
- `EVAL_TASK_REGISTRY`, `METRIC_REGISTRY`, `DATASET_REGISTRY` provide plugin-like architecture

**Dataset Layer** (`dataset/`):
- `End2EndDataset` - End-to-end evaluation datasets
- `DetectionDataset` - Object detection datasets for layout/formula detection
- `RecognitionDataset` - Recognition datasets for formulas, tables, OCR
- `Md2MdDataset` - Markdown comparison datasets

**Evaluation Tasks** (`task/`):
- `end2end_run_eval.py` - Main end-to-end evaluation logic
- `detection_eval.py` - Layout and formula detection evaluation
- `recognition_eval.py` - Text, formula, and table recognition evaluation

**Metrics** (`metrics/`):
- `cal_metric.py` - Core metric calculations (Edit Distance, BLEU, METEOR, TEDS, CDM)
- `table_metric.py` - TEDS (Table Edit Distance Score) implementation
- `show_result.py` - Result display and aggregation

**Matching and Preprocessing** (`utils/`):
- `match.py` - Core matching algorithms for ground truth vs predictions
- `match_quick.py` - Fast matching implementation
- `match_full.py` - Comprehensive matching with all features
- `data_preprocess.py` - Text normalization and preprocessing utilities

### Evaluation Flow

1. **Configuration**: Load evaluation config (YAML) specifying dataset paths, metrics, and match methods
2. **Dataset Loading**: Registry system loads appropriate dataset class based on config
3. **Matching**: Match prediction elements to ground truth using geometric and content-based matching
4. **Metric Calculation**: Apply registered metrics (Edit Distance, TEDS, BLEU, etc.) to matched pairs
5. **Result Aggregation**: Generate overall, grouped, and per-page results
6. **Output**: Save results to `result/` directory in JSON format

### Match Methods
- `quick_match` - Fast geometric-based matching (default)
- `simple_match` - Basic IoU-based matching
- `full_match` - Comprehensive matching with all features

### Supported Metrics
- **Edit Distance** - Normalized Levenshtein distance for text comparison
- **TEDS** - Table Edit Distance Score for table structure evaluation
- **CDM** - Formula semantic similarity metric
- **BLEU/METEOR** - Text similarity metrics
- **COCODet** - Object detection metrics (mAP, mAR)

## File Structure Notes

- `demo_data/` - Sample evaluation data and model predictions
- `tools/model_infer/` - Model inference scripts for various document parsing models
- `configs/` - YAML configuration files for different evaluation tasks
- `result/` - Generated evaluation results (created after running evaluations)

## Data Format

Model predictions should be in Markdown format with filenames matching the input images but with `.md` extension. Ground truth data is in JSON format with rich annotations including bounding boxes, text content, reading order, and various attribute labels.

Optional LaTeXML installation required for LaTeX table format evaluation:
```bash
# Install separately if needed for LaTeX table evaluation
# See https://math.nist.gov/~BMiller/LaTeXML/
```