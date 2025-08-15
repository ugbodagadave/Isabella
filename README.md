# Isabella — AI Bookkeeping Agent

Isabella ingests receipts from Slack, extracts structured data using IBM Granite 3.3, appends to Google Sheets, and confirms via Slack. This repo includes a local deployment path using IBM watsonx Orchestrate Developer Edition.

## Quickstart (Local Developer Edition)

Requirements
- Python 3.11+, Docker Desktop (WSL2), Slack App (bot + app tokens), Google service account JSON

Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
pip install -U ibm-watsonx-orchestrate
```

Start Orchestrate and import agent
```powershell
orchestrate server start
orchestrate env activate local
orchestrate agents import -f agent.yaml
```

Run Slack Socket Mode listener
```powershell
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

Slack App
- Enable Socket Mode; scopes: chat:write, files:read, channels:history, app_mentions:read
- Add bot to your channel; upload a receipt to trigger the flow

Docs
- Deployment plan: `docs/deployment_plan.md`
- API reference: `docs/api_reference.md`
- Setup: `docs/setup.md`
- Orchestrate deployment (legacy cloud path): `docs/deployment.md`
- IBM watsonx integration details: `docs/watsonx-integration.md` 