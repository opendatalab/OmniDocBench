# OmniDocBench

OmniDocBench主要是针对PDF页面内容解析提出的评测集。该评测代码主要用于适配OmniDocBench的评测，可进行以下几个维度的评测：
- 端到端评测：包括end2end和md2md两种评测方式
- Layout检测
- 表格识别
- 公式识别
- 文本OCR

目前支持的metric包括：
- Normalized Edit Distance
- BLEU
- METEOR
- TEDS

所有的评测的输入都是通过config文件进行配置的，我们在./configs路径下提供了各个任务的模板。

配置好config文件后，只需要将config文件作为参数传入，运行以下代码即可：

```bash
python pdf_validation.py --config ./configs/end2end.yaml
```

## 端到端评测

端到端评测是对模型在PDF页面内容解析上的精度作出的评测。以模型输出的对整个PDF页面解析结果的Markdown作为Prediction。

端到端评测分为两种方式：
- end2end: 该方法是用OmniDocBench的JSON文件作为Ground Truth, config文件请参考：./configs/end2end.yaml
- md2md: 该方法是用OmniDocBench的markdown格式作为Ground Truth。config文件请参考：./configs/md2md.yaml

我们推荐使用end2end的评测方式，因为该方式可以保留sample的类别和属性信息，从而帮助进行特殊类别ignore的操作，以及分属性的结果输出。

除此之外，在端到端的评测中，config里可以选择配置不同的匹配方式，一共有三种匹配方式：
- no_split: 不对text block做拆分和匹配的操作，而是直接合并成一整个markdown进行计算，这种方式下，将不会输出分属性的结果，也不会输出阅读顺序的结果
- simple_match: 不进行任何截断合并操作，仅对文本做双换行的段落分割后，直接与GT进行一对一匹配
- quick_match：在段落分割的基础上，加上截断合并的操作，减少段落分割差异对最终结果的影响，通过Adjacency Search Match的方式进行截断合并

我们推荐使用quick_match的方式以达到较好的匹配效果，但如果模型输出的段落分割较准确，也可以使用simple match的方式，评测运行会更加迅速。匹配方法通过config中的dataset字段下的match_method字段进行配置。

## 公式识别评测

公式识别评测可以参考./configs/formula_omidocbench.yaml进行配置，输入的格式与OmniDocBench保持一致，模型的prediction保存在对应的公式sample下，新建一个自定义字段进行保存，并且通过prediction的data_key对存储了prediction信息的字段进行指定。

metric中配置CDM字段可以将输出整理为CDM的输入格式，并存储在result中，用户可以直接将其输入到CDM中进行计算。

## 文字OCR评测

文字OCR评测可以参考./configs/ocr_omidocbench.yaml进行配置，输入的格式与OmniDocBench保持一致，模型的prediction保存在对应的公式sample下，新建一个自定义字段进行保存，并且通过prediction的data_key对存储了prediction信息的字段进行指定。

## 表格识别评测

xxx

## Layout检测

