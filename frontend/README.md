# WCPT: World Cup Personality Test

A three-page Streamlit prototype written in Python. The generated chibi soccer illustration in `static/soccer_background.png` appears behind the pages. Styling is applied from Python in `app.py`.

## Pages

1. **Welcome:** the background image, one randomly selected attributed player quote, and the **Start WCPT** button.
2. **Information check:** a conversational sequence asks about nightly sleep, weekly class hours and GPA, extracurricular hours, and average daily study time on weekdays and weekends. It asks conditional follow-ups, shows coverage, and lets the student correct the extracted record before confirmation.
3. **Result:** one of four illustrative football personalities (Midfielder, Captain, Penalty Striker, or Defender) when all six numeric baseline values are available. The user can ask **The Gaffer** for a Gemini-powered, encouraging briefing based on their confirmed check-in. It is not a prediction, diagnosis, or academic decision.

WCPT means **World Cup Personality Test**. `collection_gateway.py` is the integration point for the future information-collection agent. Today it uses a transparent rule-based demo in `collector.py`. The demo accepts short numeric answers and listed choices, then chooses the next question. It does **not** understand arbitrary natural language. The result is assigned by a small demonstration rule in `engine.py` using the six numeric baseline values only. It is not an AI assessment or a validated prediction. The app does not predict GPA, sleep, or wellbeing.

## Run

From this directory in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false
```

Open <http://127.0.0.1:8502/>. If the port is occupied, change the port number.

## Gemini setup (optional)

Create a Gemini API key in Google AI Studio, then set it in the same terminal that starts Streamlit. Keep it out of Git and browser-side code.

```powershell
$env:GEMINI_API_KEY = "your-private-key"
```

Without a key, the app shows a safe local fallback message. With a key, **Ask The Gaffer for advice** sends only the confirmed structured check-in fields—not the free-text transcript—to Gemini.

Confirmed structured records, transcripts, record IDs, and illustrative results are saved in `collection_submissions` in `data/submissions.sqlite3`. Older submissions are preserved in previous tables. Set `STUDENT_DB_PATH` to use a different database. Do not enter names or other identifying information in this prototype.

The welcome page links each quote to its UEFA interview. See [COLLECTION_STANDARD.md](COLLECTION_STANDARD.md) for the collection standard, [BACKEND_HANDOFF.md](BACKEND_HANDOFF.md) for the agent interface, and [flowchart.md](flowchart.md) for the flow. The next-phase analysis requirement is recorded in [ANALYSIS_AGENT_BACKLOG.md](ANALYSIS_AGENT_BACKLOG.md) and developed into a proposal in [ANALYSIS_AGENT_DESIGN.md](ANALYSIS_AGENT_DESIGN.md).
