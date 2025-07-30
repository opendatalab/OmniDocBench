# OCR Postprocessing with Azure OpenAI GPT

This pipeline postprocesses OCR markdown results using Azure OpenAI GPT to fix common OCR errors while preserving document structure and meaning.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_azure_openai.txt
```

### 2. Configure Azure OpenAI

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Get Azure OpenAI Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Create or navigate to your Azure OpenAI resource
3. Go to "Keys and Endpoint" to get your API key and endpoint
4. Go to "Model deployments" to see your deployment names

## Usage

### Basic Usage

Process Microsoft OCR results with default settings:

```bash
python tools/postprocess_ocr.py
```

### Advanced Usage

```bash
# Specify custom input/output directories
python tools/postprocess_ocr.py \
    --input-dir demo_data/microsoft_ocr_results_markdownonly \
    --output-dir demo_data/microsoft_ocr_results_gpt_corrected

# Use different deployment
python tools/postprocess_ocr.py --deployment gpt-4

# Override endpoint and API key
python tools/postprocess_ocr.py \
    --endpoint https://your-resource.openai.azure.com \
    --api-key your-api-key-here

# Dry run to check configuration
python tools/postprocess_ocr.py --dry-run
```

### Direct Module Usage

```bash
cd tools/model_infer
python azure_openai_postprocess.py
```

## What Gets Fixed

The GPT postprocessor fixes these common OCR errors:

1. **Spacing issues in numbers**: `"1 0"` → `"10"`, `"4 0"` → `"40"`
2. **Mathematical notation**: `"$1 0 m^{2}$"` → `"$10m^{2}$"`
3. **Mixed language characters**: Removes random foreign script
4. **Roman numeral confusion**: `"IIⅢ"` → `"III"`
5. **Symbol misinterpretation**: Fixes bullet points, list markers
6. **Bracket inconsistencies**: Mixed `)` and `》` brackets
7. **Word fragmentation**: Rejoins broken words
8. **Capitalization errors**: `"wheRe the ORCS aRe"` → `"Where the Orcs Are"`
9. **Table structure issues**: Fixes malformed markdown tables
10. **Mathematical formulas**: Corrects corrupted LaTeX

## File Processing Rules

- **Preserves structure**: Maintains headers, tables, lists, figure references
- **Skips empty files**: Empty or whitespace-only files are ignored
- **Handles large files**: Files >50KB are copied as-is to avoid token limits
- **Retry logic**: Failed requests are retried with exponential backoff
- **Rate limiting**: 1-second delay between API calls
- **Fallback**: Failed files are copied as-is rather than lost

## Output Structure

```
demo_data/microsoft_ocr_results_gpt_corrected/
├── corrected_file1.md
├── corrected_file2.md
├── ...
└── failed_files.txt  # List of files that failed processing
```

## Cost Considerations

- Uses GPT-4o by default (cheaper than GPT-4)
- Processes files up to 50KB (~12,500 tokens)
- Estimated cost: ~$0.01-0.05 per file depending on size
- Monitor usage in Azure Portal

## Troubleshooting

### Common Issues

1. **API Key Error**: Check your `.env` file and Azure credentials
2. **Rate Limiting**: Script includes built-in rate limiting
3. **Large Files**: Files >50KB are copied as-is to avoid token limits
4. **Network Issues**: Automatic retry with exponential backoff

### Debug Mode

Add debug output by modifying the script:

```python
# In azure_openai_postprocess.py, add after line 89:
print(f"Request payload: {json.dumps(payload, indent=2)}")
```

### Check Failed Files

Review files that failed processing:

```bash
cat demo_data/microsoft_ocr_results_gpt_corrected/failed_files.txt
```

## Integration with OmniDocBench

The corrected markdown files can be used as input for OmniDocBench evaluation:

1. Update your evaluation config to point to the corrected results
2. Run evaluation as normal:

```bash
python pdf_validation.py --config configs/end2end.yaml
```

3. Compare results before/after postprocessing using:

```bash
python -m metrics.show_result
```