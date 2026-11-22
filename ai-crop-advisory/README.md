# CropWise — AI Crop Advisory for Smallholder Farmers

CropWise is a Streamlit decision-support MVP for a **Bareilly, Uttar Pradesh** pilot. It combines farmer-entered information, daily weather from NASA POWER, a three-crop Random Forest comparison, separate irrigation and pest-risk rules, and a local advisory history.

It is a prototype for learning and demonstration. It is not a certified agronomist, a yield predictor, or a guarantee that a crop will succeed.

## What the app does

### Farmer inputs

- Pilot location: Bareilly, Uttar Pradesh (the location is currently fixed to this pilot).
- Crop: Rice, Maize, or Cotton.
- Growth stage: the available stage choices change with the selected crop.
- Soil nutrients and pH: use provisional defaults or enter measured N, P, K, and pH values.
- Field condition: report **Not checked**, **Dry**, **Moist**, or **Water standing** using a visual field check.
- Weather date: use the latest available observation or select a past date for a historical NASA POWER observation.
- Demo mode: generate clearly labelled simulated weather for one of three sample cases.

N, P, K, and pH are model inputs for crop comparison. The separate field-condition choice informs irrigation and pest guidance; it is a farmer observation, not a sensor measurement. If it is left as **Not checked**, the rule systems use the available weather and crop stage.

### Weather

- Requests daily temperature, relative humidity, precipitation, wind, and solar data from the NASA POWER daily point API for Bareilly.
- Uses the latest complete observation and sums precipitation across the latest seven available daily records.
- Saves the latest successful live response in `data/weather_cache.json` and uses it when a later live request fails.
- Historical date mode requests an observation for the selected date. It does not silently substitute cached or current weather if that date is unavailable.
- Shows the weather values and the source/status used by the advisory.

### Crop comparison model

- Trains a Random Forest using dataset rows labelled Rice, Maize, and Cotton.
- Uses N, P, K, temperature, humidity, and pH. It excludes the dataset rainfall field because its time period is not directly comparable to NASA's recent seven-day rainfall total.
- Compares the selected crop with the other two pilot crops and displays a relative score, rank, top model match, and class-score chart.
- Flags inputs outside the ranges observed in the training data.
- The Model Performance page displays held-out accuracy, weighted precision/recall/F1, five-fold cross-validation, a confusion matrix, and feature importance when model metadata is present.

The displayed score is a model class score, **not** a probability of crop success, yield, or field suitability. The model predicts the best dataset label from its inputs; the farmer's selected crop is separately compared against that result.

### Irrigation and pest guidance

- The irrigation rule uses crop, growth stage, field condition, recent rainfall, temperature, and forecast rain when a forecast value is available.
- The pest rule uses crop, growth stage, field condition, temperature, humidity, and recent rainfall.
- Crop-specific scouting instructions include checks such as rice leaves and plant bases, the folded centre leaves of young maize, and cotton flowers or green bolls.
- The pest result is a broad risk warning, not pest identification or disease diagnosis.
- Rule outputs are templates and can be read even if the crop model is unavailable.
- The final advisory combines the model comparison, irrigation action, and pest check in plain language.

### Other app pages

- **Dashboard / AI Advisory:** enter farm information, request advice, and view the result.
- **Weather:** inspect the weather record used for the most recent result.
- **Soil:** review soil values and their stated source.
- **Model Performance:** inspect available model evaluation metrics and charts.
- **Validation:** run dated scenarios against the expected guidance supplied in a CSV.
- **Advisory History:** inspect locally saved checks.
- **About:** view the project's purpose, sources, and limitations.

### Technologies

- Python and Streamlit for the app and interface.
- pandas for CSV and scenario data; scikit-learn and joblib for the Random Forest model and saved model artifact.
- requests for NASA POWER calls; SQLite for local advisory history.
- pytest for the automated test suite.

## How the pipeline works

```text
Crop + stage + soil values + field condition
                      │
          NASA POWER daily weather
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
 Random Forest crop         Irrigation rules
   comparison               Pest-risk rules
          └───────────┬───────────┘
                      ▼
       Plain-language advisory + SQLite history
```

The model and the irrigation/pest rules are separate. The model compares crop labels; the rules provide field actions. The advisory text is generated from deterministic Python templates; it does not require a paid AI service or call an LLM.

## Data and model details

The training file is expected at `data/raw/Crop_recommendation.csv`. Required columns are `N`, `P`, `K`, `temperature`, `humidity`, `ph`, and `label`. The loader drops incomplete rows, normalizes labels, requires all three pilot crops, and filters out other crop labels.

The current model metadata describes **300 rows** across the three selected labels and reports **100% accuracy** on an 80/20 stratified holdout and **100% mean accuracy** across five stratified folds. These are internal results on the same small public dataset, not independent tests. The dataset may be easy to separate, and the model has not been validated against Bareilly farms. Do not present these metrics as field accuracy.

Rainfall from the crop dataset is not included in the classifier. NASA's seven-day total is used by the advisory rules instead. The model's range checks only tell whether an input falls inside the training data's observed range; they are not agronomic safety limits.

## Irrigation rule settings

Editable prototype settings are in `config/irrigation_rules.json`:

- Recent rainfall trigger: 12 mm over the latest available seven-day period.
- Forecast rain: consider waiting at 10 mm; use the stronger delay message at 25 mm.
- Low-rain/hot-weather prompt: less than 8 mm over seven days and temperature at least 32°C.
- Crop stages that prompt closer irrigation checks are listed by crop in the same file.
- Early cotton stages receive an extra water-drainage check after sufficient rain.

These cutoffs are **prototype triggers**, not official ICAR irrigation thresholds, prescribed water amounts, or a locally calibrated schedule. NASA POWER live data currently provides observations, not a short-term forecast, so forecast branches are used only if a forecast value is available (for example, in demo or other supplied weather data). Check actual field moisture and follow local agricultural guidance.

## Install and run

Python 3.10 or newer is recommended. From the project directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

To retrain the model after providing the source dataset at `data/raw/Crop_recommendation.csv`:

```powershell
python -m src.train_model
```

The repository currently includes a model artifact and training CSV. If the model artifact is absent, the advisory still runs its rule-based guidance and indicates crop comparison is unavailable. To run the test suite:

```powershell
python -m pytest -q
```

## Historical validation

`validation/past_scenarios.csv` is currently an **empty schema template**. The app does not yet contain the ten sourced historical scenarios discussed during planning. Add dated rows with crop, growth stage, expected top crop, expected irrigation category, expected pest-risk level, and a source for the expected guidance. Optional soil fields can be left blank to use the configured provisional values.

The Validation page fetches NASA POWER weather for each date, runs the crop model and rule systems, compares the top crop, irrigation category, and pest-risk level with the supplied expected values, and writes results to `validation/validation_results.csv`. A scenario counts as a match only when all three comparisons match. Missing expected guidance, API failures, or incomplete scenarios are not counted. The 8-of-10 target is shown only after ten scenarios have valid results; it is a project target, not proof of agronomic correctness.

The dashboard's historical date control is separate from the validation CSV workflow. Historical scenario rows can include N, P, K, and pH, but cannot currently include a field-moisture observation; validation therefore uses **Not checked** for that input. Neither workflow includes an official Soil Health Card lookup or a soil-moisture sensor reading.

## Shortcomings and limits

- **Soil defaults are provisional.** `data/soil_defaults.json` is not verified district Soil Health Card data. The app has no Soil Health Card API or official district aggregation yet.
- **Field condition is self-reported.** Dry/moist/water-standing choices are visual categories, not readings from a moisture sensor or laboratory test. A field may vary across plots.
- **No direct irrigation measurement.** There is no soil texture, root-zone sensor, water-table measurement, irrigation history, or crop water-balance calculation. Rule thresholds need review by local agricultural experts.
- **Weather coverage is limited.** NASA POWER is gridded daily observation data, not hyperlocal farm-station data or a short-term forecast. Rain totals and timing may not match an individual plot. Cached data can be old; check its source/status and observation date.
- **Pest estimates are broad.** Rules do not use live pest surveillance, images, trap counts, observed symptoms, or district outbreak reports. They cannot identify a pest, diagnose a disease, or prescribe pesticide treatment. The risk level is based on broad weather signals; field condition can change the accompanying advice without changing the weather-based level.
- **Model evidence is preliminary.** The public crop dataset and the selected subset are not Bareilly field trials. The high internal metrics do not establish real-world accuracy. Scores are relative model outputs, not probabilities of success, yield estimates, or official suitability ratings.
- **Only three crops and one pilot location are supported.** Rice, Maize, and Cotton are the only classes. Bareilly is the only configured location; local varieties and management practices are not represented.
- **No economic or input planning.** The app does not estimate yield, cost, profit, seed variety, fertilizer dose, water volume, or pesticide treatment.
- **Hindi is incomplete.** The selector offers a Hindi preview, but the full interface, explanation, and advisory are not translated consistently.
- **Validation scenarios are not populated.** The empty CSV means the historical 8/10 target has not been demonstrated yet. Expected guidance must be independently sourced and checked.
- **No farmer evaluation yet.** There is no recorded user feedback, usability study, or field trial in this repository.
- **Local prototype only.** There are no user accounts, cloud synchronization, remote database, notifications, or production deployment configuration.
- **Local database security is basic.** SQLite history is stored in `advisory_history.sqlite3` without encryption or access control. Anyone with access to the project files may read it.
- **No personal identifiers are requested.** The app does not ask for names, phone numbers, Aadhaar, or financial details, but users should still protect the local project folder and database.

## Data storage and privacy

Each generated advisory is saved to the local SQLite database `advisory_history.sqlite3`. The record includes timestamp, location, selected crop and stage, soil inputs, weather, model result, irrigation/pest output, and final advice. The full payload also contains the farmer-reported field condition. The app does not request personal identifiers. Data is not encrypted, uploaded, or synchronized by this code.

## Project layout

```text
app.py                         Streamlit pages and farmer input flow
src/weather.py                 NASA POWER live and historical requests/cache
src/soil.py                    Soil defaults and numeric validation
src/preprocessing.py           Dataset loading and crop filtering
src/train_model.py             Random Forest training and evaluation metadata
src/crop_predictor.py          Crop scores and training-range checks
src/irrigation_rules.py        Crop/stage/weather/field-condition rules
src/pest_rules.py              Weather risk and crop/stage scouting guidance
src/advisory_engine.py         Combines results and creates final advice
src/validation.py              Historical scenario comparison
src/database.py                Local SQLite advisory history
config/irrigation_rules.json   Editable prototype thresholds and stage lists
data/raw/                      Crop training CSV
data/soil_defaults.json        Provisional soil defaults
data/weather_cache.json        Last successful live weather response
models/                        Trained model and evaluation metadata
validation/                    Scenario template and validation output
tests/                         Automated tests
translations/                   Partial English/Hindi text resources
```
