"""
trainer.py — Shared production training engine for AgriSense AI.

Both train_crop.py and train_disease.py instantiate AgriSenseTrainer,
which provides:

  - Frozen-backbone warm-up → optional full-model fine-tune
  - AdamW optimiser + ReduceLROnPlateau scheduler
  - Early stopping (patience=5 by default)
  - Mixed-precision (AMP) when CUDA is available
  - Per-epoch metrics: loss, accuracy, learning-rate
  - tqdm progress bars
  - Best-model checkpointing (saves full training state)
  - Post-training evaluation: confusion matrix + classification report
  - Deterministic seeding for reproducibility
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

try:
    from tqdm import tqdm
    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False

try:
    from sklearn.metrics import classification_report, confusion_matrix
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


# ─── Training Configuration dataclass ─────────────────────────────────────────

class TrainConfig:
    """
    All hyperparameters in one place.
    Override individual fields before passing to AgriSenseTrainer.
    """

    # Dataset
    DATASET_PATH:   str   = "../datasets/PlantVillage"
    SAVE_DIR:       str   = "../models"
    MODEL_NAME:     str   = "model"          # used in log messages

    # Architecture
    FREEZE_BACKBONE: bool = True             # freeze EfficientNet features initially

    # Optimiser
    BATCH_SIZE:     int   = 32
    EPOCHS:         int   = 30
    LEARNING_RATE:  float = 3e-4
    WEIGHT_DECAY:   float = 1e-4

    # Scheduler
    LR_FACTOR:      float = 0.5
    LR_PATIENCE:    int   = 2               # epochs without improvement before LR drop

    # Early stopping
    PATIENCE:       int   = 5               # epochs without val-acc improvement → stop

    # Fine-tune
    UNFREEZE_EPOCH: int   = 10              # epoch at which backbone is unfrozen
    FINETUNE_LR:    float = 1e-5            # lower LR for full-model fine-tuning

    # Reproducibility
    SEED:           int   = 42

    # DataLoader workers (0 = main process, safe on Windows)
    NUM_WORKERS:    int   = 0


# ─── Trainer ──────────────────────────────────────────────────────────────────

class AgriSenseTrainer:
    """
    Production training engine.

    Usage::

        cfg = TrainConfig()
        cfg.MODEL_NAME = "crop"
        cfg.EPOCHS = 30
        trainer = AgriSenseTrainer(cfg, num_classes=14, save_path="crop_model.pth")
        trainer.fit(train_loader, val_loader)
        trainer.evaluate(val_loader, class_names)
    """

    def __init__(
        self,
        cfg: TrainConfig,
        num_classes: int,
        save_path: str,
    ) -> None:
        self.cfg = cfg
        self.num_classes = num_classes
        self.save_path = save_path

        self._set_seed(cfg.SEED)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_amp = torch.cuda.is_available()
        self.scaler: Optional[GradScaler] = GradScaler() if self.use_amp else None

        print(f"\n{'='*60}")
        print(f"  AgriSense AI — {cfg.MODEL_NAME.upper()} Trainer")
        print(f"{'='*60}")
        print(f"  Device        : {self.device}")
        print(f"  Mixed Prec.   : {'ON (AMP)' if self.use_amp else 'OFF (CPU mode)'}")
        print(f"  Classes       : {num_classes}")
        print(f"  Epochs        : {cfg.EPOCHS}")
        print(f"  Batch Size    : {cfg.BATCH_SIZE}")
        print(f"  Learning Rate : {cfg.LEARNING_RATE}")
        print(f"  Backbone Freeze: {cfg.FREEZE_BACKBONE} (unfreezes at epoch {cfg.UNFREEZE_EPOCH})")
        print(f"  Early Stop    : patience={cfg.PATIENCE}")
        print(f"{'='*60}\n")

        self.model = self._build_model()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer, self.scheduler = self._build_optimizer()

        self.best_val_acc = 0.0
        self.epochs_no_improve = 0
        self._backbone_unfrozen = not cfg.FREEZE_BACKBONE

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
    ) -> float:
        """
        Run the full training loop.
        Returns the best validation accuracy achieved.
        """
        for epoch in range(1, self.cfg.EPOCHS + 1):

            # ── Optional backbone unfreeze ─────────────────────────────────
            if (
                self.cfg.FREEZE_BACKBONE
                and not self._backbone_unfrozen
                and epoch == self.cfg.UNFREEZE_EPOCH
            ):
                self._unfreeze_backbone()

            # ── Train + validate ───────────────────────────────────────────
            train_loss, train_acc = self._train_epoch(train_loader, epoch)
            val_loss, val_acc     = self._val_epoch(val_loader, epoch)
            current_lr            = self.optimizer.param_groups[0]["lr"]

            # ── Print epoch summary ────────────────────────────────────────
            print(
                f"\n  Epoch {epoch:>3}/{self.cfg.EPOCHS}"
                f"  |  Train Loss: {train_loss:.4f}  Train Acc: {train_acc:.2f}%"
                f"  |  Val Loss: {val_loss:.4f}  Val Acc: {val_acc:.2f}%"
                f"  |  LR: {current_lr:.2e}"
            )

            # ── LR scheduler step ─────────────────────────────────────────
            self.scheduler.step(val_acc)

            # ── Checkpoint if improved ────────────────────────────────────
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.epochs_no_improve = 0
                self._save_checkpoint(epoch, val_acc)
                print(f"  ✓ New best val accuracy: {val_acc:.2f}% — checkpoint saved.")
            else:
                self.epochs_no_improve += 1
                print(
                    f"  ↓ No improvement ({self.epochs_no_improve}/{self.cfg.PATIENCE})"
                )

            # ── Early stopping ─────────────────────────────────────────────
            if self.epochs_no_improve >= self.cfg.PATIENCE:
                print(
                    f"\n  Early stopping triggered after {epoch} epochs "
                    f"(no improvement for {self.cfg.PATIENCE} epochs)."
                )
                break

        print(f"\n{'='*60}")
        print(f"  Training complete.")
        print(f"  Best Validation Accuracy : {self.best_val_acc:.2f}%")
        print(f"  Model saved to           : {self.save_path}")
        print(f"{'='*60}\n")
        return self.best_val_acc

    def evaluate(
        self,
        val_loader: DataLoader,
        class_names: list[str],
        report_dir: Optional[str] = None,
    ) -> None:
        """
        Generate confusion matrix + classification report on val_loader.
        Saves results to report_dir (defaults to SAVE_DIR/reports/).
        """
        if not _SKLEARN_AVAILABLE:
            print("  [WARN] scikit-learn not installed — skipping evaluation report.")
            return

        # Load best checkpoint before evaluating
        self._load_best_checkpoint()

        report_dir = report_dir or os.path.join(self.cfg.SAVE_DIR, "reports")
        Path(report_dir).mkdir(parents=True, exist_ok=True)

        self.model.eval()
        all_preds, all_labels = [], []

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(self.device)
                outputs = self.model(images)
                preds = outputs.argmax(dim=1).cpu().tolist()
                all_preds.extend(preds)
                all_labels.extend(labels.tolist())

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        np.savetxt(
            os.path.join(report_dir, f"{self.cfg.MODEL_NAME}_confusion_matrix.csv"),
            cm,
            delimiter=",",
            fmt="%d",
        )

        # Classification report
        report_txt = classification_report(
            all_labels,
            all_preds,
            target_names=class_names,
            zero_division=0,
        )
        report_path = os.path.join(
            report_dir, f"{self.cfg.MODEL_NAME}_classification_report.txt"
        )
        with open(report_path, "w") as f:
            f.write(report_txt)

        # Per-class accuracy
        per_class_acc = {}
        cm_norm = cm.astype(float)
        for i, name in enumerate(class_names):
            row_sum = cm[i].sum()
            per_class_acc[name] = round(float(cm[i, i] / row_sum * 100), 2) if row_sum > 0 else 0.0

        acc_path = os.path.join(
            report_dir, f"{self.cfg.MODEL_NAME}_per_class_accuracy.json"
        )
        with open(acc_path, "w") as f:
            json.dump(per_class_acc, f, indent=4)

        print(f"\n{report_txt}")
        print(f"  Reports saved to: {report_dir}")

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _set_seed(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Deterministic ops (minor perf cost)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    def _build_model(self) -> nn.Module:
        weights = EfficientNet_B0_Weights.DEFAULT
        model = efficientnet_b0(weights=weights)

        # Replace classifier head
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, self.num_classes),
        )

        # Freeze backbone if requested
        if self.cfg.FREEZE_BACKBONE:
            for param in model.features.parameters():
                param.requires_grad = False
            print("  Backbone frozen — training classifier head only.")

        return model.to(self.device)

    def _build_optimizer(self):
        trainable = filter(lambda p: p.requires_grad, self.model.parameters())
        optimizer = AdamW(
            trainable,
            lr=self.cfg.LEARNING_RATE,
            weight_decay=self.cfg.WEIGHT_DECAY,
        )
        scheduler = ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=self.cfg.LR_FACTOR,
            patience=self.cfg.LR_PATIENCE,
        )
        return optimizer, scheduler

    def _unfreeze_backbone(self) -> None:
        """Unfreeze all backbone parameters and lower the learning rate."""
        for param in self.model.parameters():
            param.requires_grad = True

        # Update optimizer to track newly unfrozen params at a lower LR
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.cfg.FINETUNE_LR,
            weight_decay=self.cfg.WEIGHT_DECAY,
        )
        self.scheduler = ReduceLROnPlateau(
            self.optimizer,
            mode="max",
            factor=self.cfg.LR_FACTOR,
            patience=self.cfg.LR_PATIENCE,
        )
        self._backbone_unfrozen = True
        print(
            f"\n  *** Backbone unfrozen at epoch {self.cfg.UNFREEZE_EPOCH} "
            f"— LR reset to {self.cfg.FINETUNE_LR:.1e} ***\n"
        )

    def _train_epoch(
        self, loader: DataLoader, epoch: int
    ) -> tuple[float, float]:
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        iterator = (
            tqdm(loader, desc=f"  Epoch {epoch:>3} [train]", leave=False)
            if _TQDM_AVAILABLE
            else loader
        )

        for images, labels in iterator:
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)

            if self.use_amp:
                with autocast():
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)
                self.scaler.scale(loss).backward()
                self.scaler.unscale_(self.optimizer)
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()

            total_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            if _TQDM_AVAILABLE:
                iterator.set_postfix(
                    loss=f"{loss.item():.4f}",
                    acc=f"{correct / total * 100:.1f}%",
                )

        return total_loss / total, correct / total * 100

    def _val_epoch(
        self, loader: DataLoader, epoch: int
    ) -> tuple[float, float]:
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        iterator = (
            tqdm(loader, desc=f"  Epoch {epoch:>3} [val]  ", leave=False)
            if _TQDM_AVAILABLE
            else loader
        )

        with torch.no_grad():
            for images, labels in iterator:
                images = images.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                if self.use_amp:
                    with autocast():
                        outputs = self.model(images)
                        loss = self.criterion(outputs, labels)
                else:
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)

                total_loss += loss.item() * images.size(0)
                preds = outputs.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        return total_loss / total, correct / total * 100

    def _save_checkpoint(self, epoch: int, val_acc: float) -> None:
        Path(self.save_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "scheduler_state_dict": self.scheduler.state_dict(),
                "best_accuracy": val_acc,
                "num_classes": self.num_classes,
            },
            self.save_path,
        )

    def _load_best_checkpoint(self) -> None:
        if not os.path.exists(self.save_path):
            return
        ckpt = torch.load(self.save_path, map_location=self.device)
        # Support both plain state_dict and full checkpoint dict
        if "model_state_dict" in ckpt:
            self.model.load_state_dict(ckpt["model_state_dict"])
        else:
            self.model.load_state_dict(ckpt)
        self.model.eval()
