"""Photo-based crop disease detection with a local ONNX model.

Uses MobileNetV2 trained on PlantVillage (38 leaf classes):
onnx-community/mobilenet_v2_1.0_224-plant-disease-identification-ONNX

Inference runs locally through onnxruntime; no image leaves the machine.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps

import knowledge

MODEL_DIR = Path(__file__).resolve().parent / "assets" / "models" / "plant_disease"
MODEL_PATH = MODEL_DIR / "model.onnx"
CONFIG_PATH = MODEL_DIR / "config.json"

MODEL_NAME = "MobileNetV2 · PlantVillage"
MODEL_CLASSES = 38
MODEL_SOURCE = (
    "https://huggingface.co/onnx-community/"
    "mobilenet_v2_1.0_224-plant-disease-identification-ONNX"
)
INPUT_SIZE = 224
RESIZE_SHORTEST = 256
LOW_CONFIDENCE = 0.45

# PlantVillage label -> (app crop name, disease name or None when healthy)
LABEL_INFO: dict[str, tuple[str, str | None]] = {
    "Apple Scab": ("Apple", "Apple scab"),
    "Apple with Black Rot": ("Apple", "Black rot"),
    "Bell Pepper with Bacterial Spot": ("Bell Pepper", "Bacterial spot"),
    "Cedar Apple Rust": ("Apple", "Cedar apple rust"),
    "Cherry with Powdery Mildew": ("Cherry", "Powdery mildew"),
    "Corn (Maize) with Cercospora and Gray Leaf Spot": ("Maize", "Gray leaf spot"),
    "Corn (Maize) with Common Rust": ("Maize", "Common rust"),
    "Corn (Maize) with Northern Leaf Blight": ("Maize", "Northern leaf blight"),
    "Grape with Black Rot": ("Grapes", "Black rot"),
    "Grape with Esca (Black Measles)": ("Grapes", "Esca (black measles)"),
    "Grape with Isariopsis Leaf Spot": ("Grapes", "Isariopsis leaf spot"),
    "Healthy Apple": ("Apple", None),
    "Healthy Bell Pepper Plant": ("Bell Pepper", None),
    "Healthy Blueberry Plant": ("Blueberry", None),
    "Healthy Cherry Plant": ("Cherry", None),
    "Healthy Corn (Maize) Plant": ("Maize", None),
    "Healthy Grape Plant": ("Grapes", None),
    "Healthy Peach Plant": ("Peach", None),
    "Healthy Potato Plant": ("Potato", None),
    "Healthy Raspberry Plant": ("Raspberry", None),
    "Healthy Soybean Plant": ("Soybean", None),
    "Healthy Strawberry Plant": ("Strawberry", None),
    "Healthy Tomato Plant": ("Tomato", None),
    "Orange with Citrus Greening": ("Orange", "Citrus greening (HLB)"),
    "Peach with Bacterial Spot": ("Peach", "Bacterial spot"),
    "Potato with Early Blight": ("Potato", "Early blight"),
    "Potato with Late Blight": ("Potato", "Late blight"),
    "Squash with Powdery Mildew": ("Squash", "Powdery mildew"),
    "Strawberry with Leaf Scorch": ("Strawberry", "Leaf scorch"),
    "Tomato Mosaic Virus": ("Tomato", "Tomato mosaic virus"),
    "Tomato Yellow Leaf Curl Virus": ("Tomato", "Tomato leaf curl"),
    "Tomato with Bacterial Spot": ("Tomato", "Bacterial spot"),
    "Tomato with Early Blight": ("Tomato", "Early blight"),
    "Tomato with Late Blight": ("Tomato", "Late blight"),
    "Tomato with Leaf Mold": ("Tomato", "Leaf mold"),
    "Tomato with Septoria Leaf Spot": ("Tomato", "Septoria leaf spot"),
    "Tomato with Spider Mites or Two-spotted Spider Mite": ("Tomato", "Spider mites"),
    "Tomato with Target Spot": ("Tomato", "Target spot"),
}


def available() -> bool:
    return MODEL_PATH.exists() and CONFIG_PATH.exists()


@lru_cache(maxsize=1)
def _session() -> tuple[ort.InferenceSession, dict[int, str]]:
    if not available():
        raise FileNotFoundError(
            f"Photo model files are missing from {MODEL_DIR}."
        )
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    id2label = {int(i): name for i, name in config["id2label"].items()}
    session = ort.InferenceSession(
        str(MODEL_PATH), providers=["CPUExecutionProvider"]
    )
    return session, id2label


def preprocess(image: Image.Image) -> np.ndarray:
    image = ImageOps.exif_transpose(image).convert("RGB")
    width, height = image.size
    scale = RESIZE_SHORTEST / min(width, height)
    image = image.resize(
        (round(width * scale), round(height * scale)),
        Image.Resampling.BILINEAR,
    )
    width, height = image.size
    left = (width - INPUT_SIZE) // 2
    top = (height - INPUT_SIZE) // 2
    image = image.crop((left, top, left + INPUT_SIZE, top + INPUT_SIZE))
    array = np.asarray(image, dtype=np.float32) / 255.0
    array = (array - 0.5) / 0.5
    return np.ascontiguousarray(array.transpose(2, 0, 1)[None])


def _knowledge_entry(crop: str, disease: str | None) -> dict | None:
    if not disease:
        return None
    for entry in knowledge.diseases_for_crop(crop):
        if entry["name"].casefold() == disease.casefold():
            return entry
    return None


def predict(image: Image.Image, top_k: int = 3) -> list[dict]:
    session, id2label = _session()
    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: preprocess(image)})[0][0].astype(np.float64)
    logits -= logits.max()
    probabilities = np.exp(logits)
    probabilities /= probabilities.sum()

    market_crops = {entry["crop"] for entry in knowledge.DISEASES}
    results = []
    for index in probabilities.argsort()[-top_k:][::-1]:
        label = id2label[int(index)]
        crop, disease = LABEL_INFO.get(label, ("Unknown", None))
        results.append(
            {
                "label": label,
                "crop": crop,
                "disease": disease,
                "healthy": disease is None,
                "confidence": float(probabilities[index]),
                "knowledge": _knowledge_entry(crop, disease),
                "in_market": crop in market_crops,
            }
        )
    return results
