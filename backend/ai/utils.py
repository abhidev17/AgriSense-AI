import json
from pathlib import Path
from sklearn.model_selection import train_test_split


SUPPORTED_CROPS = {
    "Apple",
    "Cherry_(including_sour)",
    "Corn_(maize)",
    "Grape",
    "Peach",
    "Pepper,_bell",
    "Potato",
    "Soybean",
    "Strawberry",
    "Tomato",
}


def get_crop_name(folder_name: str) -> str:
    return folder_name.split("___")[0]


def load_crop_dataset(dataset_root):
    dataset_root = Path(dataset_root)

    image_paths = []
    labels = []

    crop_to_idx = {}

    for folder in sorted(dataset_root.iterdir()):

        if not folder.is_dir():
            continue

        crop = get_crop_name(folder.name)

        if crop not in SUPPORTED_CROPS:
            continue

        if crop not in crop_to_idx:
            crop_to_idx[crop] = len(crop_to_idx)

        label = crop_to_idx[crop]

        for img in folder.glob("*"):
            if img.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                image_paths.append(str(img))
                labels.append(label)

    train_x, val_x, train_y, val_y = train_test_split(
        image_paths,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    return (
        train_x,
        val_x,
        train_y,
        val_y,
        crop_to_idx,
    )


def load_disease_dataset(dataset_root):
    dataset_root = Path(dataset_root)

    image_paths = []
    labels = []

    disease_to_idx = {}

    for folder in sorted(dataset_root.iterdir()):

        if not folder.is_dir():
            continue

        crop = get_crop_name(folder.name)

        if crop not in SUPPORTED_CROPS:
            continue

        disease = folder.name

        if disease not in disease_to_idx:
            disease_to_idx[disease] = len(disease_to_idx)

        label = disease_to_idx[disease]

        for img in folder.glob("*"):
            if img.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                image_paths.append(str(img))
                labels.append(label)

    train_x, val_x, train_y, val_y = train_test_split(
        image_paths,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    return (
        train_x,
        val_x,
        train_y,
        val_y,
        disease_to_idx,
    )


def save_classes(path, crop_classes, disease_classes):
    data = {
        "crop_classes": crop_classes,
        "disease_classes": disease_classes,
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=4)