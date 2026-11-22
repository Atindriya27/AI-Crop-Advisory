from src.irrigation_rules import recommend

def test_recent_rain_prompts_field_moisture_check():
    r = recommend("Maize", "Vegetative", {"status":"Live", "rainfall":20, "temperature":25})
    assert "soil moisture" in r["action"].lower()

def test_hot_dry_critical_stage_raises_monitoring():
    r = recommend("Maize", "Tasseling", {"status":"Live", "rainfall":0, "temperature":35})
    assert r["priority"] in ("Urgent action", "Monitor")

def test_rice_stage_names_supported():
    r = recommend("Rice", "Flowering", {"status":"Live", "rainfall":0, "temperature":28})
    assert "water" in r["reason"].lower()

def test_icar_critical_stage_for_rice_is_prioritized():
    r = recommend("Rice", "Panicle initiation", {"status":"Live", "rainfall":0, "temperature":25})
    assert r["priority"] == "Monitor"
    assert "ICAR" in r["reason"]

def test_cotton_seedling_after_rain_checks_drainage():
    r = recommend("Cotton", "Seedling", {"status":"Live", "rainfall":20, "temperature":25})
    assert "drainage" in r["action"].lower()
    assert "water stagnation" in r["reason"].lower()
