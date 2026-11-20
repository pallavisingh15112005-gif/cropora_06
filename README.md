# Cropora AI

Crop price advisor for farmers: check mandi prices, see a seven-day forecast, compare markets, get selling advice and ask questions in plain language.

Built as a second-year B.Tech CSE (AI & ML) mini project by a team of two, using Python and Streamlit.

---

## 1. What the app does

| Feature | Where in the app |
|---|---|
| Today's mandi price and a 7-day price forecast with an 80% range | Prices & forecast |
| Map of nearby mandis with straight-line distance from the selected location | Mandi map |
| Same-crop comparison across mandis, including net price after estimated transport | Compare mandis |
| Sell / hold recommendation, best mandi, and "what to grow this week" | Recommendations |
| Target-price alerts stored in Turso (local libSQL file fallback) | Price alerts |
| Live Agmarknet prices via data.gov.in, cached in Turso, with sync status | Live mandi prices |
| Symptom-based guide to common crop diseases and pests, with remedies | Crop diseases |
| Leaf-photo disease screening with a local image model, top-3 confidence and linked remedies | Photo diagnosis |
| Government schemes with eligibility, how to apply and official portal links | Government schemes |
| Plain-language chatbot for prices, forecasts, selling, diseases, schemes and accuracy | Ask Cropora |
| Best crop of the week and the full commodity ranking | Dashboard |
| Honest model accuracy (MAPE, R², backtest size) and limitations | Model accuracy |

No login. A location selector in the sidebar personalises distances, transport cost and advice.

**Coverage:** 13 commodities across 18 mandis in 11 states.

- Crops: Wheat, Paddy (Rice), Maize, Soybean, Cotton, Onion, Tomato, Potato
- Fruits: Banana, Mango, Apple, Grapes, Orange

Photo diagnosis uses a separate trained image model with 38 leaf classes. Besides the
market crops above, it also recognises bell pepper, blueberry, cherry, peach, raspberry,
squash and strawberry leaves, which are outside the price coverage.

---

## 2. Data used (important for the report)

The app has two price sources, and every page states which one it is showing.

**1. Live Agmarknet prices (new).** The Live mandi prices page calls the official
data.gov.in Agmarknet resource (`9ef84268-d588-465a-a308-a864a43d0070`) and upserts
the result into Turso. `Agmarknet 2.0` protects its own JSON endpoint with a CAPTCHA
(`TOKEN_OR_CAPTCHA_REQUIRED`); the project does **not** bypass that. The key-based
data.gov.in resource is the sanctioned route to the same daily mandi prices. Live
sync needs a free API key from data.gov.in.

When live rows exist:

- Today's modal price for a matched commodity–mandi pair comes from Agmarknet.
- The 7-day forecast path is rescaled to the live level, so the chart starts at the
  live price. Model coefficients and the backtest still come from the sample history.
- Pairs without a live row keep their sample price.
- Alerts compare targets against the latest cached price (live where available).
- The app shows the source, live price date and last sync time.

**2. Synthetic sample history (still used for modelling).**

- 730 days of daily prices for 13 commodities and 81 commodity–mandi pairs: 59,130 rows.
- Latest date in the sample: **20 November 2026**.
- Columns follow the Agmarknet style: date, commodity, mandi, modal price, min price, max price (₹ per quintal).
- The generator is deterministic (fixed seed), so results are reproducible.
- Prices include harvest-season effects, a festival bump, slow market cycles, AR(1) noise, occasional shocks, and mandi-level price differences.
- The Ridge models and the rolling-origin backtest are trained and measured on this history.

This split is deliberate: the live feed supplies the current price level, while the
sample history supplies enough past data to train and validate a model. The accuracy
page and the README both state this.

**3. Leaf-photo model (for photo diagnosis, separate from prices).**

The Photo diagnosis page uses a MobileNetV2 classifier with 38 PlantVillage leaf
classes (26 disease/pest and 12 healthy), from the
[onnx-community plant disease model](https://huggingface.co/onnx-community/mobilenet_v2_1.0_224-plant-disease-identification-ONNX).
The ONNX weights, label config and
preprocessing config are stored in `assets/models/plant_disease/` and run locally with
onnxruntime. No price feed or API key is involved, and the photo is not uploaded
anywhere. PlantVillage photos ([dataset](https://github.com/spMohanty/PlantVillage-Dataset))
are mostly single leaves on plain backgrounds, so field
photos are harder; the page shows a low-confidence warning instead of forcing a
diagnosis.

Files:

- `data/prices.csv` – generated daily history
- `data/crops.csv` – crop names, category and season notes
- `data/mandis.csv` – mandi names, states, coordinates
- `data/locations.csv` – selectable user locations and coordinates
- `data/cropora.db` – local libSQL database for alerts, cached live prices and sync metadata (created automatically when Turso is not configured)

---

## 3. Tech stack

- **Python 3.12**
- **Streamlit 1.59** – multipage UI, chat elements, forms, dataframes
- **pandas / NumPy** – data preparation and features
- **scikit-learn** – Ridge regression and StandardScaler
- **Plotly 6** – price charts and OpenStreetMap-based mandi map (no API key)
- **requests** – data.gov.in Agmarknet API client
- **Turso / libSQL** – alerts, cached live prices and sync metadata; a local
  `data/cropora.db` libSQL file is used automatically when Turso is not configured
- **onnxruntime + Pillow** – local MobileNetV2 leaf-photo inference, no external AI service

The chatbot is deliberately **rule-based**: keyword intents, crop/mandi aliases (including Hindi names), and answers generated from the dataset and a curated knowledge base. No external AI service is called. Photo diagnosis also runs fully offline: the model file ships in `assets/models/plant_disease/`, and the photo is never sent to a third party.

---

## 4. How to run

From the project folder:

```bash
pip install -r requirements.txt

python scripts/generate_sample_data.py
python scripts/build_artifacts.py

python -m streamlit run app.py
```

Photo diagnosis needs no extra download: the 8.8 MB ONNX model and its config are
included in `assets/models/plant_disease/`.

On Windows, use `python -m streamlit ...` if `streamlit` is not on PATH. The app opens at http://localhost:8501.

The first two scripts only need to be rerun when you want to regenerate the dataset or retrain the forecasting models. `build_artifacts.py` takes roughly 15–20 seconds.

If your terminal cannot print the ₹ symbol, run scripts with UTF-8 output:

```bash
PYTHONIOENCODING=utf-8 python scripts/build_artifacts.py
```

### Enabling live prices and Turso

The app runs without any credentials: it uses the sample history and a local libSQL
file. To switch on live Agmarknet sync and Turso Cloud:

1. Create a free account at [data.gov.in](https://data.gov.in/) and copy your API key
   from **My Account → API key**.
2. Create a Turso database and token:

   ```bash
   turso db create cropora
   turso db show cropora --url
   turso db tokens create cropora
   ```

3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:

   ```toml
   DATA_GOV_API_KEY = "your-data-gov-in-key"
   TURSO_DATABASE_URL = "libsql://your-database.turso.io"
   TURSO_AUTH_TOKEN = "your-turso-token"
   ```

4. Restart Streamlit, open **Live mandi prices** and press **Sync now**. The page
   reports fetched rows, matched commodities/mandis, the price date and any error.
   Cached dates are upserted, not duplicated, so pressing Sync again is safe.

Environment variables with the same names also work. Never commit
`.streamlit/secrets.toml`; the example file contains placeholders only.

The app first reads `st.secrets`, then environment variables. If Turso is configured
but unreachable, the page shows the database error instead of silently falling back,
so a broken remote setup is visible.

---

## 5. How the forecast works

- One **Ridge regression** model per commodity (`alpha = 3.0`, features standardised).
- Inputs: prices lagged 1, 2, 3, 7, 14, 21 and 30 days; 7/14/30-day rolling means; 7-day rolling volatility; 7- and 30-day momentum; day-of-year seasonality (two harmonics); day-of-week; mandi identity (one-hot).
- The model predicts day 1, then feeds that prediction back to predict day 2, and so on for a recursive 7-day path.
- Day-over-day change is clamped to ±6%, and the path is anchored within 25–35% of the latest price to avoid runaway recursion.
- The shaded band is an **80% range** built from the 80th percentile of absolute errors at each horizon in the backtest. It is an estimate, not a guarantee.
- When a live Agmarknet price is cached for a pair, the whole forecast path (including
  the band) is rescaled by `live price / last sample price`. Today's price and the
  day-7 move therefore start from the live level, while the shape and accuracy still
  come from the model trained on the sample history.

**Validation:** rolling-origin backtest with 28 consecutive origins. For each origin the model is trained only on data before a cutoff and evaluated on the following seven unseen days. Errors are pooled across commodities.

Current results from `artifacts/metrics.csv`:

| Metric | Value |
|---|---|
| Average MAPE, day 7 | 1.77% |
| Average MAPE, all horizons | 1.4% |
| Average R² | 0.78 |
| Backtest predictions | 15,876 |
| Commodities modelled | 13 |

The accuracy page shows per-commodity MAE, RMSE, MAPE and R², and lists the honest limitations. Forecasts are one input to a selling decision, not a promise.

Other modelling assumptions:

- Prices are in ₹ per quintal; transport is estimated at ₹0.10 per quintal per km.
- Distance is straight-line (Haversine) from the selected location, not road distance.
- Sell/hold rule: hold if the expected net price improves by 2% or more over seven days; sell now if it falls by 2% or more; otherwise the difference is treated as small.
- Best crop of the week score = 50% price momentum + 25% stability + 25% value versus the one-year average.

---

## 6. Project structure

```
app.py                  # navigation, sidebar, shared session state
ui.py                   # shared layout, charts, map, tables, theme helpers
data_layer.py           # data loading, live overlay, distances, forecasts, sell plan
db.py                   # Turso/libSQL connection layer and schema
agmarknet.py            # data.gov.in fetch, commodity/mandi mapping, caching
forecasting.py          # feature engineering, Ridge models, backtest, artifacts
knowledge.py            # 43 disease/pest entries and 9 government schemes
chatbot.py              # rule-based intent routing and answer builders
alerts.py               # alert storage and status checks
disease_detector.py     # ONNX leaf-photo model, preprocessing and label mapping
app_pages/              # one file per screen
  dashboard.py
  prices_forecast.py
  live_prices.py
  mandi_map.py
  compare_mandis.py
  recommendations.py
  price_alerts.py
  crop_diseases.py
  photo_diagnosis.py
  schemes.py
  accuracy.py
  chat.py
scripts/
  generate_sample_data.py
  build_artifacts.py
data/                   # generated CSVs and the local cropora.db fallback
artifacts/              # metrics.csv, forecasts.csv, model_info.json
assets/hero.png         # dashboard illustration
assets/models/plant_disease/  # MobileNetV2 ONNX model, label config, preprocessing config
.streamlit/config.toml  # farming colour theme and fonts
.streamlit/secrets.toml.example  # key/token placeholders (copy, do not commit real values)
requirements.txt
```

The layout and colours are configured only in `.streamlit/config.toml` (cream background, deep green, gold accents, Playfair Display headings). No custom CSS is used.

---

## 7. What is done

- All ten required features are implemented and usable: price alerts, distance map, 7-day forecast, chatbot, sell/grow recommendations, disease guide, government schemes, mandi comparison, best crop of the week and an accuracy screen.
- 13 commodities including 5 fruits; 18 mandis across 11 states.
- Reproducible sample data generator and a trained, backtested forecasting pipeline.
- No-login, single-file-per-page Streamlit app with a consistent farming theme.
- Turso-backed storage for alerts, cached live prices and sync metadata, with a
  local libSQL file fallback so the app runs before credentials are added.
- Live Agmarknet sync through the data.gov.in API, with one-click refresh, source
  labels, live price dates, sync errors and CSV download.
- Live prices anchor today's price and the forecast level across the dashboard,
  prices, map, comparison, recommendations, alerts and chatbot pages.
- Rule-based chatbot that understands crop and city aliases (including several Hindi crop names) and answers from the app's own data.
- Photo-based disease screening: a MobileNetV2 model trained on PlantVillage's 38 leaf
  classes runs locally on an uploaded or camera photo, shows the top three matches with
  confidence, reuses the remedy knowledge base and warns on low-confidence photos.
- README, requirements file and a clear done-versus-future split for the report.

## 8. Future scope

- **Scheduled sync:** refresh live prices automatically (cron or a hosted scheduler) instead of pressing Sync now, with more commodities, mandis and variety-level prices.
- **Turso migrations:** versioned schema migrations and an admin view for sync history.
- **User accounts:** login, saved crops, saved locations and alerts synced across devices (deliberately out of scope for this version).
- **Notifications:** SMS, WhatsApp or push alerts instead of checking only when the app is opened.
- **Field-photo disease model:** an India-specific model trained on cluttered field photos and more crops, with multi-leaf detection, instead of the current PlantVillage single-leaf model.
- **Smarter forecasting:** gradient boosting / LSTM models, weather and arrival-volume features, and proper probabilistic calibration of the 80% band.
- **Road distance and routing:** a maps directions API for real transport distance and cost instead of straight-line distance and a flat rate.
- **Language support:** Hindi and other regional-language UI and chatbot responses.
- **Advisory depth:** crop calendars, input costs, storage advice and links to local KVKs, validated by an agriculture expert.

---

## 9. Suggested two-person split (for the report)

- **Member A – data and ML:** sample-data generator, data layer, feature engineering, Ridge models, rolling-origin backtest, ONNX photo model integration, accuracy page.
- **Member B – product and UI:** Streamlit theme, all app pages, charts and map, alerts storage, knowledge base, rule-based chatbot.
- **Both:** requirement analysis, integration, browser testing, documentation and presentation.

---

## 10. Limitations and responsible use

- The 730-day history and the trained model come from synthetic data. Live Agmarknet
  prices anchor the current level when synced, but model coefficients and the
  backtest are still based on the sample history; accuracy on live prices will be lower.
- Live coverage depends on what data.gov.in reports for the 13 commodities and 18
  mandis. Unmatched pairs keep their sample price, and the app labels the source.
- The data.gov.in resource requires a personal API key and is rate-limited. Agmarknet
  2.0's own endpoint requires an interactive CAPTCHA, which this project does not bypass.
- The model is linear and short-term. It cannot anticipate policy changes, transport strikes, extreme weather or sudden arrival surges.
- Photo diagnosis uses a PlantVillage-trained MobileNetV2 model with 38 leaf classes.
  Lab-style single-leaf photos work best; cluttered field photos, other crops, nutrient
  deficiencies and problems outside those classes can be misclassified. Confidence is
  the model's score, not a tested accuracy figure, and the page warns below 45%.
- Disease and pesticide guidance is general and not a diagnosis. Doses must follow the product label; consult a local Krishi Vigyan Kendra or agriculture officer.
- Government scheme summaries are for a student project. Rules and portals change; verify current terms on the official site.
- Transport cost and straight-line distance are estimates. Check actual freight and mandi charges before selling.
