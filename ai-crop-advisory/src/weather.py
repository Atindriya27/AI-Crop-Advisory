"""NASA POWER daily observations with a recent 7-day rainfall total."""
from datetime import date, timedelta
import json
import logging
from pathlib import Path
import requests
from .config import COORDINATES, LOCATION, NASA_POWER_BASE_URL, ROOT, WEATHER_TIMEOUT_SECONDS

log = logging.getLogger(__name__)
CACHE_PATH = ROOT / "data" / "weather_cache.json"
PARAMS = ["T2M", "RH2M", "PRECTOTCORR", "WS2M", "ALLSKY_SFC_SW_DWN"]

def _cached():
    try:
        cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return cached if cached.get("weather_schema_version") == 2 else None
    except (OSError, ValueError):
        return None

def _parse(payload):
    parameters = payload["properties"]["parameter"]
    dates = sorted(set.intersection(*(set(parameters[k]) for k in PARAMS)))
    for day in reversed(dates):
        vals = {key: parameters[key][day] for key in PARAMS}
        if any(v is None or float(v) < -900 for v in vals.values()):
            continue
        end = dates.index(day)
        rain_dates = dates[max(0, end - 6):end + 1]
        rain_values = [float(parameters["PRECTOTCORR"][rain_day]) for rain_day in rain_dates]
        rain_values = [value for value in rain_values if value >= 0]
        rain_total = sum(rain_values)
        return {"date": day, "temperature": float(vals["T2M"]), "humidity": float(vals["RH2M"]),
                "rainfall": rain_total, "rainfall_7d": rain_total, "rainfall_days": len(rain_values),
                "daily_rainfall": float(vals["PRECTOTCORR"]), "wind": float(vals["WS2M"]),
                "solar": float(vals["ALLSKY_SFC_SW_DWN"]), "forecast_rainfall": None,
                "weather_schema_version": 2}
    raise ValueError("NASA POWER response has no complete daily record")

def fetch_weather(location=LOCATION, use_demo=False):
    if use_demo:
        return {"date": "SIMULATED DEMO", "temperature": 34.0, "humidity": 42.0, "rainfall": 0.5,
                "rainfall_7d": 0.5, "rainfall_days": 7, "daily_rainfall": 0.5,
                "wind": 2.1, "solar": 22.0, "forecast_rainfall": 0.0,
                "weather_schema_version": 2, "status": "Simulated demo"}
    coord = COORDINATES[location]
    params = {"parameters": ",".join(PARAMS), "community": "AG", "longitude": coord["longitude"],
              "latitude": coord["latitude"], "start": (date.today()-timedelta(days=16)).strftime("%Y%m%d"),
              "end": (date.today()-timedelta(days=1)).strftime("%Y%m%d"), "format": "JSON"}
    try:
        response = requests.get(NASA_POWER_BASE_URL, params=params, timeout=WEATHER_TIMEOUT_SECONDS)
        response.raise_for_status()
        result = _parse(response.json())
        result["status"] = "Live NASA POWER observations"
        CACHE_PATH.write_text(json.dumps(result), encoding="utf-8")
        return result
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        log.warning("NASA POWER request failed: %s", exc)
        cached = _cached()
        if cached:
            cached["status"] = "Cached weather (NASA POWER unavailable)"
            return cached
        return {"status": "Unavailable", "error": "Weather data is temporarily unavailable. Please try again later."}

def fetch_historical_weather(location, historical_date):
    """Fetch the dated NASA POWER record; never substitute live/cache data for validation."""
    target = date.fromisoformat(str(historical_date)[:10])
    coord = COORDINATES[location]
    params = {"parameters": ",".join(PARAMS), "community": "AG", "longitude": coord["longitude"],
              "latitude": coord["latitude"], "start": (target-timedelta(days=6)).strftime("%Y%m%d"),
              "end": target.strftime("%Y%m%d"), "format": "JSON"}
    response = requests.get(NASA_POWER_BASE_URL, params=params, timeout=WEATHER_TIMEOUT_SECONDS)
    response.raise_for_status()
    result = _parse(response.json())
    if result["date"] != target.strftime("%Y%m%d"):
        raise ValueError(f"NASA POWER has no complete record for {target.isoformat()}.")
    result["status"] = "Historical NASA POWER observation"
    return result
