# Isabella M5 Deployment Plan — Local Developer Edition + ngrok (No Cloud Orchestrate)

This plan deploys Isabella locally using IBM watsonx Orchestrate Developer Edition and exposes the local agent to Slack via ngrok. It is designed for hackathon or restricted accounts where Orchestrate SaaS and watsonx.ai Deployment Spaces are unavailable. The runtime flow, tool contracts, and prompts remain EXACTLY the same as the E2E tests.

Primary reference:
- IBM docs: Getting started with IBM watsonx Orchestrate — `https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate`
- Developer Edition (local): Installing and running on developer/on‑prem `https://developer.watson-orchestrate.ibm.com/getting_started/installing#on-premises`
- Guide with local server details and examples: `https://ruslanmv.com/blog/hello-watsonx-orchestrate`

---

## What you’ll run

- IBM watsonx Orchestrate Developer Edition locally (Docker containers for core services like API, Redis, Postgres)
- Your agent skills mapped 1:1 to repo tools (no code duplication of prompts)
- Slack events routed to your local Orchestrate via ngrok
- Observability: structured JSON logs with correlation IDs
- Manual review path via Slack interactive buttons

The E2E production flow is unchanged:
1) `tools/text_extractor.py` → OCR/PDF text
2) `tools/receipt_processor.py` → Granite 3.3 JSON → validate with `data/schemas/receipt_schema.json`
3) `tools/sheets_manager.py` → append to Google Sheets using `data/templates/sheets_template.json`
4) Slack confirmation: "✅ Your receipt has been added to Google Sheets"
5) If low confidence / schema fail / ambiguous duplicate → Manual Review (Approve/Reject) before append

---

## Prerequisites and Downloads [ACTION REQUIRED]

Windows 10/11 (PowerShell) with admin rights.

- Python 3.11+
  - Check: `python --version`
- Git (optional but recommended)
- Docker Desktop with WSL2 backend enabled
  - Check: `docker --version` and `docker compose version`
  - Resources: allocate at least 4 CPU / 6–8 GB RAM / 20+ GB disk
- ngrok account and CLI
  - Download: `https://ngrok.com/download`
  - Login and get your auth token
- IBM Entitlement Key (Developer Edition)
  - Get from My IBM (used to pull Developer Edition images and run locally)
- Existing credentials (already in your `.env` per your screenshot):
  - IBM Granite: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `GRANITE_MODEL_ID`
  - Google Sheets: `GOOGLE_SHEETS_CREDENTIALS_PATH`, `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_WORKSHEET_NAME`
  - Slack: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_CHANNEL_ID`
  - OCR/Rules: `TESSERACT_CMD`, `TESSERACT_LANG`, `OCR_CONFIDENCE_THRESHOLD`, `IMAGE_PREPROCESSING`
  - Business: `DEFAULT_CURRENCY`, `TIMEZONE`, `AUTO_CATEGORIZATION_ENABLED`, `DUPLICATE_DETECTION_ENABLED`, `REQUIRE_APPROVAL`, `TOP_VENDORS_LIMIT`

Notes
- The prior cloud error was due to Orchestrate SaaS API key restrictions (WXO API). Developer Edition avoids that by running locally.
- Keep secrets out of logs and code. Use your existing `.env` as-is.

---

## Step 1 — Python environment and ADK install [ACTION REQUIRED]

```powershell
# In project root: C:\Users\HP\Isabella
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
# Install ADK (Agent Development Kit)
pip install -U ibm-watsonx-orchestrate
```

Verify ADK:
```powershell
orchestrate --version
```

---

## Step 2 — Configure Developer Edition (local) [ACTION REQUIRED]

You will run Orchestrate locally via Docker. Ensure Docker Desktop is running.

1) Add Developer Edition parameters to your environment (do NOT commit values):

- Entitlement key (required by Developer Edition)
- Continue to use your existing `WATSONX_API_KEY` and `WATSONX_URL` for Granite models

For local runs, you can either place these in a separate PowerShell profile or export them before starting the server. Example (PowerShell session only):
```powershell
$env:WO_DEVELOPER_EDITION_SOURCE = "myibm"
$env:WO_ENTITLEMENT_KEY = "<YOUR_ENTITLEMENT_KEY>"
$env:WO_DEVELOPER_EDITION_SKIP_LOGIN = "false"
# Granite access
$env:WATSONX_API_KEY = $env:WATSONX_API_KEY   # already set from your .env tooling
$env:WATSONX_URL = $env:WATSONX_URL           # e.g., https://us-south.ml.cloud.ibm.com
$env:GRANITE_MODEL_ID = $env:GRANITE_MODEL_ID # e.g., ibm/granite-3-3-8b-instruct
```

2) Start local Orchestrate server (first run downloads Docker images — be patient):
```powershell
orchestrate server start
```

Useful checks:
```powershell
orchestrate server status
orchestrate server logs | cat
```

Stop later with:
```powershell
orchestrate server stop
```

---

## Step 3 — Activate local environment [ACTION REQUIRED]

Developer Edition ships with a built‑in local target.
```powershell
orchestrate env list
orchestrate env activate local
orchestrate env show active
```

This avoids the WXO API key flow entirely. If you previously added a remote env, it’s fine — just ensure `local` is active.

---

## Step 4A — Slack Socket Mode (recommended; no ngrok) [ACTION REQUIRED]

Slack delivers events over WebSocket; no public HTTP needed.

Slack app configuration:
- Enable Socket Mode (App-Level Token with `connections:write`)
- Bot token scopes: `chat:write`, `files:read`, `channels:history`, `app_mentions:read`
- Event Subscriptions: subscribe to `app_mention`, `message.channels`, `file_shared` (no Request URL required in Socket Mode)
- Install app to workspace and add bot to the channel (`SLACK_CHANNEL_ID`)

Start the Socket Mode listener:
```powershell
# From project root
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```
Leave this running to receive events.

---

## Step 4B — HTTP mode via ngrok (optional) [SKIP if using Socket Mode]

Slack needs to reach your local Orchestrate over the public internet.

1) Authenticate ngrok:
```powershell
ngrok config add-authtoken <YOUR_NGROK_AUTH_TOKEN>
```

2) Start a tunnel to the Orchestrate API (port 4321):
```powershell
ngrok http 4321
```

3) Copy the https forwarding URL, e.g., `https://abcd-1234.ngrok-free.app`

4) Configure your Slack App (in Slack API dashboard):
- Scopes: `chat:write`, `files:read` (if needed), `channels:history`, `app_mentions:read`
- Event Subscriptions → Request URL:
  - `https://<your-ngrok-domain>/slack/events`
- Interactivity → Request URL:
  - `https://<your-ngrok-domain>/slack/actions`
- Install app to workspace; add bot to target channels

Your `agent.yaml` already declares a Slack channel; local Orchestrate will route inbound events to your `tools/controller.py`/`tools/slack_interface.py` skills.

---

## Step 5 — Deploy the local agent [ACTION REQUIRED]

Use the existing `agent.yaml` at project root (already updated to use `${GRANITE_MODEL_ID}` and include `controller`).
```powershell
# From project root
orchestrate agent deploy -f agent.yaml
```

Optional: start the lite chat for quick manual tests
```powershell
orchestrate chat start
# Open http://localhost:3000/chat-lite
```

Open local OpenAPI docs for the Developer Edition at
- `http://localhost:4321/docs`

Bearer token (if you call local APIs programmatically) is stored at
- `~/.cache/orchestrate/credentials.yaml`

---

## Step 6 — Production‑like validation on local [ACTION REQUIRED]

Smoke test via Slack
- Upload a known test receipt (PDF/image) to the channel your bot is in
- Expect a new row in your Google Sheet and a Slack confirmation:
  - "✅ Your receipt has been added to Google Sheets"

Functional checks
- Manual review trigger: use a low‑quality image or set a low `OCR_CONFIDENCE_THRESHOLD` and confirm Approve/Reject path works
- Queries: ask vendor/period summaries (respect `TOP_VENDORS_LIMIT`)

Automated tests (local) [[memory:6125763]]
```powershell
pytest -q
pytest -m e2e -q
```

Observability
- Ensure structured JSON logs include: timestamp, component, action, correlation_id, event, status, duration_ms, error_type, error_message
- Derived metrics from logs: `ocr_duration_ms`, `llm_duration_ms`, `sheets_append_ms`, `duplicates_detected`, `schema_validation_errors`, `e2e_success_rate`

Audit trail
- Persist: Date, Vendor, Amount, Category, Description, Receipt_Link, Processed_Date, Confidence_Score
- Add Slack confirmation ts in `Description` suffix `CONFIRM_TS=<ts>` (or later add a column)

---

## Troubleshooting (Local)

- Server won’t start / image pull issues
  - Confirm Docker Desktop is running and you’re logged in if required
  - Ensure `WO_ENTITLEMENT_KEY` is set in the session before `orchestrate server start`
- Slack 401/403 on events
  - Double‑check `SLACK_SIGNING_SECRET` and the Request URLs to your ngrok https domain
  - Ensure bot is a member of the channel
- Granite model access errors
  - Validate `WATSONX_API_KEY`, `WATSONX_URL`, `GRANITE_MODEL_ID`
- Nothing happens on upload
  - Check `orchestrate server logs | cat`
  - Verify `orchestrate env show active` prints `local`
  - Confirm ngrok is pointing to 4321 and events are hitting `/slack/events`

---

## Operations Runbook (Local)

Reprocess by correlation_id
1. Search structured logs for `correlation_id` to recover `Receipt_Link`
2. Repost the `Receipt_Link` in Slack or use a local API call with the bearer token

Manual approvals
- Reviewers get interactive Approve/Reject; decisions are logged with actor, timestamp, correlation_id

Credential rotation
- Update env values in your local shell or secret store; restart server if needed

Incident response
- Use logs to trace OCR → LLM → Sheets → Slack via `correlation_id`
- Remove incorrect rows directly in the Sheet and record the corrective action

---

## Rollback and Safety

- Feature‑gate: set `REQUIRE_APPROVAL=true` to force review for all receipts during incidents
- Keep a copy of your working `agent.yaml` and dependency versions
- If server becomes unstable, `orchestrate server stop` then `orchestrate server start`

---

## Security Notes

- Never print or commit secrets (Slack tokens, API keys, entitlement key)
- Only log non‑sensitive context with correlation IDs
- Grant only required scopes to the Slack app and minimum permissions to the Google service account

---

## Appendix — Reference Commands

Env and server
```powershell
orchestrate --version
orchestrate server start
orchestrate server status
orchestrate server logs | cat
orchestrate server stop
orchestrate env list
orchestrate env activate local
orchestrate env show active
```

Agent
```powershell
orchestrate agent deploy -f agent.yaml
```

Chat and docs
```powershell
orchestrate chat start
# http://localhost:3000/chat-lite
# http://localhost:4321/docs
```

ngrok
```powershell
ngrok config add-authtoken <YOUR_NGROK_AUTH_TOKEN>
ngrok http 4321
```

Slack URLs (configure in Slack app)
- Events Request URL: `https://<ngrok-domain>/slack/events`
- Interactivity URL: `https://<ngrok-domain>/slack/actions`

---

This local Developer Edition plan is the source of truth for M5 under hackathon/restricted accounts. It implements the same flow, observability, audit, and manual review behaviors; only the orchestration runtime changes from cloud to local with ngrok exposure. 