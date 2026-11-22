_CROP_STAGE_SCOUTING = {
    "Rice": {
        "early": {"Seedling", "Transplanting / establishment", "Vegetative"},
        "reproductive": {"Panicle initiation", "Flowering", "Grain filling"},
    },
    "Maize": {
        "whorl": {"Seedling", "Vegetative", "Pre-tasseling"},
        "reproductive": {"Tasseling", "Silking", "Grain filling"},
    },
    "Cotton": {
        "flowering": {"Squaring", "Flowering"},
        "boll": {"Boll formation"},
    },
}


def _scouting_action(crop, stage):
    """Give a crop- and stage-specific scouting action, never a diagnosis."""
    windows = _CROP_STAGE_SCOUTING.get(crop, {})
    if crop == "Rice":
        return "Check the leaves and the base of the plants for damage or insects"
    if crop == "Maize":
        if stage in windows.get("whorl", set()):
            return "Check the folded leaves at the center of the plants for small worms or fresh damage"
        return "Check the leaves and young cobs for fresh damage"
    if crop == "Cotton":
        if stage in windows.get("flowering", set()):
            return "Check the flowers for damage and look at nearby pest traps"
        if stage in windows.get("boll", set()):
            return "Check green cotton pods for holes or worms"
        return "Check under the leaves for insects or damage"
    return "Inspect the crop for fresh pest damage"


def assess(crop, stage, weather, field_moisture="Not checked"):
    if not weather or weather.get("status") == "Unavailable":
        reason = "Weather data is unavailable. Check the crop and try again when weather data returns."
        if field_moisture == "Water standing" and crop != "Rice":
            reason += " You reported standing water, so check that it can drain away."
        elif field_moisture == "Dry":
            reason += " You reported dry soil; check whether the crop also looks thirsty."
        return {"level": "Unknown", "reason": reason, "action": _scouting_action(crop, stage), "field_moisture": field_moisture}
    t, h, rain = (float(weather.get(k, 0) or 0) for k in ("temperature", "humidity", "rainfall"))
    warm = 22 <= t <= 34
    humid = h >= 75
    wet = rain >= 10
    score = int(warm) + int(humid) + int(wet)
    if score >= 3:
        level = "High"
    elif score == 2 or (humid and warm):
        level = "Moderate"
    else:
        level = "Low"
    factors = []
    if warm: factors.append("warm temperatures")
    if humid: factors.append("high humidity")
    if wet: factors.append("recent rainfall")
    scouting = _scouting_action(crop, stage)
    action = scouting
    soil_note = ""
    if field_moisture == "Water standing":
        if crop == "Rice":
            soil_note = " Standing water alone does not mean rice has a pest problem."
            action = "Check the leaves and plant bases for damage, and follow your usual rice water schedule"
        else:
            soil_note = " Standing water can harm roots. Check that it can drain away."
            action += "; check that extra water can drain away"
    elif field_moisture == "Dry":
        soil_note = " Dry soil may stress the crop, so check the plants as well as for pests."
        action += "; check whether the crop looks thirsty"
    elif field_moisture == "Moist":
        soil_note = " You reported moist soil; keep checking the crop for pests."
    if factors:
        reason = (", ".join(factors).capitalize()
                  + " may increase pest or disease risk. This is a warning, not a diagnosis. "
                  + f"At the {stage.lower()} stage, {scouting.lower()}." + soil_note)
    else:
        reason = ("The weather does not show strong signs of increased pest risk. "
                  + f"At this stage, keep checking the crop: {scouting.lower()}." + soil_note)
    return {"level": level, "reason": reason, "action": action, "field_moisture": field_moisture}
