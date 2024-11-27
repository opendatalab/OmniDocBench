# OmniDocBench

![](https://github.com/user-attachments/assets/f3e53ba8-bb97-4ca9-b2e7-e2530865aaa9)

![](https://github.com/user-attachments/assets/ea389904-c130-410e-b05f-676882cc973c)

OmniDocBench主要是针对PDF页面内容解析提出的评测集，具有丰富的标注，可进行以下几个维度的评测：
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
- COCODet (mAP, mAR, etc.)

## 评测集下载

xxx

## 安装

```bash
conda create --name omnidocbench python=3.8 --file requirements.txt
```

## 评测使用

所有的评测的输入都是通过config文件进行配置的，我们在[configs](./configs)路径下提供了各个任务的模板。

配置好config文件后，只需要将config文件作为参数传入，运行以下代码即可：

```bash
python pdf_validation.py --config <config_path>
```

## 端到端评测-end2end（推荐）

端到端评测是对模型在PDF页面内容解析上的精度作出的评测。以模型输出的对整个PDF页面解析结果的Markdown作为Prediction。

端到端评测分为两种方式：
- `end2end`: 该方法是用OmniDocBench的JSON文件作为Ground Truth, config文件请参考：[end2end](./configs/end2end.yaml)
- `md2md`: 该方法是用OmniDocBench的markdown格式作为Ground Truth。具体内容将在下一小节`markdown-to-markdown评测`中详述。

我们推荐使用`end2end`的评测方式，因为该方式可以保留sample的类别和属性信息，从而帮助进行特殊类别ignore的操作，以及分属性的结果输出。

`end2end`的评测可以对四个维度进行评测，我们提供了一个end2end的评测结果示例在[result](./result)中，包括:
- 文本段落
- 行间公式
- 表格
- 阅读顺序

`end2end.yaml`的配置如下：

```YAML
end2end_eval:          # 指定task名称，端到端评测通用该task
  metrics:             # 配置需要使用的metric
    text_block:        # 针对文本段落的配置
      metric:
        - Edit_dist    # Normalized Edit Distance
        - BLEU         
        - METEOR
    display_formula:   # 针对行间公式的配置
      metric:
        - Edit_dist
        - CDM          # 仅支持导出CDM评测所需的格式，存储在results中
    table:             # 针对表格的配置
      metric:
        - TEDS
        - Edit_dist
    reading_order:     # 针对阅读顺序的配置
      metric:
        - Edit_dist
  dataset:                                       # 数据集配置
    dataset_name: end2end_dataset                # 数据集名称，无需修改
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json  # OmniDocBench的路径
    prediction:
      data_path: ./demo_data/end2end            # 模型对PDF页面解析markdown结果的文件夹路径
    match_method: quick_match                    # 匹配方式，可选有: no_split/no_split/quick_match
    filter:                                      # 页面级别的筛选
      language: english                          # 需要评测的页面属性以及对应标签
```

`prediction`下的`data_path`输入的是模型对PDF页面解析结果的文件夹路径，路径中保存的是每个页面对应的markdown，文件名与图片名保持一致，仅将.jpg后缀替换成.md。

除了已支持的metric以外，还支持导出[CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm)评测所需的格式，只需要在metric中配置CDM字段，即可将输出整理为CDM的输入格式，并存储在[result](./result)中。

在端到端的评测中，config里可以选择配置不同的匹配方式，一共有三种匹配方式：
- `no_split`: 不对text block做拆分和匹配的操作，而是直接合并成一整个markdown进行计算，这种方式下，将不会输出分属性的结果，也不会输出阅读顺序的结果；
- `no_split`: 不进行任何截断合并操作，仅对文本做双换行的段落分割后，直接与GT进行一对一匹配；
- `quick_match`：在段落分割的基础上，加上截断合并的操作，减少段落分割差异对最终结果的影响，通过Adjacency Search Match的方式进行截断合并；

我们推荐使用`quick_match`的方式以达到较好的匹配效果，但如果模型输出的段落分割较准确，也可以使用`simple_match`的方式，评测运行会更加迅速。匹配方法通过config中的dataset字段下的match_method字段进行配置。

使用`filter`字段可以对数据集进行筛选，比如将`dataset`下设置`filter`字段为`language: english`，将会仅评测页面语言为英文的页面。更多页面属性请参考“评测集介绍”部分。如果希望全量评测，请注释掉`filter`相关字段。

## 端到端评测-md2md

markdown-to-markdown评测以模型输出的对整个PDF页面解析结果的Markdown作为Prediction，用OmniDocBench的markdown格式作为Ground Truth。config文件请参考：[md2md](./configs/md2md.yaml)。我们更加推荐使用上一节的`end2end`的方式使用OmniDocBench进行评测，从而保留丰富的属性标注以及ignore逻辑。但是我们依然提供了`md2md`的评测方法，以便于与现有的评测方式对齐。

`md2md`的评测可以对三个维度进行评测，包括:
- 文本段落
- 行间公式
- 表格
- 阅读顺序

`md2md.yaml`的配置如下：

```YAML
end2end_eval:          # 指定task名称，端到端评测通用该task
  metrics:             # 配置需要使用的metric
    text_block:        # 针对文本段落的配置
      metric:
        - Edit_dist    # Normalized Edit Distance
        - BLEU         
        - METEOR
    display_formula:   # 针对行间公式的配置
      metric:
        - Edit_dist
        - CDM          # 仅支持导出CDM评测所需的格式，存储在results中
    table:             # 针对表格的配置
      metric:
        - TEDS
        - Edit_dist
    reading_order:     # 针对阅读顺序的配置
      metric:
        - Edit_dist
  dataset:                                               # 数据集配置
    dataset_name: md2md_dataset                          # 数据集名称，无需修改
    ground_truth:                                        # 针对ground truth的数据集配置
      data_path: ./demo_data/omnidocbench_demo/mds      # OmniDocBench的markdown文件夹路径
      page_info: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json          # OmniDocBench的JSON文件路径，主要是用于获取页面级别的属性
    prediction:                                          # 针对模型预测结果的配置
      data_path: ./demo_data/end2end                    # 模型对PDF页面解析markdown结果的文件夹路径
    match_method: quick_match                            # 匹配方式，可选有: no_split/no_split/quick_match
    filter:                                              # 页面级别的筛选
      language: english                                  # 需要评测的页面属性以及对应标签
```

`prediction`下的`data_path`输入的是模型对PDF页面解析结果的文件夹路径，路径中保存的是每个页面对应的markdown，文件名与图片名保持一致，仅将.jpg后缀替换成.md。

`ground_truth`下的`data_path`输入的是OmniDocBench的markdown文件夹路径，与模型对PDF页面解析结果的markdown文件名一一对应。`ground_truth`下的`page_info`路径输入的是OmniDocBench的JSON文件路径，主要是用于获取页面级别的属性。如果不需要页面级别分属性的评测结果输出，也可以直接将该字段注释掉。但是，如果没有配置`ground_truth`下的`page_info`字段，就无法使用`filter`相关功能。

除此之外的config中字段的解释请参考`端到端评测-end2end`小节。

## 公式识别评测

OmniDocBench包含每个PDF页面的公式的bounding box信息以及对应的公式识别标注，因此可以作为公式识别评测的benchmark。公式包括行间公式`equation_isolated`和行内公式`equation_inline`，本repo目前提供的例子是行间公式的评测。

公式识别评测可以参考[formula_recognition](./configs/formula_recognition.yaml)进行配置。 `formula_recognition.yaml`的配置文件如下：

```YAML
recogition_eval:      # 指定task名称，所有的识别相关的任务通用此task
  metrics:            # 配置需要使用的metric
    - Edit_dist       # Normalized Edit Distance
    - CDM             # 仅支持导出CDM评测所需的格式，存储在results中
  dataset:                                                                   # 数据集配置
    dataset_name: omnidocbench_single_module_dataset                         # 数据集名称，如果按照规定的输入格式则不需要修改
    ground_truth:                                                            # 针对ground truth的数据集配置
      data_path: ./demo_data/recognition/OmniDocBench_demo_formula.json      # 同时包含ground truth和模型prediction结果的JSON文件
      data_key: latex                                                        # 存储Ground Truth的字段名，对于OmniDocBench来说，公式的识别结果存储在latex这个字段中
      category_filter: ['equation_isolated']                                 # 用于评测的类别，在公式识别中，评测的category_name是equation_isolated
    prediction:                                                              # 针对模型预测结果的配置
      data_key: pred                                                         # 存储模型预测结果的字段名，这个是用户自定义的
    category_type: formula                                                   # category_type主要是用于数据预处理策略的选择，可选项有：formula/text
```

`metrics`部分，除了已支持的metric以外，还支持导出[CDM](https://github.com/opendatalab/UniMERNet/tree/main/cdm)评测所需的格式，只需要在metric中配置CDM字段，即可将输出整理为CDM的输入格式，并存储在[result](./result)中。

`dataset`的部分，输入的`ground_truth`的`data_path`中的数据格式与OmniDocBench保持一致，仅对应的公式sample下新增一个自定义字段保存模型的prediction结果。通过`dataset`下的`prediction`字段下的`data_key`对存储了prediction信息的字段进行指定，比如`pred`。关于更多OmniDocBench的文件结构细节请参考`评测集介绍`小节。模型结果的输入格式可以参考[OmniDocBench_demo_formula](./demo_data/recognition/OmniDocBench_demo_formula.json)，其格式为：

```JSON
[{
    "layout_dets": [    // 页面元素列表
        {
            "category_type": "equation_isolated",  // OmniDocBench类别名称
            "poly": [    // OmniDocBench位置信息，分别是左上角、右上角、右下角、左下角的x,y坐标
                136.0, 
                781.0,
                340.0,
                781.0,
                340.0,
                806.0,
                136.0,
                806.0
            ],
            ...   // 其他OmniDocBench字段
            "latex": "$xxx$",  // formula的LaTeX会写在这里
            "pred": "$xxx$",   // !! 模型的prediction结果存储在这里，由用户自定义一个新增字段，存储在与ground truth同级
            
        ...
    ],
    "page_info": {...},        // OmniDocBench页面信息
    "extra": {...}             // OmniDocBench标注间关系信息
},
...
]
```

在此提供一个模型infer的脚本供参考：

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
        if anno['category_type'] != 'equation_isolated':   # 筛选出行间公式类别进行评测
            continue

        bbox = poly2bbox(anno['poly'])
        im = img.crop(bbox).convert('RGB')
        response = model.chat(im, question)  # 需要根据模型修改传入图片的方式
        anno['pred'] = response              # 直接在对应的annotation下新增字段存储模型的infer结果

with open('./demo_data/recognition/OmniDocBench_demo_formula.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False)
```

## 文字OCR评测

OmniDocBench包含每个PDF页面的所有文字的bounding box信息以及对应的文字识别标注，因此可以作为OCR评测的benchmark。文本的标注包含block_level的标注和span_level的标注，都可以用于评测。本repo目前提供的例子是block_level的评测，即文本段落级别的OCR评测。

文字OCR评测可以参考[ocr](./configs/ocr.yaml)进行配置。 `ocr.yaml`的配置文件如下：

```YAML
recogition_eval:      # 指定task名称，所有的识别相关的任务通用此task
  metrics:            # 配置需要使用的metric
    - Edit_dist       # Normalized Edit Distance
    - BLEU
    - METEOR
  dataset:                                                                   # 数据集配置
    dataset_name: omnidocbench_single_module_dataset                         # 数据集名称，如果按照规定的输入格式则不需要修改
    ground_truth:                                                            # 针对ground truth的数据集配置
      data_path: ./demo_data/recognition/OmniDocBench_demo_text_ocr.json     # 同时包含ground truth和模型prediction结果的JSON文件
      data_key: text                                                         # 存储Ground Truth的字段名，对于OmniDocBench来说，文本识别结果存储在text这个字段中，所有block level只要包含text字段的annotations都会参与评测
    prediction:                                                              # 针对模型预测结果的配置
      data_key: pred                                                         # 存储模型预测结果的字段名，这个是用户自定义的
    category_type: text                                                      # category_type主要是用于数据预处理策略的选择，可选项有：formula/text
```

`dataset`的部分，输入的`ground_truth`的`data_path`中的数据格式与OmniDocBench保持一致，仅对应的含有text字段的sample下新增一个自定义字段保存模型的prediction结果。通过`dataset`下的`prediction`字段下的`data_key`对存储了prediction信息的字段进行指定，比如`pred`。数据集的输入格式可以参考[OmniDocBench_demo_text_ocr](./demo_data/recognition/OmniDocBench_demo_text_ocr.json)，各个字段含义可以参考`公式识别评测`部分提供的样例。

在此提供一个模型infer的脚本供参考：

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
        if not anno.get('text'):             # 筛选出OmniDocBench中包含text字段的annotations进行模型infer
            continue

        bbox = poly2bbox(anno['poly'])
        im = img.crop(bbox).convert('RGB')
        response = model.chat(im, question)  # 需要根据模型修改传入图片的方式
        anno['pred'] = response              # 直接在对应的annotation下新增字段存储模型的infer结果

with open('./demo_data/recognition/OmniDocBench_demo_text_ocr.json', 'w', encoding='utf-8') as f:
    json.dump(samples, f, ensure_ascii=False)
```

## 表格识别评测

xxx

## Layout检测

OmniDocBench包含每个PDF页面的所有文档组件的bounding box信息，因此可以作为Layout检测任务评测的benchmark。

Layout检测config文件参考[layout_detection](./configs/layout_detection.yaml)，数据格式参考[detection_prediction](./demo_data/detection/detection_prediction.json)。

以下我们以精简格式为例进行展示。`layout_detection.yaml`的配置文件如下：

```YAML
detection_eval:   # 指定task名称，所有的检测相关的任务通用此task
  metrics:
    - COCODet     # 检测任务相关指标，主要是mAP, mAR等
  dataset: 
    dataset_name: detection_dataset_simple_format       # 数据集名称，如果按照规定的输入格式则不需要修改
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json               # OmniDocBench的JSON文件路径
    prediction:
      data_path: ./demo_data/detection/detection_prediction.json                    # 模型预测结果JSON文件路径
    filter:                                             # 页面级别的筛选
      data_source: exam_paper                           # 需要评测的页面属性以及对应标签
  categories:
    eval_cat:                # 参与最终评测的类别
      block_level:           # block级别的类别，详细类别信息请参考OmniDocBench的评测集介绍部分
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
    gt_cat_mapping:          # ground truth到最终评测类别的映射表，key是ground truth类别，value是最终评测类别名称
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
    pred_cat_mapping:       # prediction到最终评测类别的映射表，key是prediction类别，value是最终评测类别名称
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

使用filter字段可以对数据集进行筛选，比如将`dataset`下设置`filter`字段为`data_source: exam_paper`即筛选数据类型为exam_paper的页面。更多页面属性请参考“评测集介绍”部分。如果希望全量评测，请注释掉`filter`相关字段。

`dataset`部分`prediction`的`data_path`中传入的是模型的prediction，其数据格式为：

```JSON
{
    "results": [
        {
            "image_name": "docstructbench_llm-raw-scihub-o.O-adsc.201190003.pdf_6",                     // 图片名
            "bbox": [53.892921447753906, 909.8675537109375, 808.5555419921875, 1006.2714233398438],     // bounding box信息，分别是左上角和右下角的x,y坐标
            "category_id": 1,                                                                           // 类别序号名称
            "score": 0.9446213841438293                                                                 // 置信度
        }, 
        ...                                                                                             // 所有的bounding box都直接平铺在一个list内部
    ],
    "categories": {"0": "title", "1": "plain text", "2": "abandon", ...}                                // 每个类别序号所对应的类别名称
```


## 公式检测

OmniDocBench包含每个PDF页面的公式的bounding box信息，因此可以作为Layout检测任务评测的benchmark。公式检测与Layout检测的格式基本一致。公式包含行内公式和行间公式。在本节提供一个config样例，可以同时评测行间公式和行内公式的检测结果。

公式检测可以参考[formula_detection](./configs/formula_detection.yaml)进行配置。`formula_detection.yaml`的配置文件如下：

```YAML
detection_eval:   # 指定task名称，所有的检测相关的任务通用此task
  metrics:
    - COCODet     # 检测任务相关指标，主要是mAP, mAR等
  dataset: 
    dataset_name: detection_dataset_simple_format       # 数据集名称，如果按照规定的输入格式则不需要修改
    ground_truth:
      data_path: ./demo_data/omnidocbench_demo/OmniDocBench_demo.json               # OmniDocBench的JSON文件路径
    prediction:
      data_path: ./demo_data/detection/detection_prediction.json                     # 模型预测结果JSON文件路径
    filter:                                             # 页面级别的筛选
      data_source: exam_paper                           # 需要评测的页面属性以及对应标签
  categories:
    eval_cat:                                  # 参与最终评测的类别
      block_level:                             # block级别的类别，详细类别信息请参考OmniDocBench的评测集介绍部分
        - isolate_formula                      # 行间公式
      span_level:                              # span级别的类别，详细类别信息请参考OmniDocBench的评测集介绍部分
        - inline_formula                       # 行内公式
    gt_cat_mapping:                            # ground truth到最终评测类别的映射表，key是ground truth类别，value是最终评测类别名称
      equation_isolated: isolate_formula
      equation_inline: inline_formula
    pred_cat_mapping:                          # prediction到最终评测类别的映射表，key是prediction类别，value是最终评测类别名称
      interline_formula: isolate_formula
      inline_formula: inline_formula
```

config中参数解释以及数据集格式请参考`Layout检测`小节，公式检测与Layout检测小节的主要区别是，在参与最终评测的类别`eval_cat`下新增了`span_level`的类别`inline_formula`，span_level的类别和block_level级别的类别在评测的时候将会共同参与评测。


## 评测集介绍

评测集的数据格式为JSON，其结构和各个字段的解释如下：

```json
[{
    "layout_dets": [    // 页面元素列表
        {
            "category_type": "text_block",  // 类别名称
            "poly": [
                136.0, // 位置信息，分别是左上角、右上角、右下角、左下角的x,y坐标
                781.0,
                340.0,
                781.0,
                340.0,
                806.0,
                136.0,
                806.0
            ],
            "ignore": false,        // 是否在评测的时候不考虑
            "order": 0,             // 阅读顺序
            "anno_id": 0,           // 特殊的标注ID，每个layout框唯一
            "text": "xxx",          // 可选字段，OCR结果会写在这里
            "latex": "$xxx$",       // 可选字段，formula和table的LaTeX会写在这里
            "html": "xxx",          // 可选字段，table的HTML会写在这里
            "attribute" {"xxx": "xxx"},         // layout的分类属性，后文会详细展示
            "line_with_spans:": [   // span level的标注框
                {
                    "category_type": "text_span",
                    "poly": [...],
                    "ignore": false,
                    "text": "xxx",   
                    "latex": "$xxx$",
                 },
                 ...
            ],
            "merge_list": [    // 只有包含merge关系的标注框内有这个字段，是否包含merge逻辑取决于是否包含单换行分割小段落，比如列表类型
                {
                    "category_type": "text_block", 
                    "poly": [...],
                    ...   // 跟block级别标注的字段一致
                    "line_with_spans": [...]
                    ...
                 },
                 ...
            ]
        ...
    ],
    "page_info": {         
        "page_no": 0,            // 页码
        "height": 1684,          // 页面的宽
        "width": 1200,           // 页面的高
        "image_path": "xx/xx/",  // 标注的页面文件名称
        "page_attribute": {"xxx": "xxx"}     // 页面的属性标签
    },
    "extra": {
        "relation": [ // 具有相关关系的标注
            {  
                "source_anno_id": 1,
                "target_anno_id": 2, 
                "relation": "parent_son"  // figure/table与其对应的caption/footnote类别的关系标签
            },
            {  
                "source_anno_id": 5,
                "target_anno_id": 6,
                "relation_type": "truncated"  // 段落因为排版原因被截断，会标注一个截断关系标签，后续评测的时候会拼接后再作为一整个段落进行评测
            },
        ]
    }
},
...
]
```

验证集类别包括：

```
# Block级别标注框
'title'               # 标题
'text_block'          # 段落级别纯文本
'figure',             # 图片类
'figure_caption',     # 图片说明、标题
'figure_footnote',    # 图片注释
'table',              # 表格主体
'table_caption',      # 表格说明和标题
'table_footnote',     # 表格的注释
'equation_isolated',  # 行间公式
'equation_caption',   # 公式序号
'header'              # 页眉
'footer'              # 页脚  
'page_number'         # 页码
'page_footnote'       # 页面注释
'abandon',            # 其他的舍弃类（比如页面中间的一些无关信息）
'code_txt',           # 代码块
'code_txt_caption',   # 代码块说明
'reference',          # 参考文献类

# Span级别标注框
'text_span'           # span级别的纯文本
'equation_ignore',    # 需要忽略的公式类
'equation_inline',    # 行内公式类
'footnote_mark',      #文章的上下角标
```

页面分类属性包括：
```
'data_source': #PDF类型分类
    academic_literature  # 学术文献
    PPT2PDF # PPT转PDF
    book # 黑白的图书和教材
    colorful_textbook # 彩色图文教材
    exam_paper # 试卷
    note # 手写笔记
    magazine # 杂志
    research_report # 研报、财报
    newspaper # 报纸

'language':#语种
    en # 英文
    simplified_chinese # 简体中文
    en_ch_mixed # 中英混合

'layout': #页面布局类型
    single_column # 单栏
    double_column # 双栏
    three_column # 三栏
    1andmore_column # 一混多，常见于文献
    other_layout # 其他

'watermark'： # 是否包含水印
    true  
    false

'fuzzy_scan': # 是否模糊扫描
    true  
    false

'colorful_backgroud': # 是否包含彩色背景，需要参与识别的内容的底色包含两个以上
    true  
    false
```

标注框级别属性-表格相关属性:

```
'table_layout': # 表格的方向
    vertical #竖版表格
    horizontal #横版表格

'with_span': # 合并单元格
    False
    True

'line':# 表格的线框
    full_line # 全线框
    less_line # 漏线框
    fewer_line # 三线框 
    wireless_line # 无线框

'language': #表格的语种
    table_en  # 英文表格
    table_simplified_chinese  #中文简体表格
    table_en_ch_mixed  #中英混合表格

'include_equation': # 表格是否包含公式
    False
    True

'include_backgroud': # 表格是否包含底色
    False
    True

'table_vertical' # 表格是否旋转90度或270度
    False
    True
```

标注框级别属性-文本段落相关属性: 
```
'text_language': # 文本的段落内语种
    text_en  # 英文
    text_simplified_chinese #简体中文
    text_en_ch_mixed  #中英混合

'text_background':  #文本的背景色
    white # 默认值，白色背景
    single_colored # 除白色外的单背景色
    multi_colored  # 混合背景色

'text_rotate': # 文本的段落内文字旋转分类
    normal # 默认值，横向文本，没有旋转
    rotate90  # 旋转角度，顺时针旋转90度
    rotate180 # 顺时针旋转180度
    rotate270 # 顺时针旋转270度
    horizontal # 文字是正常的，排版是竖型文本
```

标注框级别属性-公式相关属性: 
```
'formula_type': #公式类型
    print  # 打印体
    handwriting # 手写体
```