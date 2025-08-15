# Isabella — AI Bookkeeping Agent

**Status: M5 Deployment Complete ✅**  
*Local IBM watsonx Orchestrate Developer Edition + Slack Socket Mode + E2E Validated*

Isabella is a production-ready AI bookkeeping agent that ingests receipts from Slack, extracts structured data using IBM Granite 3.3, appends to Google Sheets, and confirms via Slack. This repository includes a complete local deployment path using IBM watsonx Orchestrate Developer Edition with Socket Mode Slack integration.

## 🚀 Quickstart (Local Developer Edition)

### Prerequisites
- **Python 3.11+** (check: `python --version`)
- **Docker Desktop** with WSL2 backend enabled (check: `docker --version`)
- **Slack App** with bot + app tokens configured
- **Google Service Account** JSON credentials
- **IBM Entitlement Key** for Developer Edition
- **IBM Watsonx API Key** for Granite 3.3 access

### Environment Setup
```powershell
# In project root: C:\Users\HP\Isabella
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
pip install -U ibm-watsonx-orchestrate
```

### Start IBM watsonx Orchestrate Developer Edition
```powershell
# Set Developer Edition environment variables
$env:WO_DEVELOPER_EDITION_SOURCE = "myibm"
$env:WO_ENTITLEMENT_KEY = "<YOUR_ENTITLEMENT_KEY>"
$env:WO_DEVELOPER_EDITION_SKIP_LOGIN = "false"

# Start local Orchestrate server (first run downloads Docker images)
orchestrate server start

# Activate local environment
orchestrate env activate local
orchestrate agents import -f agent.yaml
```

### Run Slack Socket Mode Listener
```powershell
# Start the Socket Mode listener (leave running)
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

### Slack App Configuration
- **Enable Socket Mode** (App-Level Token with `connections:write`)
- **Bot Token Scopes**: `chat:write`, `files:read`, `channels:history`, `app_mentions:read`
- **Event Subscriptions**: Subscribe to `app_mention`, `message.channels`, `file_shared`
- **Install app to workspace** and add bot to your channel
- **Upload a receipt** to trigger the complete E2E flow

## 🏗️ Architecture Overview

### Core Components
- **IBM Granite 3.3** (`ibm/granite-3-3-8b-instruct`): LLM for structured data extraction
- **IBM watsonx Orchestrate Developer Edition**: Local agent platform via Docker
- **Slack Socket Mode**: WebSocket-based event handling (no public HTTP required)
- **Google Sheets API**: Expense data persistence with header-driven mapping
- **Tesseract OCR**: Text extraction from images and PDFs

### Production Flow (Validated E2E)
1. **Slack File Upload** → `file_shared` event received via Socket Mode
2. **Text Extraction** → `tools/text_extractor.py` (OCR/PDF parsing)
3. **AI Processing** → `tools/receipt_processor.py` (Granite 3.3 JSON extraction)
4. **Schema Validation** → Validate against `data/schemas/receipt_schema.json`
5. **Data Persistence** → `tools/sheets_manager.py` (Google Sheets append)
6. **Confirmation** → Slack message: "✅ Your receipt has been added to Google Sheets"

### Integration Details
For comprehensive technical details on how IBM watsonx.ai (Granite) and IBM watsonx Orchestrate are integrated, see: **[`docs/watsonx-integration.md`](docs/watsonx-integration.md)**

## 📁 Project Structure

```
Isabella/
├── agent.yaml                    # Orchestrate agent definition (spec_version: v1)
├── tools/
│   ├── slack_socket_runner.py    # Socket Mode listener (production entrypoint)
│   ├── controller.py             # Main orchestration logic
│   ├── text_extractor.py         # OCR and PDF text extraction
│   ├── receipt_processor.py      # Granite 3.3 integration
│   ├── sheets_manager.py         # Google Sheets operations
│   └── slack_interface.py        # Slack event handling
├── models/
│   └── granite_client.py         # IBM Watsonx API client
├── integrations/
│   ├── google_sheets_api.py      # Google Sheets API wrapper
│   └── slack_api.py              # Slack API utilities
├── config/
│   ├── settings.py               # Environment configuration
│   └── prompts.py                # Granite prompts (single source of truth)
├── data/
│   ├── schemas/                  # JSON validation schemas
│   └── templates/                # Google Sheets templates
└── tests/                        # Comprehensive test suite
```

## 🔧 Configuration

### Environment Variables (`.env`)
All secrets and configuration are managed via environment variables:

**IBM Watsonx (Granite 3.3)**
- `WATSONX_API_KEY`: IBM Cloud IAM API key
- `WATSONX_PROJECT_ID`: Watsonx project identifier
- `WATSONX_URL`: Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`)
- `GRANITE_MODEL_ID`: Model identifier (`ibm/granite-3-3-8b-instruct`)

**Slack Integration**
- `SLACK_BOT_TOKEN`: Bot user OAuth token
- `SLACK_APP_TOKEN`: App-level token for Socket Mode
- `SLACK_SIGNING_SECRET`: Request verification secret
- `SLACK_CHANNEL_ID`: Target channel for confirmations

**Google Sheets**
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Service account JSON file path
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Target spreadsheet ID
- `GOOGLE_SHEETS_WORKSHEET_NAME`: Worksheet name for data

**OCR and Business Rules**
- `TESSERACT_CMD`: Tesseract executable path
- `TESSERACT_LANG`: OCR language (`eng`)
- `OCR_CONFIDENCE_THRESHOLD`: Minimum confidence score
- `DEFAULT_CURRENCY`: Default currency code
- `DUPLICATE_DETECTION_ENABLED`: Enable duplicate detection

## 🧪 Testing

### Run Test Suite
```powershell
# All tests
pytest

# End-to-end tests only
pytest -m e2e

# With coverage
pytest --cov=tools --cov=integrations --cov=models
```

### E2E Test with Custom Receipt
```powershell
# Set receipt URL for E2E test
$env:E2E_RECEIPT_URL="https://your-receipt-url.com/file.pdf"
pytest -m e2e -q
```

## 📚 Documentation

- **[Deployment Plan](docs/deployment_plan.md)**: Complete local deployment guide with troubleshooting
- **[IBM watsonx Integration](docs/watsonx-integration.md)**: Technical details on Granite + Orchestrate integration
- **[API Reference](docs/api_reference.md)**: Tool contracts and integration specifications
- **[Setup Guide](docs/setup.md)**: Initial project setup and configuration
- **[Legacy Cloud Deployment](docs/deployment.md)**: Cloud Orchestrate deployment (not used in current setup)

## 🔍 Observability and Monitoring

### Structured Logging
All components emit structured JSON logs with:
- `timestamp`: ISO 8601 timestamp
- `component`: Tool/component name
- `action`: Specific operation performed
- `correlation_id`: End-to-end request tracking
- `event`: Event type (success/error)
- `status`: Operation status
- `duration_ms`: Operation duration
- `error_type`: Error classification (if applicable)
- `error_message`: Detailed error description (if applicable)

### Audit Trail
- **Google Sheets**: All processed receipts with metadata
- **Slack Confirmations**: Timestamped confirmations with correlation IDs
- **Manual Review**: Approve/Reject decisions logged with actor and reason

### Monitoring Commands
```powershell
# Orchestrate server logs
orchestrate server logs

# Socket Mode listener logs (in separate terminal)
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

## 🚨 Troubleshooting

### Common Issues
1. **Docker resource allocation**: Ensure Docker Desktop has sufficient CPU/RAM
2. **Slack authentication**: Verify bot token and app token permissions
3. **Granite model access**: Check Watsonx API key and project access
4. **Google Sheets permissions**: Verify service account has write access

### Debug Commands
```powershell
# Check Orchestrate status
orchestrate server status
orchestrate env show active

# Verify agent import
orchestrate agents list

# Test Slack connection
# Upload a receipt and check logs
```

## 🔒 Security

- **No secrets in code**: All credentials via environment variables
- **Least privilege**: Minimal Slack scopes and Google Sheets permissions
- **Secure file handling**: Temporary file cleanup after processing
- **Token authentication**: All API calls use proper authentication

## 📈 Production Readiness

### Completed Features
- ✅ **E2E Flow Validation**: Complete receipt processing pipeline tested
- ✅ **Local Deployment**: IBM watsonx Orchestrate Developer Edition operational
- ✅ **Socket Mode Integration**: Slack events handled without public HTTP
- ✅ **Structured Logging**: JSON logs with correlation IDs
- ✅ **Error Handling**: Comprehensive retry mechanisms and error recovery
- ✅ **Schema Validation**: All LLM outputs validated against schemas
- ✅ **Duplicate Detection**: Vendor/amount/date comparison logic
- ✅ **Test Coverage**: Unit, integration, and E2E tests passing

### Pending Enhancements
- 🔄 **Interactive Manual Review**: Approve/Reject buttons for low-confidence receipts
- 🔄 **Enhanced Observability**: Duration metrics and performance monitoring
- 🔄 **HTTP Mode Support**: ngrok-based deployment option

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `pytest`
5. Update documentation as needed
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Deployment Status**: M5 Complete - Local IBM watsonx Orchestrate Developer Edition with Socket Mode Slack integration successfully deployed and validated end-to-end. Production flow operational with comprehensive observability and audit capabilities. 