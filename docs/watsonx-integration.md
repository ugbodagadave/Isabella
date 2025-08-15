# IBM watsonx Integration (Granite + Orchestrate)

This document explains the technical integration between IBM watsonx.ai (Granite 3.3) and IBM watsonx Orchestrate (Developer Edition) used by Isabella.

## Components
- Granite Client (`models/granite_client.py`):
  - Obtains IAM access token from `https://iam.cloud.ibm.com/identity/token` using `WATSONX_API_KEY` (IBM Cloud IAM).
  - Calls Text Generation at `{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29`.
  - Sends `model_id` (e.g., `ibm/granite-3-3-8b-instruct`) and `project_id` from environment.
  - Parses `generated_text` from response.
- Orchestrate Developer Edition (local):
  - Provides the Agent UI and platform services via Docker stack.
  - We import our `agent.yaml` (spec_version v1). The UI “LLM” display is informational. Business logic lives in repo tools.
- Slack Socket Mode listener (`tools/slack_socket_runner.py`):
  - Uses `slack-bolt` and `SocketModeHandler` to receive events without public HTTP.
  - `tools/slack_interface.py` fetches `file_shared` metadata via Slack Web API and downloads the file to a temp path using bot token.

## Data Flow
1. User uploads a file in Slack.
2. Socket listener receives `file_shared` → downloads using `url_private_download` with Bearer bot token.
3. `Controller.handle_file_shared`:
   - OCR via `TextExtractor` (Tesseract for images, pdfplumber for PDFs)
   - LLM via `GraniteClient.generate()` with prompts from `config/prompts.py`
   - JSON schema validation (`data/schemas/receipt_schema.json`)
   - Google Sheets append via `integrations/google_sheets_api.py`
4. Slack confirmation: “✅ Your receipt has been added to Google Sheets”.

## Authentication and Secrets
- Environment variables only (loaded by `python-dotenv` in the runner):
  - Watsonx: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `GRANITE_MODEL_ID`
  - Slack: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_CHANNEL_ID`
  - Sheets: `GOOGLE_SHEETS_CREDENTIALS_PATH`, `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_WORKSHEET_NAME`
  - OCR/Rules: `TESSERACT_CMD`, `TESSERACT_LANG`, `OCR_CONFIDENCE_THRESHOLD`, etc.
- Secrets are never printed; Slack file downloads use token-authenticated URLs.

## Observability and Audit
- Add structured logs per step: timestamp, component, action, correlation_id, event, status, duration_ms, error_type, error_message.
- Audit in Sheets: Date, Vendor, Amount, Category, Description, Receipt_Link, Processed_Date, Confidence_Score; include Slack confirmation timestamp in Description suffix when available.

## Socket Mode vs HTTP mode
- Socket Mode (current): no public endpoint; start `tools/slack_socket_runner.py` and subscribe to events in Slack App settings.
- HTTP mode (optional): expose `http://localhost:4321` with ngrok and set Slack Event/Interactivity Request URLs (`/slack/events`, `/slack/actions`). Not required when Socket Mode is used.

## Error Handling
- Retries with tenacity in controller for OCR/LLM/Sheets operations.
- Slack download guarded; posts user-friendly errors.

## Security Notes
- IAM tokens cached in memory, refreshed automatically.
- Least-privilege Slack scopes.
- Service account credentials path from env; never logged or committed. 