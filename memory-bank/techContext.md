# Tech Context

## Development Environment
- **Language:** Python 3.11+
- **Platform:** Windows PowerShell (C:\Users\HP\Isabella)
- **Virtual Environment:** `.venv`
- **Deployment:** Local IBM watsonx Orchestrate Developer Edition

## Core Technologies

### AI/LLM Stack
- **IBM Granite 3.3:** `ibm/granite-3-3-8b-instruct` via Watsonx API
- **Authentication:** IAM token management with automatic refresh
- **API Endpoint:** Text generation at `{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29`
- **Project Integration:** Uses `WATSONX_PROJECT_ID` for model access

### Orchestration Platform
- **IBM watsonx Orchestrate Developer Edition:** Local Docker-based deployment
- **Container Services:** API, Redis, Postgres, MinIO running in Docker containers
- **Local Environment:** `orchestrate env activate local` for development
- **Agent Import:** `agent.yaml` with `spec_version: v1` imported into local instance
- **UI Access:** Local Orchestrate UI at `http://localhost:3000`

### Slack Integration
- **Socket Mode:** WebSocket-based event handling with `slack-bolt` and `slack-sdk`
- **Event Types:** `file_shared`, `app_mention`, `message.channels`
- **File Processing:** `tools/slack_interface.py` uses Slack WebClient for file downloads
- **Authentication:** Bot token used for `files_info` and `url_private_download` operations
- **No Public HTTP:** Socket Mode eliminates need for public endpoints

### OCR and Document Processing
- **Tesseract:** OCR processing via `pytesseract` for image text extraction
- **PDF Processing:** PDF parsing via `pdfplumber` for document text extraction
- **Image Preprocessing:** OpenCV-based image enhancement for OCR accuracy
- **Language Support:** Configurable via `TESSERACT_LANG` environment variable

### Data Persistence
- **Google Sheets API:** `gspread` library for spreadsheet operations
- **Service Account:** JSON credentials loaded from environment variable path
- **Header-driven Mapping:** Uses `data/templates/sheets_template.json` for column mapping
- **Canonical Columns:** Date, Vendor, Amount, Category, Description, Receipt_Link, Processed_Date, Confidence_Score

## Integration Architecture

### Socket Mode Listener
- **Entry Point:** `tools/slack_socket_runner.py` starts dedicated Socket Mode listener
- **Environment Loading:** `python-dotenv` loads environment variables from `.env`
- **Component Initialization:** TextExtractor, GraniteClient, ReceiptProcessor, GoogleSheetsClient, SheetsManager, Controller, SlackInterface
- **Event Handling:** `SocketModeHandler` receives events and routes to appropriate handlers

### Slack File Processing
- **Event Reception:** `file_shared` events trigger file download process
- **File Information:** `tools/slack_interface.py` calls `files_info` to get file metadata
- **Download Process:** Uses `url_private_download` with Bearer token authentication
- **Temporary Storage:** Files downloaded to temp paths with automatic cleanup
- **Controller Integration:** `local_path` and `receipt_link` passed to controller for processing

### Controller Orchestration
- **Main Coordinator:** `tools/controller.py` orchestrates complete receipt processing flow
- **Pipeline Management:** OCR → Granite → schema validation → Sheets → Slack confirmation
- **Error Handling:** Tenacity-based retries for external API calls
- **Correlation IDs:** End-to-end request tracking across all components
- **Duplicate Detection:** Vendor/amount/date comparison logic

### Google Sheets Integration
- **Client Initialization:** `integrations/google_sheets_api.py` manages API client
- **Authentication:** Service account JSON loaded from `GOOGLE_SHEETS_CREDENTIALS_PATH`
- **Header Management:** Automatic header initialization and validation
- **Data Mapping:** Header-driven mapping using predefined templates
- **Error Recovery:** Retry mechanisms for API failures

## Configuration Management

### Environment Variables
All configuration managed via environment variables loaded from `.env`:

**IBM Watsonx (Granite 3.3)**
- `WATSONX_API_KEY`: IBM Cloud IAM API key for authentication
- `WATSONX_PROJECT_ID`: Watsonx project identifier for model access
- `WATSONX_URL`: Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`)
- `GRANITE_MODEL_ID`: Model identifier (`ibm/granite-3-3-8b-instruct`)

**Slack Integration**
- `SLACK_BOT_TOKEN`: Bot user OAuth token for API operations
- `SLACK_APP_TOKEN`: App-level token for Socket Mode connections
- `SLACK_SIGNING_SECRET`: Request verification secret for security
- `SLACK_CHANNEL_ID`: Target channel for confirmations and notifications

**Google Sheets**
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Service account JSON file path
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Target spreadsheet identifier
- `GOOGLE_SHEETS_WORKSHEET_NAME`: Worksheet name for data operations

**OCR and Business Rules**
- `TESSERACT_CMD`: Tesseract executable path for OCR processing
- `TESSERACT_LANG`: OCR language configuration (`eng`)
- `OCR_CONFIDENCE_THRESHOLD`: Minimum confidence score for OCR results
- `IMAGE_PREPROCESSING`: Image enhancement configuration
- `DEFAULT_CURRENCY`: Default currency code for expense processing
- `TIMEZONE`: Timezone configuration for date processing
- `AUTO_CATEGORIZATION_ENABLED`: Automatic category assignment
- `DUPLICATE_DETECTION_ENABLED`: Duplicate detection feature flag
- `REQUIRE_APPROVAL`: Manual approval requirement flag
- `TOP_VENDORS_LIMIT`: Limit for vendor summary queries (default: 5)

### Developer Edition Configuration
- `WO_DEVELOPER_EDITION_SOURCE`: Source configuration (`myibm`)
- `WO_ENTITLEMENT_KEY`: IBM entitlement key for Developer Edition
- `WO_DEVELOPER_EDITION_SKIP_LOGIN`: Login configuration flag

## Testing Framework

### Test Types
- **Unit Tests:** Component-level testing with mocked external services
- **Integration Tests:** Service integration testing with mocked APIs
- **End-to-End Tests:** Complete pipeline validation with real or test data
- **Test Execution:** pytest used locally (`pytest`, `pytest -m e2e`)

### Test Configuration
- **Environment Loading:** Proper environment variable loading for test sessions
- **Test Isolation:** `_test_mode` flag for Slack interface to bypass real API calls
- **Mock Services:** External API calls mocked for reliable testing
- **E2E Configuration:** Custom receipt URLs via `E2E_RECEIPT_URL` environment variable

## Deployment Architecture

### Local Development Deployment
- **Orchestrate Server:** `orchestrate server start` launches local Docker containers
- **Environment Activation:** `orchestrate env activate local` sets local environment
- **Agent Import:** `orchestrate agents import -f agent.yaml` imports agent definition
- **Socket Mode Listener:** `tools/slack_socket_runner.py` runs as dedicated process

### Production Flow
1. **Slack File Upload:** User uploads receipt to configured Slack channel
2. **Socket Mode Event:** `file_shared` event received by Socket Mode listener
3. **File Download:** File downloaded using Slack WebClient with bot token
4. **Text Extraction:** OCR or PDF parsing performed on downloaded file
5. **AI Processing:** Granite 3.3 extracts structured JSON from text
6. **Schema Validation:** JSON validated against predefined schemas
7. **Data Persistence:** Structured data appended to Google Sheets
8. **User Confirmation:** Slack confirmation message posted to channel

### Monitoring and Observability
- **Structured Logging:** JSON logs with correlation IDs and duration metrics
- **Error Tracking:** Comprehensive error handling and classification
- **Performance Monitoring:** Duration tracking across all processing steps
- **Audit Trail:** Complete audit trail in Google Sheets with metadata

## Security Considerations

### Authentication and Authorization
- **IAM Tokens:** IBM Watsonx API access via IAM tokens with automatic refresh
- **Service Accounts:** Google Sheets access via service account JSON
- **Bot Tokens:** Slack API access via bot user OAuth tokens
- **Least Privilege:** Minimal permissions for all external services

### Data Security
- **Environment Variables:** All secrets managed via environment variables
- **Temporary Files:** Secure file handling with automatic cleanup
- **No Secrets in Code:** No credentials hardcoded in source code
- **Secure Communication:** All API calls use proper authentication

### Network Security
- **Socket Mode:** WebSocket-based communication (no public HTTP required)
- **Local Deployment:** All services running locally in Docker containers
- **No Public Exposure:** No public endpoints required for operation 