# Tech Context

## Development Environment
- Language: Python 3.11+
- Platform: Windows PowerShell (C:\Users\HP\Isabella)
- Virtual Environment: `.venv`

## Core Technologies
- AI/LLM: IBM Granite 3.3 (`ibm/granite-3-3-8b-instruct`) via Watsonx API (IAM token → generation endpoint)
- Orchestrate: IBM watsonx Orchestrate Developer Edition (local Docker stack)
- Slack: Socket Mode (WebSocket) with `slack-bolt` and `slack-sdk`
- OCR: Tesseract via `pytesseract`, PDF via `pdfplumber`

## Integration Architecture
- Socket listener: `tools/slack_socket_runner.py` starts `SlackInterface` (SocketModeHandler)
- Slack file download: `tools/slack_interface.py` uses Slack WebClient `files_info` + `url_private_download` with Bearer token
- Controller orchestrates OCR → Granite → schema validation → Sheets
- Google Sheets via `gspread` and service account JSON path from env

## Configuration
- All secrets from environment (`.env`), loaded by the runner via `python-dotenv`
- Key vars: Slack `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`; Granite `WATSONX_API_KEY`, `WATSONX_URL`, `GRANITE_MODEL_ID`; Sheets `GOOGLE_SHEETS_*`; OCR `TESSERACT_CMD`, `TESSERACT_LANG`

## Testing
- pytest used locally (`pytest`, `pytest -m e2e`) [[memory:6125763]]

## Deployment
- Local: `orchestrate server start`, `orchestrate env activate local`, import `agent.yaml`, run socket runner
- Optional HTTP mode: ngrok tunnel to 4321 and Slack Request URLs → `/slack/events`, `/slack/actions` 