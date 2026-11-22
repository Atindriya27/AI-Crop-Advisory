from src.advisory_engine import AdvisoryContext, run
from src.soil import defaults

def test_workflow_survives_missing_model():
    result = run(AdvisoryContext("Bareilly, Uttar Pradesh", "Maize", "Vegetative", defaults(), {"status":"Unavailable"}))
    assert result["crop_suitability"] is None
    assert result["pest_risk"]["level"] == "Unknown"
    assert result["final_advice"]

def test_demo_weather_advisory():
    result = run(AdvisoryContext("Bareilly, Uttar Pradesh", "Rice", "Flowering", defaults(), {"status":"Simulated demo", "temperature":29, "humidity":86, "rainfall":14, "forecast_rainfall":0}, demo=True))
    assert result["pest_risk"]["level"] == "High"
