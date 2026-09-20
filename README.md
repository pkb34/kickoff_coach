# kickoff_coach

PitchSide / Kickoff Coach is a Python Streamlit hackathon MVP that uses a five-question check-in to assign a soccer archetype and create a "Match Fitness" score.

## Frontend prototype

The Python/Streamlit student-facing prototype lives in [`frontend/`](frontend/). It includes a welcome page, a conversational information check with a rule-based demo collector, and an illustrative football-personality result page. The real information-collection and analysis agents have not been connected yet.

Run it from the `frontend` directory using the instructions in [`frontend/README.md`](frontend/README.md). The collection schema and backend integration contract are in [`frontend/COLLECTION_STANDARD.md`](frontend/COLLECTION_STANDARD.md) and [`frontend/BACKEND_HANDOFF.md`](frontend/BACKEND_HANDOFF.md).

The repository root's `Data.py` belongs to the separate backend work and is left unchanged.

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
