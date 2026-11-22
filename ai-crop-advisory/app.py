import json
from datetime import date, timedelta

import streamlit as st

from src.advisory_engine import AdvisoryContext, run
from src.config import LOCATION, ROOT, SUPPORTED_CROPS
from src.crop_predictor import metadata
from src.database import get_record, history, initialize, save
from src.soil import defaults, validate
from src.validation import RESULTS, SCENARIOS, meets_target, run_validation, score as validation_score
from src.weather import fetch_historical_weather, fetch_weather

st.set_page_config(page_title="AI Crop Advisory", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")
initialize()

st.markdown("""
<style>
:root{color-scheme:light}
.stApp,[data-testid="stAppViewContainer"]{background:#eef6fb;color:#17334a}
.block-container{max-width:1390px;padding:0 2.4rem 3rem}
[data-testid="stHeader"]{display:none}
[data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,[data-testid="stAppViewContainer"] h3,[data-testid="stAppViewContainer"] h4,[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] .stMarkdown{color:#17334a}
[data-testid="stAppViewContainer"] .stCaption{color:#728399}
[data-testid="stSidebar"]{background:#173d2b;border-right:1px solid #24543a;min-width:260px}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#9db0c4!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#9db0c4!important}
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] label p{color:#d4dfeb!important}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label p{color:#e2ebf4!important}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div{background:#fffdf2!important;border:1px solid #8eaa80!important;min-height:42px;color:#172b40!important}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"]{color:#172b40!important;-webkit-text-fill-color:#172b40!important;opacity:1!important}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg{fill:#536a80!important}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg{fill:#536a80!important}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:.36rem .5rem;margin:.1rem 0}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#24543a}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#2b6841;border-radius:9px}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#fff!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{font-weight:550}
.brand{display:flex;align-items:center;gap:.65rem;color:#fff;font-size:1.24rem;font-weight:750;padding:.35rem .2rem 1.1rem}
.brand-mark{background:#398b45;border-radius:12px;width:40px;height:40px;display:inline-flex;align-items:center;justify-content:center;font-size:1.25rem;box-shadow:0 5px 16px #f0c34236}
.brand-accent{color:#f3cf58}
.nav-kicker{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:#d6c16b;font-weight:700;margin:1.1rem 0 .3rem}
.sidebar-region{border:1px solid #477456;background:#204b34;border-radius:10px;padding:.72rem .8rem;margin:.25rem 0 .6rem;color:#e6eff7!important}
.sidebar-region strong{display:block;color:#f2f7fb!important;font-size:.88rem}.sidebar-region span{display:block;color:#b8c9d9!important;font-size:.75rem;margin-top:.22rem}
.topbar{height:62px;background:#fff;border-bottom:1px solid #e5eaf0;display:flex;align-items:center;justify-content:space-between;margin:0 -2.4rem 2.15rem;padding:0 2.4rem;color:#718197;font-size:.9rem}
.crumb-current{color:#20364e;font-weight:700}.system-pill{color:#61758b}.system-dot{color:#12ad91;font-size:1rem;padding-right:.35rem}
.intro-row{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin-bottom:1.35rem}
.eyebrow{font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;color:#328547;font-weight:800;margin-bottom:.55rem}
.page-title{font-size:2rem;font-weight:760;letter-spacing:-.04em;margin:0;color:#173d2b}
.page-subtitle{color:#728399;margin:.4rem 0 0;font-size:1rem}
.date-chip{background:#fffdf4;border:1px solid #f0d889;border-radius:10px;padding:.65rem .9rem;color:#40556d;font-size:.85rem;white-space:nowrap}
.info-strip{background:#e5f2fb;border:1px solid #cfe4f2;border-radius:10px;color:#476883;padding:.72rem .95rem;margin:1.1rem 0 1.25rem;font-size:.87rem}
.info-strip strong{color:#173d2b}
.panel-title{font-size:1.08rem;font-weight:720;color:#17334d;margin:0}
.panel-subtitle{font-size:.86rem;color:#7a8da2;margin:.18rem 0 1rem}
.farm-panel [data-testid="stVerticalBlockBorderWrapper"]{border-color:#cfe0d0;background:#fff;box-shadow:0 7px 24px #2356380c;border-radius:16px}
.farm-panel [data-testid="stWidgetLabel"] p{font-size:.82rem;color:#38516a;font-weight:650}
.stButton>button{background:#398b45;color:#fff!important;border:0;border-radius:9px;font-weight:700;min-height:2.6rem;box-shadow:0 5px 14px #398b4525}
.stButton>button:hover{background:#2f7439;color:#fff!important;border:0;box-shadow:0 7px 17px #398b4538}
.metric-card{background:#fff;border:1px solid #dce8e0;border-radius:14px;padding:1.1rem 1.2rem;min-height:126px;box-shadow:0 4px 15px #2356380a}
.metric-label{font-size:.82rem;color:#718299}.metric-value{font-size:1.35rem;font-weight:760;color:#173d2b;margin:.35rem 0}.metric-detail{font-size:.82rem;color:#718299;line-height:1.4}.metric-icon{float:right;width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center}.icon-sky{background:#e4f2fc;color:#3281b5}.icon-grass{background:#e7f3e6;color:#398b45}.icon-sun{background:#fff4ce;color:#bd8b10}
.section-heading{font-size:1.12rem;font-weight:720;color:#17334d;margin:1.6rem 0 .25rem}.section-desc{color:#7a8da2;font-size:.87rem;margin-bottom:.8rem}
.result-panel{background:#fff;border:1px solid #e2e8ef;border-radius:15px;padding:1.15rem 1.3rem;box-shadow:0 4px 16px #17324a08}
.recommend{background:#e8f4e8;border:1px solid #d2e6d1;border-left:4px solid #398b45;padding:1rem 1.15rem;border-radius:11px;color:#193b2b;line-height:1.6}
.rank-note{font-size:.85rem;color:#728399}.teal{color:#078f7f;font-weight:700}
[data-testid="stAlert"]{border-radius:11px}
@media(max-width:850px){.block-container{padding:0 1rem 2rem}.topbar{margin:0 -1rem 1.4rem;padding:0 1rem}.intro-row{align-items:flex-start;flex-direction:column}.page-title{font-size:1.65rem}.date-chip{display:none}.metric-card{margin-bottom:.6rem}}
</style>
""", unsafe_allow_html=True)

pages = ["Dashboard", "Weather", "Soil", "AI Advisory", "Model Performance", "Validation", "Advisory History", "About"]
page_icons = {"Dashboard":"▦", "Weather":"☼", "Soil":"♧", "AI Advisory":"✦", "Model Performance":"▤", "Validation":"⌁", "Advisory History":"▣", "About":"ⓘ"}

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">🌾</span><span>Crop<span class="brand-accent">Wise</span></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-kicker">Farm workspace</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", pages, format_func=lambda name: f"{page_icons[name]}   {name}", label_visibility="collapsed")
    st.markdown('<div class="nav-kicker">Preferences</div>', unsafe_allow_html=True)
    lang = st.selectbox("Language / भाषा", ["English", "हिन्दी (preview)"], key="language_choice")
    st.markdown('<div class="nav-kicker">Pilot region</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-region"><strong>📍 Bareilly, Uttar Pradesh</strong><span>Pilot region · Decision support</span></div>', unsafe_allow_html=True)
    if lang == "हिन्दी":
        st.info("Hindi interface text is prepared for a future release; this MVP's advisory is in English.")

st.markdown(f'<div class="topbar"><div>Workspace&nbsp;&nbsp; / &nbsp;&nbsp;<span class="crumb-current">{page}</span></div><div class="system-pill"><span class="system-dot">●</span> Advisory system ready</div></div>', unsafe_allow_html=True)

st.session_state.setdefault("farm_location", LOCATION)
st.session_state.setdefault("farm_crop", SUPPORTED_CROPS[0])
st.session_state.setdefault("use_default_soil", True)
st.session_state.setdefault("field_moisture", "Not checked")
st.session_state.setdefault("demo_mode", False)
st.session_state.setdefault("demo_scenario", "Maize · hot and dry")
st.session_state.setdefault("use_historical_weather", False)
st.session_state.setdefault("historical_weather_date", date.today() - timedelta(days=7))
stages = {"Maize": ["Seedling", "Vegetative", "Pre-tasseling", "Tasseling", "Silking", "Grain filling", "Maturity"],
          "Rice": ["Seedling", "Transplanting / establishment", "Vegetative", "Panicle initiation", "Flowering", "Grain filling", "Maturity"],
          "Cotton": ["Seedling", "Vegetative", "Squaring", "Flowering", "Boll formation", "Maturity"]}
last_result = st.session_state.get("last_result")
initial_context = last_result["context"] if last_result else {}
location = st.session_state.get("farm_location", initial_context.get("location", LOCATION))
crop = st.session_state.get("farm_crop", initial_context.get("crop", SUPPORTED_CROPS[0]))
stage_key = f"growth_stage_{crop}"
stage = st.session_state.get(stage_key, initial_context.get("growth_stage", stages[crop][0]))
use_default = st.session_state.get("use_default_soil", True)
field_moisture = st.session_state.get("field_moisture", "Not checked")
base_soil = defaults(location)
soil = {k: base_soil[k] for k in ("nitrogen", "phosphorus", "potassium", "ph")}
if not use_default:
    soil = {"nitrogen": st.session_state.get("soil_n", base_soil["nitrogen"]),
            "phosphorus": st.session_state.get("soil_p", base_soil["phosphorus"]),
            "potassium": st.session_state.get("soil_k", base_soil["potassium"]),
            "ph": st.session_state.get("soil_ph", base_soil["ph"])}
demo = st.session_state.get("demo_mode", False)
demo_scenario = st.session_state.get("demo_scenario", "Maize · hot and dry")
use_historical_weather = st.session_state.get("use_historical_weather", False)
historical_weather_date = st.session_state.get("historical_weather_date", date.today() - timedelta(days=7))

st.markdown(f'<div class="intro-row"><div><div class="eyebrow">Smallholder decision support</div><h1 class="page-title">{ "Good day" if page == "Dashboard" else page } <span style="color:#e7b52e">✦</span></h1><p class="page-subtitle">Weather, soil, and crop guidance for your Bareilly farm.</p></div><div class="date-chip">▣ &nbsp; {date.today().strftime("%A, %B %d")}</div></div>', unsafe_allow_html=True)

if page in ("Dashboard", "AI Advisory"):
    st.markdown('<div class="info-strip"><strong>Decision-support prototype</strong> &nbsp; Crop comparison uses NPK and pH; irrigation and pest-risk rules also use your field-moisture observation and weather.</div>', unsafe_allow_html=True)
    st.markdown('<div class="farm-panel">', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="panel-title">＋ &nbsp; Check your farm</div><div class="panel-subtitle">Choose a crop and stage, then confirm the soil information.</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.1, 1.1, 1.2])
        with c1:
            location = st.selectbox("Location", [LOCATION], key="farm_location", help="Bareilly is the current pilot district.")
        with c2:
            crop = st.selectbox("Crop to assess", SUPPORTED_CROPS, key="farm_crop")
        with c3:
            stage_key = f"growth_stage_{crop}"
            if st.session_state.get(stage_key) not in stages[crop]:
                st.session_state[stage_key] = stages[crop][0]
            stage = st.selectbox("Growth stage", stages[crop], key=stage_key)
        base_soil = defaults(location)
        use_default = st.checkbox("Use provisional soil defaults (uncheck to enter your own N, P, K and pH)", key="use_default_soil")
        if use_default:
            soil = {k: base_soil[k] for k in ("nitrogen", "phosphorus", "potassium", "ph")}
            st.caption(f"Unverified demo values · N {soil['nitrogen']:.0f} · P {soil['phosphorus']:.0f} · K {soil['potassium']:.0f} · pH {soil['ph']:.1f}. Not district SHC data; replace with a farm soil test when available.")
        else:
            s1, s2, s3, s4 = st.columns(4)
            soil = {
                "nitrogen": s1.number_input("Nitrogen (N)", 0., 300., float(base_soil["nitrogen"]), key="soil_n"),
                "phosphorus": s2.number_input("Phosphorus (P)", 0., 150., float(base_soil["phosphorus"]), key="soil_p"),
                "potassium": s3.number_input("Potassium (K)", 0., 300., float(base_soil["potassium"]), key="soil_k"),
                "ph": s4.number_input("Soil pH", 3., 10., float(base_soil["ph"]), key="soil_ph")
            }
        field_moisture = st.selectbox(
            "What does the field look like?",
            ["Not checked", "Dry", "Moist", "Water standing"],
            key="field_moisture",
            help="Choose the closest match from a quick visual check of the field soil.",
        )
        st.caption("This quick field check helps with watering and pest advice. NPK and pH are used for crop comparison.")
        use_historical_weather = st.checkbox(
            "Choose a historical NASA POWER observation date",
            key="use_historical_weather",
            help="When enabled, the advisory uses the daily NASA POWER record ending on your selected date instead of the latest available observation.",
        )
        if use_historical_weather:
            if st.session_state.get("demo_mode", False):
                st.session_state["demo_mode"] = False
            historical_weather_date = st.date_input(
                "NASA POWER date",
                min_value=date(1981, 1, 1),
                max_value=date.today() - timedelta(days=1),
                key="historical_weather_date",
                help="Choose a past date with a complete NASA POWER daily record.",
            )
            st.caption("Historical mode uses observed weather through this date; it does not use the monthly rainfall total in your source table.")
        demo_col, scenario_col, button_col = st.columns([1, 1.5, 1.1], vertical_alignment="bottom")
        with demo_col:
            demo = st.toggle("Demo mode · simulated", key="demo_mode", disabled=use_historical_weather)
        with scenario_col:
            if demo:
                demo_scenario = st.selectbox("Demo scenario", ["Maize · hot and dry", "Rice · warm and humid", "Cotton · rain expected"], key="demo_scenario")
        with button_col:
            submit = st.button("✦  Get Advisory", type="primary", use_container_width=True)

    if submit:
        try:
            soil = validate(soil)
            if use_historical_weather:
                weather = fetch_historical_weather(location, historical_weather_date)
            else:
                weather = fetch_weather(location, use_demo=demo)
            if demo and demo_scenario.startswith("Rice"):
                weather.update(temperature=29., humidity=86., rainfall=14., rainfall_7d=14., forecast_rainfall=0.)
            elif demo and demo_scenario.startswith("Cotton"):
                weather.update(temperature=27., humidity=72., rainfall=1., rainfall_7d=1., forecast_rainfall=18.)
            context = AdvisoryContext(location, crop, stage, soil, weather, "Provisional district defaults" if use_default else "Farmer-entered", demo, field_moisture)
            result = run(context)
            save(result)
            st.session_state["last_result"] = result
            st.session_state["last_saved"] = True
            last_result = result
        except ValueError as exc:
            st.error(f"Please check the soil inputs: {exc}")
        except Exception:
            st.error("The advisory could not be prepared. Please try again.")
            if st.query_params.get("debug") == "1":
                st.exception(Exception("See developer log for details."))

result = st.session_state.get("last_result")
if result and page in ("Dashboard", "AI Advisory"):
    saved = result["context"]
    saved_weather = saved.get("weather", {})
    historical_date_changed = (
        (use_historical_weather and saved_weather.get("date") != historical_weather_date.strftime("%Y%m%d"))
        or (not use_historical_weather and saved_weather.get("status") == "Historical NASA POWER observation")
    )
    inputs_changed = (saved["location"] != location or saved["crop"] != crop or saved["growth_stage"] != stage or
                      saved["soil"] != soil or saved.get("field_moisture", "Not checked") != st.session_state.get("field_moisture", "Not checked") or
                      saved.get("demo", False) != demo or historical_date_changed)
    if inputs_changed:
        result = None
        st.info("Your farm inputs changed. Press **Get Advisory** to calculate a fresh result.")

if page in ("Dashboard", "AI Advisory"):
    if result is None:
        st.markdown('<div class="section-heading">Your farm at a glance</div><div class="section-desc">Your advisory and field actions will appear here after you request a check.</div>', unsafe_allow_html=True)
        st.info("Start with the farm details above, then choose **Get Advisory**.")
        with st.container(border=True):
            st.markdown("**How the advisory works**  \nFarmer input → NASA POWER weather + soil → crop comparison → irrigation and pest-risk checks → one practical recommendation")
    else:
        w, irr, pest, pred = result["context"]["weather"], result["irrigation"], result["pest_risk"], result["crop_suitability"]
        st.markdown(f'<div class="section-heading">Farm overview</div><div class="section-desc">{result["context"]["location"]} &nbsp;·&nbsp; {result["context"]["crop"]} &nbsp;·&nbsp; {result["context"]["growth_stage"]}</div>', unsafe_allow_html=True)
        if w.get("status") == "Unavailable":
            st.warning(w.get("error", "Weather data is temporarily unavailable."))
        else:
            st.caption(f"Weather source: NASA POWER · {w.get('status')} · observation date {w.get('date')}")
        cols = st.columns(3)
        with cols[0]: st.markdown(f"<div class='metric-card'><span class='metric-icon icon-sky'>☼</span><div class='metric-label'>Weather</div><div class='metric-value'>{w.get('temperature','—')}°C</div><div class='metric-detail'>Humidity {w.get('humidity','—')}% · 7-day rain {w.get('rainfall_7d',w.get('rainfall','—'))} mm</div></div>", unsafe_allow_html=True)
        with cols[1]: st.markdown(f"<div class='metric-card'><span class='metric-icon icon-grass'>💧</span><div class='metric-label'>Irrigation</div><div class='metric-value'>{irr['priority']}</div><div class='metric-detail'>{irr['action']}</div></div>", unsafe_allow_html=True)
        with cols[2]: st.markdown(f"<div class='metric-card'><span class='metric-icon icon-sun'>⌁</span><div class='metric-label'>Pest risk</div><div class='metric-value'>{pest['level']}</div><div class='metric-detail'>Field: {pest.get('field_moisture', 'Not checked')} · {pest['action']}. Weather-based risk alert · not a diagnosis</div></div>", unsafe_allow_html=True)

        st.markdown('<div class="section-heading">Selected crop suitability</div><div class="section-desc">How the selected crop matches the soil and weather inputs, compared with the other two pilot crops.</div>', unsafe_allow_html=True)
        if pred:
            selected_score = pred.get("selected_crop_score")
            selected_rank = pred.get("selected_crop_rank")
            match_label = {1: "Strongest relative match", 2: "Middle relative match", 3: "Lowest relative match"}.get(selected_rank, "Relative match unavailable")
            if pred.get("input_out_of_range"):
                match_label = "Outside training ranges"
            c1, c2 = st.columns([1, 1.35])
            with c1:
                with st.container(border=True):
                    st.markdown(f"**{result['context']['crop']} · {match_label}**")
                    if selected_score is not None:
                        st.metric("Relative model score", f"{selected_score:.0%}", f"Rank {selected_rank} of 3", delta_color="off", help="A comparison score from the classifier, not a probability of crop success or yield.")
                        st.progress(selected_score)
                    st.caption("This describes the model’s match among Rice, Maize, and Cotton for the soil and weather values above. It is not a field-tested suitability or yield prediction.")
            with c2:
                with st.container(border=True):
                    st.markdown(f"**Top match · {pred['crop'].title()}**")
                    st.metric("Top model score", f"{pred['confidence']:.0%}", delta_color="off")
                    st.bar_chart(pred["probabilities"], height=130)
            out_of_range = pred.get("input_out_of_range", [])
            if out_of_range:
                details = ", ".join(f"{item['feature']} {item['value']:.1f} (training range {item['min']:.1f}–{item['max']:.1f})" for item in out_of_range)
                st.warning(f"The model has not learned these input values: {details}. Treat its crop scores as unsupported comparisons, not suitability advice.")
            elif pred["confidence"] < .55:
                st.warning("Low confidence: the model cannot make a strong distinction among the three crop labels. Treat this as an initial comparison, not a crop-success prediction.")
            st.caption("The model uses a general public dataset and has not been field-validated in Bareilly.")
        else:
            st.warning("Crop suitability is unavailable because the model could not use these inputs.")
        if demo:
            st.warning("Simulated demo values — not live weather.")

        st.markdown('<div class="section-heading">Today\'s recommendation</div><div class="section-desc">The advisory engine combines crop comparison, irrigation rules, and pest-risk checks.</div>', unsafe_allow_html=True)
        st.markdown(f"<div class='recommend'><b>{result['final_advice']}</b></div>", unsafe_allow_html=True)
        with st.expander("Why this recommendation?"):
            st.write("**Irrigation:**", irr["reason"])
            st.write("**Pest risk:**", pest["reason"])
            st.write("**Soil values used:**", ", ".join(f"{k}: {v}" for k,v in result["context"]["soil"].items()))
            st.write("**Field moisture (farmer observation):**", result["context"].get("field_moisture", "Not checked"))
            st.write("**Weather values used:**", json.dumps(w, ensure_ascii=False))
        st.caption(result["disclaimer"])

elif page == "Weather":
    st.markdown('<div class="section-heading">Weather observations</div><div class="section-desc">NASA POWER daily observations used by the latest advisory.</div>', unsafe_allow_html=True)
    if result:
        weather = result["context"]["weather"]
        a,b,c = st.columns(3)
        for col,label,key,suffix in ((a,"Temperature","temperature","°C"),(b,"Relative humidity","humidity","%"),(c,"Rainfall · 7 days","rainfall_7d"," mm")):
            col.metric(label, f"{weather.get(key, weather.get('rainfall','—'))}{suffix}")
        st.json(weather)
        st.caption("POWER gives daily gridded observations, not a short-term local forecast.")
    else:
        st.info("Run an advisory from the Dashboard to retrieve and display weather observations.")

elif page == "Soil":
    st.markdown('<div class="section-heading">Soil information</div><div class="section-desc">Review the soil inputs used by the latest advisory.</div>', unsafe_allow_html=True)
    if result:
        st.json(result["context"]["soil"])
        st.caption(f"Source: {result['context']['soil_source']}")
    else:
        st.json(defaults())
        st.warning("Bareilly defaults are provisional demonstration values, not verified district Soil Health Card averages. Enter farm soil-test results in the Dashboard for a farm-specific assessment.")

elif page == "Model Performance":
    st.markdown('<div class="section-heading">Model performance</div><div class="section-desc">Held-out evaluation for the three pilot crops.</div>', unsafe_allow_html=True)
    m = metadata()
    if not m:
        st.warning("No trained model or evaluation metrics are present.")
    else:
        st.caption(f"Dataset {m['dataset']} · {m['samples']} rows · {len(m['features'])} features · classes: {', '.join(m['classes'])}")
        a,b,c,d = st.columns(4)
        for col,label,key in zip((a,b,c,d),("Accuracy","Precision","Recall","F1"),("accuracy","precision_weighted","recall_weighted","f1_weighted")):
            col.metric(label, f"{m[key]:.1%}")
        st.caption(f"Random Forest · {m['split']} · random_state={m['random_state']} · Metrics are not field-trial accuracy.")
        cv = m.get("cross_validation")
        if cv:
            st.caption(f"5-fold cross-validation on the same dataset: {cv['accuracy_mean']:.1%} ± {cv['accuracy_std']:.1%}. This is internal validation, not an independent Bareilly field test.")
        st.caption("Predictions outside the feature ranges shown in the training data are flagged as unsupported.")
        import matplotlib.pyplot as plt
        fig,ax = plt.subplots()
        ax.imshow(m["confusion_matrix"], cmap="Greens")
        ax.set_xticks(range(len(m["class_labels"])),m["class_labels"],rotation=30)
        ax.set_yticks(range(len(m["class_labels"])),m["class_labels"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        for i,row in enumerate(m["confusion_matrix"]):
            for j,val in enumerate(row): ax.text(j,i,str(val),ha="center",va="center")
        st.pyplot(fig)
        st.bar_chart(m["feature_importance"])

elif page == "Validation":
    st.markdown('<div class="section-heading">Historical validation</div><div class="section-desc">Compare dated NASA POWER scenarios with independently reviewed expected guidance.</div>', unsafe_allow_html=True)
    st.caption("Use Rice, Maize, and Cotton. Expected fields: top crop; irrigation category; pest-risk level; and a source for each expected result. Leave soil columns blank to use configured defaults.")
    if SCENARIOS.exists():
        scenarios = __import__("pandas").read_csv(SCENARIOS)
        if scenarios.empty:
            st.info("Add real historical scenarios and sourced expected guidance to validation/past_scenarios.csv before running the check.")
        else:
            st.dataframe(scenarios, use_container_width=True)
            if st.button("Run historical validation", type="primary"):
                with st.spinner("Fetching historical NASA POWER observations and running scenarios…"):
                    try:
                        st.session_state["validation_results"] = run_validation()
                    except Exception as exc:
                        st.error(f"Validation could not run: {exc}")
    validation_results = st.session_state.get("validation_results")
    if validation_results is None and RESULTS.exists():
        try:
            saved_results = __import__("pandas").read_csv(RESULTS)
            validation_results = saved_results if not saved_results.empty else None
        except Exception:
            validation_results = None
    if validation_results is not None:
        result_frame = __import__("pandas").DataFrame(validation_results)
        valid_count = int(result_frame["match"].notna().sum()) if "match" in result_frame else 0
        matched_count = int(result_frame["match"].fillna(False).astype(bool).sum()) if valid_count else 0
        metric = validation_score(result_frame)
        a,b,c = st.columns(3)
        a.metric("Scored scenarios", f"{valid_count} / {len(result_frame)}")
        b.metric("Matches", str(matched_count))
        c.metric("Match rate", f"{metric:.0%}" if metric is not None else "Not available")
        if meets_target(result_frame): st.success("At least 8 of 10 scored scenarios matched the supplied guidance.")
        elif valid_count >= 10: st.warning("The target of 8 matches out of 10 was not met.")
        else: st.info("At least 10 valid scenarios are needed to evaluate the 8/10 target.")
        st.dataframe(result_frame, use_container_width=True, hide_index=True)

elif page == "Advisory History":
    st.markdown('<div class="section-heading">Advisory history</div><div class="section-desc">Past checks saved on this device. No personal identifiers are collected.</div>', unsafe_allow_html=True)
    rows = history()
    if rows:
        import pandas as pd
        st.dataframe(pd.DataFrame([{"ID":r["id"],"Date":r["timestamp"],"Selected crop":r["crop"],"Relative score":f"{r['selected_crop_score']:.0%}" if r["selected_crop_score"] is not None else "Unavailable","Rank":f"{r['selected_crop_rank']} / 3" if r["selected_crop_rank"] else "—","Top match":(r["predicted_crop"] or "Unavailable").title(),"Irrigation":r["irrigation"],"Pest Risk":r["pest_risk"]} for r in rows]), use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect a saved advisory", [r["id"] for r in rows])
        st.json(json.loads(get_record(selected)["payload_json"]))
    else:
        st.info("Your saved advisories will appear here after you run a farm check.")

elif page == "About":
    st.markdown('<div class="section-heading">About CropWise</div><div class="section-desc">A transparent decision-support prototype for smallholder farmers.</div>', unsafe_allow_html=True)
    st.markdown("""
**Purpose:** supports SDG 2 and SDG 13 through a sequence of input collection, data retrieval, crop comparison, rule-based analysis, recommendation, and history storage.

**Sources:** weather uses NASA POWER daily observations. Soil defaults are provisional placeholders. The crop model uses Rice, Maize, and Cotton rows from the public Kaggle Crop Recommendation dataset. Critical irrigation stages are informed by the [ICAR Kharif Agro-Advisory 2025](https://www.icar.org.in/sites/default/files/Circulars/ICAR-En-Kharif-Agro-Advisories-for-Farmers-2025.pdf); rain thresholds are configurable prototype checks, not official ICAR thresholds.

**Limitations:** general dataset rather than Bareilly field trials; soil defaults may not represent a farm; field moisture is farmer-reported, not sensor-measured; rainfall periods in the training data may differ from NASA's seven-day total; no short-range forecast; pest output is risk, not diagnosis. NPK and pH inform crop comparison but do not determine irrigation demand. This advisory is decision support and does not replace certified agricultural or expert advice.
""")
