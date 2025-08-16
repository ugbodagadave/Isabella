# Setup Guide

## Overview
Isabella is an AI bookkeeping agent that processes receipts via Slack, extracts structured data using IBM Granite 3.3, and manages expenses in Google Sheets. The project follows a strict Test → Document → Commit → Push workflow.

## Prerequisites
- Python 3.11+
- IBM Watsonx account with Granite 3.3 access
- Google Sheets API credentials
- Slack App with bot token and event subscriptions
- Tesseract OCR (only required if you set `OCR_BACKEND=tesseract` for legacy OCR or tests)

## Installation

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create `.env` based on `.env.sample` and configure all required variables:

**IBM Watsonx / Granite:**
- `WATSONX_API_KEY` - Your IBM Watsonx API key
- `WATSONX_PROJECT_ID` - Watsonx project identifier
- `WATSONX_URL` - Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`)
- `GRANITE_MODEL_ID` - Granite model (default: `ibm/granite-3-3-8b-instruct`)

**Google Sheets:**
- `GOOGLE_SHEETS_CREDENTIALS_PATH` - Path to service account JSON
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Target spreadsheet ID
- `GOOGLE_SHEETS_WORKSHEET_NAME` - Worksheet name (default: `Sheet1`)

**Slack:**
- `SLACK_BOT_TOKEN` - Bot user OAuth token
- `SLACK_APP_TOKEN` - App-level token (starts with `xapp-`)
- `SLACK_SIGNING_SECRET` - App signing secret
- `SLACK_CHANNEL_ID` - Default channel for notifications

**Vision OCR / Processing:**
- Images use vision chat via `meta-llama/llama-3-2-11b-vision-instruct` (IBM watsonx)
- PDFs use `pdfplumber` (no vision)
- To force legacy OCR for tests, set `OCR_BACKEND=tesseract`
- Logs include a redacted transcript preview to aid debugging

**Business Rules:**
- `DEFAULT_CURRENCY` - Default currency (default: `USD`)
- `TIMEZONE` - Timezone for dates (default: `America/New_York`)
- `TOP_VENDORS_LIMIT` - Max vendors in summaries (default: `5`)

### 3. Google Credentials
Place your Google service account JSON at `./config/google-credentials.json`

### 4. Google Sheets Setup
Ensure your target Google Sheet has the header row from `data/templates/sheets_template.json`:
- Date, Vendor, Amount, Category, Description, Receipt_Link, Payment_Method, Receipt_Number, Tax_Amount, Location, Processed_Date, Confidence_Score

## Testing

### Unit and Integration Tests
```bash
# Run all tests
pytest -q

# Run with coverage
pytest --cov
```

### Live End-to-End Tests
E2E tests use real integrations (Granite, Google Sheets, Slack) and are marked with `@pytest.mark.e2e`.

**Prerequisites for E2E:**
- All environment variables configured
- Google Sheet with headers created
- Slack bot with `files:read` scope

**Running E2E tests:**
```bash
# Run only E2E tests
pytest -m e2e -q

# Provide receipt via environment variable
$env:E2E_RECEIPT_PATH = "path/to/receipt.pdf"
# OR
$env:E2E_RECEIPT_URL = "https://drive.google.com/uc?export=download&id=..."
```

**E2E Test Flow:**
1. Downloads receipt from path/URL
2. Extracts text via vision chat (or OCR if `OCR_BACKEND=tesseract`)
3. Processes with Granite 3.3 LLM
4. Validates JSON against schema
5. Appends to Google Sheets with correlation ID
6. Posts confirmation to Slack: "✅ Your receipt has been added to Google Sheets"

**Note:** E2E tests write a row with `Description=E2E_TEST` to your sheet for validation.

## Development Workflow

### Test → Document → Commit → Push
1. **Test:** Run `pytest -q` to ensure all tests pass
2. **Document:** Update relevant documentation
3. **Commit:** Stage and commit changes
4. **Push:** Push to remote repository

```bash
# Complete workflow
pytest -q
git add .
git commit -m "feat/fix/docs: description"
git push origin main
```

## Current Status
- ✅ M0-M3: Core tools, integrations, and end-to-end flow completed
- ✅ M4: Query flow with natural language processing completed
- 🔄 M5: Deployment with IBM Watsonx Orchestrate ADK (next phase)

## Troubleshooting

### Common Issues
- **Vision chat errors:** verify `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and that images are sent as data URIs
- **OCR failures (legacy):** Ensure Tesseract is installed and `TESSERACT_CMD` is correct
- **Granite API errors:** Verify `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`
- **Google Sheets errors:** Check service account permissions and spreadsheet access
- **Slack errors:** Verify bot token and app permissions. If you see Slack `no_text` errors in logs, ensure you are on the latest code and that `verify_tokens=True` in `tools/slack_socket_runner.py` (production mode). Restart the listener and retry.

### Debug Mode
Enable debug logging by setting log level in your environment or code.

## Next Steps
After setup, proceed to M5 deployment using IBM Watsonx Orchestrate ADK. See `docs/deployment.md` for detailed deployment instructions. 