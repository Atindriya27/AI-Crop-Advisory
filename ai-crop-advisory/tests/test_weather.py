from src.weather import _parse

def test_parse_latest_complete_day():
    parameters = {key: {"20260101": 1, "20260102": value} for key, value in {"T2M":25,"RH2M":70,"PRECTOTCORR":2,"WS2M":3,"ALLSKY_SFC_SW_DWN":20}.items()}
    result = _parse({"properties":{"parameter":parameters}})
    assert result["date"] == "20260102"
    assert result["temperature"] == 25

def test_parse_rejects_missing_values():
    import pytest
    with pytest.raises(ValueError): _parse({"properties":{"parameter":{k:{"20260101":-999} for k in ("T2M","RH2M","PRECTOTCORR","WS2M","ALLSKY_SFC_SW_DWN")}}})
