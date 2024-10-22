# PDF Validation

运行代码：

```bash
python pdf_validation.py --config ./configs/vali.yaml
```

验证通过配置文件来完成以下参数的传入：1. 通过config来设定需要验证的task; 2. 传入GT和prediction; 3. Detection任务里，可以设置需要验证的类别，以及标注类别映射

目前，Detection部分打算以pipeline的格式进行验证，formula recognition用[unimernet_test](https://huggingface.co/datasets/wanderkid/UniMER_Dataset/tree/main)的格式。
