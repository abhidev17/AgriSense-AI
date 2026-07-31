import json
import os
import io
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0

# Resolve paths relative to this file
AI_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(AI_DIR), "models")
CROP_MODEL_PATH = os.path.join(MODELS_DIR, "crop_model.pth")
DISEASE_MODEL_PATH = os.path.join(MODELS_DIR, "disease_model.pth")
CLASSES_PATH = os.path.join(MODELS_DIR, "classes.json")

# Crop name mappings from API friendly names to PlantVillage prefix names
CROP_NAME_MAPPING = {
    "Tomato": "Tomato",
    "Potato": "Potato",
    "Bell Pepper": "Pepper,_bell",
    "Pepper": "Pepper,_bell",
    "Corn (Maize)": "Corn_(maize)",
    "Corn": "Corn_(maize)",
    "Apple": "Apple",
    "Cherry": "Cherry_(including_sour)",
    "Grape": "Grape",
    "Peach": "Peach",
    "Strawberry": "Strawberry",
    "Soybean": "Soybean"
}

# Global cache for lazy loading
_crop_model = None
_disease_model = None
_classes_data = None
_idx_to_crop = None
_idx_to_disease = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Preprocessing transforms (ImageNet normalization)
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def _load_classes():
    global _classes_data, _idx_to_crop, _idx_to_disease
    if _classes_data is not None:
        return _classes_data

    if not os.path.exists(CLASSES_PATH):
        raise FileNotFoundError(f"Classes configuration file not found at {CLASSES_PATH}")

    with open(CLASSES_PATH, "r") as f:
        _classes_data = json.load(f)

    # Invert the mappings to index -> name
    _idx_to_crop = {v: k for k, v in _classes_data["crop_classes"].items()}
    _idx_to_disease = {v: k for k, v in _classes_data["disease_classes"].items()}

    return _classes_data


def _load_crop_model():
    global _crop_model
    if _crop_model is not None:
        return _crop_model

    classes = _load_classes()
    num_classes = len(classes["crop_classes"])

    model = efficientnet_b0(weights=None)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, num_classes)

    if not os.path.exists(CROP_MODEL_PATH):
        raise FileNotFoundError(f"Crop model weights not found at {CROP_MODEL_PATH}")

    state_dict = torch.load(CROP_MODEL_PATH, map_location=_device)
    model.load_state_dict(state_dict)
    model.to(_device)
    model.eval()

    _crop_model = model
    return _crop_model


def _load_disease_model():
    global _disease_model
    if _disease_model is not None:
        return _disease_model

    classes = _load_classes()
    num_classes = len(classes["disease_classes"])

    model = efficientnet_b0(weights=None)
    num_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_features, num_classes)

    if not os.path.exists(DISEASE_MODEL_PATH):
        raise FileNotFoundError(f"Disease model weights not found at {DISEASE_MODEL_PATH}")

    state_dict = torch.load(DISEASE_MODEL_PATH, map_location=_device)
    model.load_state_dict(state_dict)
    model.to(_device)
    model.eval()

    _disease_model = model
    return _disease_model


def _load_image(image_input) -> Image.Image:
    if isinstance(image_input, bytes):
        return Image.open(io.BytesIO(image_input)).convert("RGB")
    elif isinstance(image_input, (str, os.PathLike)):
        return Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        return image_input
    else:
        raise ValueError("Unsupported image input type. Must be bytes, path string, or PIL Image.")


@torch.no_grad()
def predict_crop(image_path) -> tuple[str, float]:
    """
    Predict the crop class from the image.
    Returns:
        (crop_name, confidence)
    """
    model = _load_crop_model()
    _load_classes()

    image = _load_image(image_path)
    tensor = _transform(image).unsqueeze(0).to(_device)

    outputs = model(tensor)
    probs = torch.softmax(outputs, dim=1)[0]
    
    best_idx = probs.argmax().item()
    crop_name = _idx_to_crop[best_idx]
    confidence = probs[best_idx].item()

    return crop_name, confidence


@torch.no_grad()
def predict_disease(image_path, crop_name: str = None) -> tuple[str, float]:
    """
    Predict the disease class from the image.
    If crop_name is provided, filters predictions to classes belonging to that crop.
    Returns:
        (disease_name, confidence)
    """
    model = _load_disease_model()
    classes = _load_classes()

    image = _load_image(image_path)
    tensor = _transform(image).unsqueeze(0).to(_device)

    outputs = model(tensor)
    probs = torch.softmax(outputs, dim=1)[0]

    # Map the crop name to PlantVillage name prefix (e.g. Tomato -> Tomato)
    mapped_prefix = None
    if crop_name:
        mapped_prefix = CROP_NAME_MAPPING.get(crop_name, crop_name)

    # Filter classes by prefix
    if mapped_prefix:
        # Find indices of disease classes that match the crop prefix
        filtered_indices = []
        for class_name, idx in classes["disease_classes"].items():
            if class_name.startswith(mapped_prefix + "___"):
                filtered_indices.append(idx)

        if filtered_indices:
            # Gather probabilities for matching classes
            indices_tensor = torch.tensor(filtered_indices, device=_device)
            filtered_probs = probs[indices_tensor]
            
            # Normalize filtered probabilities
            sum_probs = filtered_probs.sum()
            if sum_probs > 0:
                normalized_probs = filtered_probs / sum_probs
            else:
                normalized_probs = filtered_probs

            best_filtered_idx = normalized_probs.argmax().item()
            actual_class_idx = filtered_indices[best_filtered_idx]
            
            full_class_name = _idx_to_disease[actual_class_idx]
            confidence = normalized_probs[best_filtered_idx].item()
            
            # Extract disease name (Tomato___Early_blight -> Early blight)
            disease_name = full_class_name.split("___")[1].replace("_", " ").title()
            return disease_name, confidence

    # Fallback to all classes if no crop filtering can be done
    best_idx = probs.argmax().item()
    full_class_name = _idx_to_disease[best_idx]
    confidence = probs[best_idx].item()

    disease_name = full_class_name.split("___")[1].replace("_", " ").title()
    return disease_name, confidence
