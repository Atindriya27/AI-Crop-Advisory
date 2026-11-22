import pandas as pd
from .config import FEATURES, SUPPORTED_CROPS

ALIASES = {"label": "label", "N": "N", "P": "P", "K": "K", "temperature": "temperature", "humidity": "humidity", "ph": "ph", "rainfall": "rainfall"}

def load_dataset(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    required = set(FEATURES + ["label"])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    df = df[FEATURES + ["label"]].dropna()
    df["label"] = df["label"].astype(str).str.strip().str.lower()
    required_crops = {crop.lower() for crop in SUPPORTED_CROPS}
    if not set(df.label).issuperset(required_crops):
        missing_crops = sorted(required_crops - set(df.label))
        raise ValueError(f"Dataset is missing required crop classes: {', '.join(missing_crops)}")
    # Restrict the trained classifier to the three pilot labels so its output
    # ranks only crops the app can actually advise on.
    return df[df.label.isin(required_crops)].reset_index(drop=True)
