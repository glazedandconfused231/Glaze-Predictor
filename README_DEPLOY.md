
# Glaze Combination Predictor — Streamlit Cloud

This folder contains everything needed to deploy your app on Streamlit Community Cloud.

## Files
- `glaze_predictor_app.py` — the app
- `glaze_inventory.csv` — your glaze list (editable in app)
- `glaze_rules.csv` — rule hints for interactions
- `glaze_experiments.csv` — your logged results
- `requirements.txt` — Python dependencies
- `runtime.txt` — Python version pin (3.11)

## One-time Setup (about 5 minutes)
1. Create a **public GitHub repository** (e.g., `glaze-predictor`).
2. Upload all files from this folder to that repo.
3. Go to https://share.streamlit.io/ → **New app** → connect your GitHub → pick your repo.
4. Set **Main file path** to `glaze_predictor_app.py` → Deploy.
5. After it builds, you’ll get a URL you can open on your iPhone.

## Updating your glazes
- Use the sidebar in the app to add/edit and **Save** — this writes back to the CSVs in the app filesystem.
- For permanent changes (so they persist across redeploys), commit the updated CSVs back to GitHub.
