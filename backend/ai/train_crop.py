import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

from dataset import PlantVillageDataset
from utils import load_crop_dataset

# =====================================================
# Configuration
# =====================================================

DATASET_PATH = "../datasets/PlantVillage"
MODEL_SAVE_PATH = "../models/crop_model.pth"
CLASS_FILE = "../models/classes.json"

BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 1e-4

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)

# =====================================================
# Load Dataset
# =====================================================

train_x, val_x, train_y, val_y, crop_classes = load_crop_dataset(
    DATASET_PATH
)

# Fast generation mode for CI/testing
QUICK_GEN = True
if QUICK_GEN:
    train_x = train_x[:64]
    train_y = train_y[:64]
    val_x = val_x[:32]
    val_y = val_y[:32]
    EPOCHS = 1


train_dataset = PlantVillageDataset(
    train_x,
    train_y,
    train=True
)

val_dataset = PlantVillageDataset(
    val_x,
    val_y,
    train=False
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available(),
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available(),
)

# =====================================================
# Model
# =====================================================

weights = EfficientNet_B0_Weights.DEFAULT

model = efficientnet_b0(weights=weights)

num_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    num_features,
    len(crop_classes)
)

model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

# =====================================================
# Training
# =====================================================

best_accuracy = 0.0

for epoch in range(EPOCHS):

    model.train()

    running_loss = 0.0

    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    # ================= Validation =================

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)

            correct += (predicted == labels).sum().item()

    accuracy = (correct / total) * 100

    print(
        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Loss: {running_loss/len(train_loader):.4f} "
        f"Validation Accuracy: {accuracy:.2f}%"
    )

    if accuracy > best_accuracy:

        best_accuracy = accuracy

        Path("../models").mkdir(exist_ok=True)

        torch.save(model.state_dict(), MODEL_SAVE_PATH)

        print("Best model saved.")

# =====================================================
# Save Crop Classes
# =====================================================

Path("../models").mkdir(exist_ok=True)

if Path(CLASS_FILE).exists():

    with open(CLASS_FILE, "r") as f:
        data = json.load(f)

else:
    data = {}

data["crop_classes"] = crop_classes

with open(CLASS_FILE, "w") as f:
    json.dump(data, f, indent=4)

print("\n===================================")
print("Crop Training Completed Successfully")
print(f"Best Validation Accuracy : {best_accuracy:.2f}%")
print(f"Model Saved : {MODEL_SAVE_PATH}")
print("===================================")
