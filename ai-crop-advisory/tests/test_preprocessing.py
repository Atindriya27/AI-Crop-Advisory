import pandas as pd
from src.preprocessing import load_dataset

def test_training_data_is_filtered_to_three_pilot_crops(tmp_path):
    rows = []
    for label in ("rice", "maize", "cotton", "apple"):
        rows.append({"N": 50, "P": 40, "K": 30, "temperature": 25, "humidity": 70, "ph": 6.5, "rainfall": 80, "label": label})
    path = tmp_path / "crops.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    data = load_dataset(path)
    assert set(data.label) == {"rice", "maize", "cotton"}
    assert len(data) == 3
