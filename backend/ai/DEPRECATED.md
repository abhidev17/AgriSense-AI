# DEPRECATED — CNN Training Pipeline

The custom PyTorch training pipeline in this directory is **no longer used** by
the AgriSense AI backend.

## What changed

Crop and disease classification is now handled entirely by **Gemini Vision**
via `app/services/gemini.py`.

## Why

| Old approach | New approach |
|---|---|
| PlantVillage CNN (crop_model.pth) | Gemini Vision API |
| PlantVillage CNN (disease_model.pth) | Gemini Vision API |
| 64-image quick-gen training | No training required |
| Separate leaf validation heuristic | Single Gemini Vision call |

## Files in this directory

These files are kept for reference and are **not imported** by the backend:

- `train_crop.py` — production crop trainer (EfficientNet-B0, AdamW, early stopping)
- `train_disease.py` — production disease trainer
- `trainer.py` — shared training engine
- `dataset.py` — PlantVillage dataset loader
- `inference.py` — PyTorch model inference (unused)
- `utils.py` — dataset loader utilities (unused)

## If you want to retrain anyway

```bash
cd backend/ai
python train_crop.py
python train_disease.py
```

Models would need to be plugged back into `app/services/gemini.py`
as a secondary confidence signal — not required for the current architecture.
