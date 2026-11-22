import pandas as pd
import src.validation as validation

def test_validation_runner_uses_real_scenario_and_compares_outputs(tmp_path, monkeypatch):
    scenarios = pd.DataFrame([{
        "date": "2025-06-10", "crop": "Rice", "growth_stage": "Flowering",
        "soil_n": 80, "soil_p": 40, "soil_k": 45, "soil_ph": 6.7,
        "expected_top_crop": "rice", "expected_irrigation": "delay",
        "expected_pest_risk": "moderate", "expected_source": "ICAR advisory"
    }])
    scenario_path, result_path = tmp_path / "scenarios.csv", tmp_path / "results.csv"
    scenarios.to_csv(scenario_path, index=False)
    monkeypatch.setattr(validation, "SCENARIOS", scenario_path)
    monkeypatch.setattr(validation, "RESULTS", result_path)
    monkeypatch.setattr(validation, "fetch_historical_weather", lambda *a: {
        "date":"20250610", "temperature":28, "humidity":76, "rainfall":2,
        "wind":1, "solar":20, "status":"Historical NASA POWER observation"
    })
    monkeypatch.setattr(validation, "run_advisory", lambda context: {
        "crop_suitability":{"crop":"rice"},
        "irrigation":{"category":"delay"}, "pest_risk":{"level":"Moderate"},
        "final_advice":"Delay and monitor."
    })
    result = validation.run_validation()
    assert bool(result.loc[0, "match"]) is True
    assert validation.score(result) == 1.0
    assert result_path.exists()

def test_validation_target_requires_ten_scenarios():
    assert validation.meets_target(pd.DataFrame({"match":[True]*8+[False]*2}))
    assert not validation.meets_target(pd.DataFrame({"match":[True]*8+[False]}))
