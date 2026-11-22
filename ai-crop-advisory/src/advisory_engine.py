from dataclasses import dataclass, asdict
from .crop_predictor import predict
from .irrigation_rules import recommend
from .pest_rules import assess

@dataclass
class AdvisoryContext:
    location: str
    crop: str
    growth_stage: str
    soil: dict
    weather: dict
    soil_source: str = ""
    demo: bool = False
    field_moisture: str = "Not checked"

def run(context):
    try:
        crop_result = predict(context.soil, context.weather, context.crop)
        model_error = None
    except Exception as exc:
        crop_result, model_error = None, str(exc)
    irrigation = recommend(context.crop, context.growth_stage, context.weather, context.field_moisture)
    pest = assess(context.crop, context.growth_stage, context.weather, context.field_moisture)
    actions = []
    if crop_result:
        if crop_result.get("input_out_of_range"):
            actions.append("Some soil or weather inputs are outside the model's training ranges; its crop comparison is not reliable for these inputs.")
        elif crop_result["confidence"] < .55:
            actions.append("The crop comparison is uncertain; review the soil and field conditions with an agricultural expert before making a crop decision.")
        elif crop_result["crop"] == context.crop.lower():
            actions.append(f"{context.crop} is the model's strongest relative match among Rice, Maize, and Cotton for these inputs.")
        else:
            actions.append(f"Among the three crops, the model's strongest relative match is {crop_result['crop'].title()}, while you selected {context.crop}; compare both before planting.")
    else:
        actions.append("Crop suitability could not be assessed because the model is unavailable or weather inputs are incomplete.")
    actions.append(irrigation["action"] + ".")
    if pest["level"] in ("High", "Moderate"):
        actions.append(f"Pest risk is {pest['level'].lower()}; {pest['action'].lower()}. This is a risk alert, not a diagnosis.")
    elif pest["level"] == "Low":
        actions.append(f"Pest risk is low under the current weather; {pest['action'].lower()} as part of routine field checks.")
    else:
        actions.append("Pest risk could not be assessed from the available weather; monitor the field and retry when weather data is available.")
    result = {"context": asdict(context), "crop_suitability": crop_result, "model_error": model_error,
              "irrigation": irrigation, "pest_risk": pest, "final_advice": " ".join(actions),
              "disclaimer": "This advisory is decision support and does not replace certified agricultural or expert advice."}
    return result
