"""Historical validation with actual dated NASA POWER records and supplied expected guidance."""
import json
import pandas as pd
from .config import ROOT, SUPPORTED_CROPS, LOCATION
from .soil import defaults, validate as validate_soil
from .weather import fetch_historical_weather
from .advisory_engine import AdvisoryContext, run as run_advisory

SCENARIOS = ROOT / "validation" / "past_scenarios.csv"
RESULTS = ROOT / "validation" / "validation_results.csv"
REQUIRED = ["date", "crop", "growth_stage", "expected_top_crop", "expected_irrigation", "expected_pest_risk", "expected_source"]

def load_scenarios():
    return pd.read_csv(SCENARIOS)

def _text(row, key):
    value = row.get(key)
    return None if pd.isna(value) or not str(value).strip() else str(value).strip()

def run_validation(location=LOCATION):
    scenarios = load_scenarios()
    if scenarios.empty:
        raise ValueError("Add dated scenarios and independently reviewed expected guidance to past_scenarios.csv first.")
    missing_columns = sorted(set(REQUIRED) - set(scenarios.columns))
    if missing_columns:
        raise ValueError(f"Scenario file is missing columns: {', '.join(missing_columns)}")
    results = []
    for _, row in scenarios.iterrows():
        record = row.to_dict()
        try:
            crop = _text(row, "crop").title()
            expected_top = _text(row, "expected_top_crop").lower()
            expected_irrigation = _text(row, "expected_irrigation").lower()
            expected_pest = _text(row, "expected_pest_risk").lower()
            source = _text(row, "expected_source")
            if crop not in SUPPORTED_CROPS:
                raise ValueError(f"Unsupported crop {crop}; use one of {', '.join(SUPPORTED_CROPS)}.")
            if not all((expected_top, expected_irrigation, expected_pest, source)):
                raise ValueError("Expected crop, irrigation category, pest level, and guidance source must be filled before scoring.")
            if expected_top not in {c.lower() for c in SUPPORTED_CROPS}:
                raise ValueError("expected_top_crop must be Rice, Maize, or Cotton.")
            if expected_irrigation not in {"required", "recommended", "delay", "not currently necessary"}:
                raise ValueError("expected_irrigation must be Required, Recommended, Delay, or Not currently necessary.")
            if expected_pest not in {"low", "moderate", "high"}:
                raise ValueError("expected_pest_risk must be Low, Moderate, or High.")
            historical_weather = fetch_historical_weather(location, _text(row, "date"))
            soil_input = {"nitrogen": row.get("soil_n"), "phosphorus": row.get("soil_p"),
                          "potassium": row.get("soil_k"), "ph": row.get("soil_ph")}
            if any(pd.isna(v) for v in soil_input.values()):
                soil = {k: defaults(location)[k] for k in ("nitrogen", "phosphorus", "potassium", "ph")}
                soil_source = "configured district defaults"
            else:
                soil = validate_soil(soil_input)
                soil_source = "scenario soil values"
            context = AdvisoryContext(location, crop, _text(row, "growth_stage"), soil, historical_weather, soil_source)
            advisory = run_advisory(context)
            model = advisory.get("crop_suitability") or {}
            actual_top = str(model.get("crop", "")).lower()
            actual_irrigation = advisory["irrigation"].get("category", "unknown")
            actual_pest = advisory["pest_risk"]["level"].lower()
            comparisons = [actual_top == expected_top, actual_irrigation == expected_irrigation, actual_pest == expected_pest]
            record.update({"weather_date_used": historical_weather["date"], "weather_json": json.dumps(historical_weather),
                           "soil_source_used": soil_source, "actual_top_crop": actual_top,
                           "actual_irrigation": actual_irrigation, "actual_pest_risk": actual_pest,
                           "actual_advice": advisory["final_advice"], "match": all(comparisons), "error": ""})
        except Exception as exc:
            record.update({"actual_top_crop": "", "actual_irrigation": "", "actual_pest_risk": "",
                           "actual_advice": "", "match": None, "error": str(exc)})
        results.append(record)
    frame = pd.DataFrame(results)
    frame.to_csv(RESULTS, index=False)
    return frame

def score(results):
    if "match" not in results or len(results) == 0:
        return None
    valid = results["match"].dropna()
    return float(valid.astype(bool).mean()) if len(valid) else None

def meets_target(results):
    if "match" not in results:
        return False
    valid = results["match"].dropna().astype(bool)
    return len(valid) >= 10 and int(valid.sum()) >= 8
