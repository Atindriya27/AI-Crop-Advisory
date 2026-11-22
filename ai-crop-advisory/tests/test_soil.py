import pytest
from src.soil import defaults, validate

def test_defaults_are_valid():
    assert validate(defaults())["ph"] == 7.2

def test_reject_impossible_ph():
    values = defaults(); values["ph"] = 12
    with pytest.raises(ValueError): validate(values)
