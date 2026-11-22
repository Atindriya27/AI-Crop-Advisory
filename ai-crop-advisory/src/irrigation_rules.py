from .config import IRRIGATION_RULES


def _stage_guidance(crop, stage):
    if crop == "Rice":
        return "Check the water level in the field. Add water only if it is needed."
    if crop == "Maize":
        return "Check the soil near the roots. Water if it is dry."
    if crop == "Cotton":
        return "Check the soil near the roots. Water if it is dry, and let extra water drain away."
    return "Check the soil before watering."


def _observed_moisture_advice(crop, stage, field_moisture):
    critical = stage in IRRIGATION_RULES["crop_stage_priority"].get(crop, [])
    if field_moisture == "Water standing":
        action = ("Do not add water now. Check the water level in the rice field."
                  if crop == "Rice" else "Wait before watering. Check that extra water can drain away.")
        return {"action": action, "category": "delay", "priority": "Monitor",
                "reason": "You reported standing water. Check the field again after the water level changes."}
    if field_moisture == "Dry":
        action = _dry_field_action(crop, stage)
        return {"action": action, "category": "recommended", "priority": "Monitor" if critical else "Urgent action",
                "reason": ("You reported dry soil. Check near the roots and follow your usual crop watering schedule."
                           + (" Check the field again soon because this is an important growth stage." if critical else ""))}
    if field_moisture == "Moist":
        action = ("No need to add water now. Check the rice field again before the next watering."
                  if crop == "Rice" else "No need to water now. Check the soil again before the next watering.")
        return {"action": action, "category": "not currently necessary", "priority": "Normal",
                "reason": "You reported that the soil is moist. Check it again before the next watering or after a change in weather."}
    return None


def recommend(crop, stage, weather, field_moisture="Not checked"):
    if not weather or weather.get("status") == "Unavailable":
        observed = _observed_moisture_advice(crop, stage, field_moisture)
        if observed:
            observed["reason"] += " Weather data is unavailable, so this advice uses only your field check."
            return observed
        return {"action": "Weather data is unavailable", "category": "unknown", "priority": "Monitor", "reason": "Check the soil and follow your usual crop watering schedule."}
    rain = float(weather.get("rainfall", 0) or 0)
    forecast = weather.get("forecast_rainfall")
    forecast = float(forecast) if forecast is not None else None
    temp = float(weather.get("temperature", 0))
    critical = stage in IRRIGATION_RULES["crop_stage_priority"].get(crop, [])
    waterlogging_sensitive = stage in IRRIGATION_RULES.get("waterlogging_sensitive_stages", {}).get(crop, [])
    if waterlogging_sensitive and rain >= IRRIGATION_RULES["rain_recent_mm"]:
        return {"action": "Wait before watering. Check that extra water can drain away.", "category": "delay", "priority": "Monitor",
                "reason": f"It rained {rain:.1f} mm in the past week. Cotton does not grow well in standing water, so check the field before watering."}
    if forecast is not None and forecast >= IRRIGATION_RULES["heavy_forecast_mm"]:
        return {"action": "Wait for the expected rain, then check the field before watering", "category": "delay", "priority": "Urgent action", "reason": f"About {forecast:.1f} mm of rain is expected. Check the field after it rains."}
    observed = _observed_moisture_advice(crop, stage, field_moisture)
    if observed:
        return observed
    if rain >= IRRIGATION_RULES["rain_recent_mm"]:
        return {"action": "Check the soil before watering", "category": "delay", "priority": "Normal", "reason": f"It rained {rain:.1f} mm in the past week. Check whether the soil is still dry before watering."}
    if forecast is not None and forecast >= IRRIGATION_RULES["rain_forecast_mm"]:
        return {"action": "Consider waiting for the expected rain", "category": "delay", "priority": "Monitor", "reason": f"About {forecast:.1f} mm of rain is expected. Check the soil afterward."}
    if (rain < IRRIGATION_RULES["low_rain_7d_mm"] and temp >= IRRIGATION_RULES["hot_celsius"]) or critical:
        action = _stage_guidance(crop, stage)
        return {"action": action, "category": "recommended", "priority": "Monitor" if critical else "Urgent action",
                "reason": ("There has been little rain and the weather is warm. "
                           + ("This is an important growth stage, so check the field soon. " if critical else "")
                           + "Check the soil before watering.")}
    return {"action": _stage_guidance(crop, stage), "category": "not currently necessary", "priority": "Normal", "reason": "The weather alone does not show that watering is needed. Check the field before changing your schedule."}


def _dry_field_action(crop, stage):
    if crop == "Rice":
        return "The field is dry. Add water according to your usual rice schedule."
    if crop == "Maize":
        return "The soil is dry. Water the maize according to your usual schedule."
    if crop == "Cotton":
        return "The soil is dry. Water the cotton according to your usual schedule."
    return "The soil is dry. Water according to your usual crop schedule."
