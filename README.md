# kickoff_coach

PitchSide / Kickoff Coach is a Python Streamlit hackathon project with a student-facing football personality experience and separate backend work.

The current frontend is the v8 still-image version. Its welcome page offers the main quiz button and a small link to a separate password-protected staff dashboard. See [`frontend/README.md`](frontend/README.md) for the two local run commands; the dashboard charts display category labels horizontally.

## Frontend prototype

The Python/Streamlit student-facing prototype lives in [`frontend/`](frontend/). It includes a welcome page, a conversational information check driven by a local rule-based question agent, and a football-personality result page. A local analysis agent prepares descriptive results. Gemini can optionally create a narrative briefing after the student requests it. These agents have not yet been integrated with the separate backend.

Run it from the `frontend` directory using the instructions in [`frontend/README.md`](frontend/README.md). The collection schema and backend integration contract are in [`frontend/COLLECTION_STANDARD.md`](frontend/COLLECTION_STANDARD.md) and [`frontend/BACKEND_HANDOFF.md`](frontend/BACKEND_HANDOFF.md).

The repository root's `app.py`, `Data.py`, and `setup_databricks.py` belong to the separate backend work. Follow the instructions in `frontend/README.md` to run the student-facing experience.

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
