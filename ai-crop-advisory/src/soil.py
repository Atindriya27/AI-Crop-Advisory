from .config import LOCATION, SOIL_DEFAULTS

RANGES = {"nitrogen": (0, 300), "phosphorus": (0, 150), "potassium": (0, 300), "ph": (3.0, 10.0)}

def defaults(location=LOCATION):
    return dict(SOIL_DEFAULTS[location])

def validate(values):
    clean = {}
    for key, (low, high) in RANGES.items():
        if key not in values:
            raise ValueError(f"Missing soil value: {key}")
        value = float(values[key])
        if not low <= value <= high:
            raise ValueError(f"{key} must be between {low} and {high}.")
        clean[key] = value
    return clean
