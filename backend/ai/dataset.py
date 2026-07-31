"""
dataset.py — PlantVillage dataset loader for AgriSense AI.

Provides:
  - PlantVillageDataset: PyTorch Dataset with production-grade transforms.
  - get_train_transforms() / get_val_transforms(): callable transform builders
    so inference.py can import identical val-transforms without circular deps.

Training transforms:  RandomResizedCrop → Flip → Rotation → ColorJitter → ToTensor → Normalize
Validation transforms: Resize(256) → CenterCrop(224) → ToTensor → Normalize

ImageNet mean/std used throughout for EfficientNet-B0 compatibility.
"""

from pathlib import Path
from PIL import Image

from torch.utils.data import Dataset
from torchvision import transforms

# ─── ImageNet statistics (same as EfficientNet-B0 pretraining) ────────────────
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]


def get_train_transforms() -> transforms.Compose:
    """
    Return augmented training transforms.
    RandomResizedCrop forces the model to learn from partial views,
    which dramatically improves generalisation on field images.
    """
    return transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.3,
            hue=0.05,
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


def get_val_transforms() -> transforms.Compose:
    """
    Return deterministic validation / inference transforms.
    Resize to 256 then centre-crop to 224 — this is the canonical
    EfficientNet-B0 evaluation pipeline.
    """
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


class PlantVillageDataset(Dataset):
    """
    PyTorch Dataset for PlantVillage images.

    Args:
        image_paths: List of absolute paths to image files.
        labels:      Integer class index for each image.
        train:       If True, applies training augmentations.
                     If False, applies deterministic val/inference transforms.
    """

    def __init__(
        self,
        image_paths: list,
        labels: list,
        train: bool = True,
    ) -> None:
        self.image_paths = image_paths
        self.labels = labels
        self.transform = get_train_transforms() if train else get_val_transforms()

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, index: int):
        image = Image.open(self.image_paths[index]).convert("RGB")
        image = self.transform(image)
        label = self.labels[index]
        return image, label