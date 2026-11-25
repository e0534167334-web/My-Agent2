# Smart Study Agent
Python 3.12 / Windows / LangGraph / Streamlit / SQLite.

## Setup
Extract to a new folder, not over your existing project. Open it in VS Code. Run `./setup.ps1` in PowerShell (or manually create venv and install requirements if script execution is restricted). Copy your existing API key into `.env` locally. Never commit it. Run `./run.ps1`. Demo mode uses no API, ignores input and does not persist reminders. Real mode sends input to OpenAI only after consent. Keep tracing false for personal data.

## Architecture
Domain models, policies and validators are independent of the LLM. Infrastructure provides file readers, planner, SQLite and ICS. Graph: extract -> clarify interrupt if needed -> generate -> validate -> retry (max 2) -> review interrupt -> approve or revise (max 2) -> end. The UI persists approved plans and exports ICS. SQLite checkpoints retain inputs locally, including images. Delete data only when you no longer need saved plans. The UI does not yet restore a thread after browser restart. One availability interval per request; event edits require starting over. Missing end time is treated as one hour. Mixed scanned/text PDF pages may not be fully extracted. No external calendar sync.

## Windows reminders
After real plan approval, run `./install-reminders.ps1` yourself. It registers a limited current-user task at login and every five minutes. It shows a local message box even when Streamlit is closed, with no internet required. Missed alerts are delivered at next login/check; no notification while PC is off. Acknowledged alerts are marked delivered; crash before marking may repeat an alert. Test using a near-future synthetic event. Remove with `Unregister-ScheduledTask -TaskName SmartStudyAgentReminders -Confirm`. ICS intentionally has no alarms to avoid duplicate notifications. Task registration and delivery must be tested on Windows.

## Evaluation (paid API calls; optional until submission)
Use synthetic data only. Set LANGSMITH_API_KEY and regional endpoint if needed. Each command below makes three model calls with the bundled dataset; verify dataset size before reusing a remote dataset. Run separately, review credit before the second run.

```
python -m evaluation.experiments --variant before --confirm-paid
python -m evaluation.experiments --variant after --confirm-paid
```

Baseline generic reminder vs deterministic domain policy. Evaluator checks extracted type and reminder count. This is a component experiment, not full graph evaluation. Record actual scores and inspect traces; do not invent results. Add screenshots of graph traces and both experiments to docs/ and write a real insight using the template. LangSmith access is required for submission.

## Verification
`python -m pytest -q`. Graph test is skipped if LangGraph is missing. No real API or Windows execution is performed by tests. Review limits, time-zone edge cases, and saved data before real use.
