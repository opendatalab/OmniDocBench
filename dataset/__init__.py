from .recog_dataset import *
from .end2end_dataset import *
from .detection_dataset import *
from registry.registry import DATASET_REGISTRY

__all__ = [
    "RecognitionFormulaDataset",
    "End2EndDataset",
    "DetectionDataset"
]

print('DATASET_REGISTRY: ', DATASET_REGISTRY.list_items())