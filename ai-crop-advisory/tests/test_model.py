import pytest
from src.crop_predictor import predict, ModelUnavailable
from src.soil import defaults

def test_missing_model_is_reported():
    from src.config import MODEL_PATH
    if MODEL_PATH.exists(): pytest.skip("trained model is present")
    with pytest.raises(ModelUnavailable): predict(defaults(), {"temperature":25,"humidity":70,"rainfall":2})
