from pathlib import Path
import json
import os
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_CROPS = ["Rice", "Maize", "Cotton"]
LOCATION = "Bareilly, Uttar Pradesh"
COORDINATES = {LOCATION: {"latitude": 28.3670, "longitude": 79.4304}}
SOIL_DEFAULTS_PATH = ROOT / "data" / "soil_defaults.json"
MODEL_PATH = ROOT / "models" / "crop_model.joblib"
METADATA_PATH = ROOT / "models" / "model_metadata.json"
DB_PATH = ROOT / "advisory_history.sqlite3"
NASA_POWER_BASE_URL = os.getenv("NASA_POWER_BASE_URL", "https://power.larc.nasa.gov/api/temporal/daily/point")
WEATHER_TIMEOUT_SECONDS = int(os.getenv("WEATHER_TIMEOUT_SECONDS", "12"))
# Seven-day rainfall remains an input to irrigation and pest rules, but is not
# comparable to the source dataset's rainfall period, so it is excluded from ML.
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph"]
DATASET_PATH = ROOT / "data" / "raw" / "Crop_recommendation.csv"

def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

SOIL_DEFAULTS = load_json(SOIL_DEFAULTS_PATH)
IRRIGATION_RULES = load_json(ROOT / "config" / "irrigation_rules.json")
