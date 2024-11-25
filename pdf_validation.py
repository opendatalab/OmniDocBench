# coding: utf-8
import os
import argparse
import sys
import io
import os
import pathlib
import sys
import yaml
from registry.registry import EVAL_TASK_REGISTRY, DATASET_REGISTRY, METRIC_REGISTRY
import dataset
import task
import metrics

def process_args(args):
    parser = argparse.ArgumentParser(description='Render latex formulas for comparison.')
    parser.add_argument('--config', '-c', type=str, default='./configs/end2end.yaml')
    parameters = parser.parse_args(args)
    return parameters

if __name__ == '__main__':
    parameters = process_args(sys.argv[1:])
    config_path = parameters.config
    
    if isinstance(config_path, (str, pathlib.Path)):
        with io.open(os.path.abspath(config_path), "r", encoding="utf-8") as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise TypeError("Unexpected file type")

    if cfg is not None and not isinstance(cfg, (list, dict, str)):
        raise IOError(  # pragma: no cover
            f"Invalid loaded object type: {type(cfg).__name__}"
        )


    for task in cfg.keys():
        if not cfg.get(task):
            print(f'No config for task {task}')
        dataset = cfg[task]['dataset']['dataset_name']
        # metrics_list = [METRIC_REGISTRY.get(i) for i in cfg[task]['metrics']] # TODO: 直接在主函数里实例化
        metrics_list = cfg[task]['metrics']  # 在task里再实例化
        val_dataset = DATASET_REGISTRY.get(dataset)(cfg[task])
        val_task = EVAL_TASK_REGISTRY.get(task)
        # val_task(val_dataset, metrics_list)
        if cfg[task]['dataset']['prediction'].get('data_path'):
            save_name = os.path.basename(cfg[task]['dataset']['prediction']['data_path']) + '_' + cfg[task]['dataset'].get('match_method', 'quick_match')
        else:
            save_name = os.path.basename(cfg[task]['dataset']['ground_truth']['data_path']).split('.')[0]
        print('###### Process: ', save_name)
        if cfg[task]['dataset']['ground_truth'].get('page_info'):
            val_task(val_dataset, metrics_list, cfg[task]['dataset']['ground_truth']['page_info'], save_name)  # 按页面区分
        else:
            val_task(val_dataset, metrics_list, cfg[task]['dataset']['ground_truth']['data_path'], save_name)  # 按页面区分
