from src.pest_rules import assess

def test_warm_humid_wet_is_high():
    assert assess("Rice", "Vegetative", {"status":"Live", "temperature":29, "humidity":85, "rainfall":14})["level"] == "High"

def test_cool_dry_is_low():
    assert assess("Maize", "Seedling", {"status":"Live", "temperature":12, "humidity":40, "rainfall":0})["level"] == "Low"
