# PitchSide / Kickoff Coach

A fully Python Streamlit hackathon MVP that uses a five-question check-in to assign a soccer archetype and create a "Match Fitness" score.

## First run: local Python demo

```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

The app works without Databricks or Gemini. It uses synthetic records and a built-in Gaffer briefing.

## Optional: Databricks

Set the connection values from your Databricks SQL Warehouse. The hostname should not include `https://`.

```bash
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_TOKEN="your-private-token"
python3 setup_databricks.py
```

This creates `main.pitchside.student_checkins` with synthetic data. Replace `main` in `Data.py` and `setup_databricks.py` if your Unity Catalog uses another catalog.

## Optional: Gemini

```bash
export GEMINI_API_KEY="your-gemini-key"
```

Restart Streamlit after setting the key. Never commit tokens or API keys.
