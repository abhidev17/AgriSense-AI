"""
train_crop.py — Production crop classifier training script for AgriSense AI.

Trains an EfficientNet-B0 to classify crop species from PlantVillage images.

Usage (from the backend/ai/ directory):
    python train_crop.py

Expected dataset layout:
    datasets/PlantVillage/
        Tomato___Early_blight/    ← folder names follow PlantVillage convention
        Tomato___healthy/
        Potato___Early_blight/
        ...

Outputs:
    models/crop_model.pth          ← best checkpoint (full training state)
    models/classes.json            ← updated crop_classes mapping
    models/reports/crop_*.txt/csv/json  ← evaluation reports

Target: >95% validation accuracy on PlantVillage crops.
"""

import json
import sys
from pathlib import Path

# Make sure imports resolve whether run from /ai or /backend
sys.path.insert(0, str(Path(__file__).parent))

import torch
from torch.utils.data import DataLoader

from dataset import PlantVillageDataset
from trainer import AgriSenseTrainer, TrainConfig
from utils import load_crop_dataset

# ──────────────────────────────────────────────────────────────────────────────
# Configuration  — edit these values to tune training
# ──────────────────────────────────────────────────────────────────────────────

cfg = TrainConfig()
cfg.MODEL_NAME      = "crop"
cfg.DATASET_PATH    = "../datasets/PlantVillage"
cfg.SAVE_DIR        = "../models"

# Architecture
cfg.FREEZE_BACKBONE  = True    # freeze EfficientNet backbone initially
cfg.UNFREEZE_EPOCH   = 10      # unfreeze backbone from this epoch onwards
cfg.FINETUNE_LR      = 1e-5   # lower LR for fine-tuning stage

# Optimiser
cfg.BATCH_SIZE       = 32
cfg.EPOCHS           = 30
cfg.LEARNING_RATE    = 3e-4
cfg.WEIGHT_DECAY     = 1e-4

# Scheduler
cfg.LR_FACTOR        = 0.5
cfg.LR_PATIENCE      = 2

# Early stopping
cfg.PATIENCE         = 5

# Reproducibility
cfg.SEED             = 42
cfg.NUM_WORKERS      = 0       # set to 4+ on Linux/Mac for faster loading

MODEL_SAVE_PATH = str(Path(cfg.SAVE_DIR) / "crop_model.pth")
CLASS_FILE      = str(Path(cfg.SAVE_DIR) / "classes.json")

# ──────────────────────────────────────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────────────────────────────────────

print("Loading crop dataset...")
train_x, val_x, train_y, val_y, crop_classes = load_crop_dataset(cfg.DATASET_PATH)

print(f"  Train samples : {len(train_x)}")
print(f"  Val samples   : {len(val_x)}")
print(f"  Crop classes  : {len(crop_classes)}  → {list(crop_classes.keys())}\n")

train_dataset = PlantVillageDataset(train_x, train_y, train=True)
val_dataset   = PlantVillageDataset(val_x,   val_y,   train=False)

train_loader = DataLoader(
    train_dataset,
    batch_size=cfg.BATCH_SIZE,
    shuffle=True,
    num_workers=cfg.NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    persistent_workers=(cfg.NUM_WORKERS > 0),
)

val_loader = DataLoader(
    val_dataset,
    batch_size=cfg.BATCH_SIZE,
    shuffle=False,
    num_workers=cfg.NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    persistent_workers=(cfg.NUM_WORKERS > 0),
)

# ──────────────────────────────────────────────────────────────────────────────
# Train
# ──────────────────────────────────────────────────────────────────────────────

trainer = AgriSenseTrainer(
    cfg=cfg,
    num_classes=len(crop_classes),
    save_path=MODEL_SAVE_PATH,
)

best_accuracy = trainer.fit(train_loader, val_loader)

# ──────────────────────────────────────────────────────────────────────────────
# Post-training evaluation
# ──────────────────────────────────────────────────────────────────────────────

print("Generating evaluation report on validation set...")
class_names = list(crop_classes.keys())
trainer.evaluate(val_loader, class_names=class_names)

# ──────────────────────────────────────────────────────────────────────────────
# Save / update classes.json
# ──────────────────────────────────────────────────────────────────────────────

Path(cfg.SAVE_DIR).mkdir(parents=True, exist_ok=True)

if Path(CLASS_FILE).exists():
    with open(CLASS_FILE, "r") as f:
        data = json.load(f)
else:
    data = {}

data["crop_classes"] = crop_classes

with open(CLASS_FILE, "w") as f:
    json.dump(data, f, indent=4)

print(f"  classes.json updated at {CLASS_FILE}")

# ──────────────────────────────────────────────────────────────────────────────
# Final summary
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  CROP TRAINING COMPLETED")
print(f"  Best Validation Accuracy : {best_accuracy:.2f}%")
print(f"  Model saved to           : {MODEL_SAVE_PATH}")
print(f"  Classes saved to         : {CLASS_FILE}")
print("=" * 60)
