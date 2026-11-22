import json
import joblib
import pandas as pd
from .config import FEATURES, MODEL_PATH, METADATA_PATH

class ModelUnavailable(RuntimeError):
    pass

def predict(soil, weather, selected_crop=None):
    if not MODEL_PATH.exists():
        raise ModelUnavailable("Crop suitability model is unavailable. Supply data/raw/Crop_recommendation.csv and run python -m src.train_model.")
    model = joblib.load(MODEL_PATH)
    row = {"N": soil["nitrogen"], "P": soil["phosphorus"], "K": soil["potassium"],
           "temperature": weather["temperature"], "humidity": weather["humidity"],
           "ph": soil["ph"]}
    probabilities = model.predict_proba(pd.DataFrame([[row[k] for k in FEATURES]], columns=FEATURES))[0]
    index = probabilities.argmax()
    distribution = dict(zip(model.classes_.tolist(), probabilities.tolist()))
    selected_key = str(selected_crop).lower() if selected_crop else None
    selected_score = distribution.get(selected_key) if selected_key else None
    selected_rank = (1 + sum(score > selected_score for score in distribution.values())) if selected_score is not None else None
    training_ranges = (metadata() or {}).get("feature_ranges", {})
    out_of_range = []
    for feature, value in row.items():
        limits = training_ranges.get(feature)
        if limits and not limits["min"] <= float(value) <= limits["max"]:
            out_of_range.append({"feature": feature, "value": float(value),
                                 "min": float(limits["min"]), "max": float(limits["max"])})
    return {"crop": str(model.classes_[index]), "confidence": float(probabilities[index]),
            "selected_crop": selected_key, "selected_crop_score": selected_score,
            "selected_crop_rank": selected_rank, "candidate_count": len(distribution),
            "probabilities": distribution, "input_out_of_range": out_of_range}

def metadata():
    return json.loads(METADATA_PATH.read_text(encoding="utf-8")) if METADATA_PATH.exists() else None
