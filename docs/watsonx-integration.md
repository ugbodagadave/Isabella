# IBM watsonx Integration (Granite + Orchestrate)

This document provides comprehensive technical details on how IBM watsonx.ai (Granite 3.3) and IBM watsonx Orchestrate (Developer Edition) are integrated within the Isabella AI bookkeeping agent. The deployment is operational with local IBM watsonx Orchestrate Developer Edition and Socket Mode Slack integration.

## Architecture Overview

### Core Components

#### 1. Granite Client (`models/granite_client.py`)
**Purpose:** Manages IBM Watsonx API interactions for Granite 3.3 model access

**Authentication Flow:**
- Obtains IAM access token from `https://iam.cloud.ibm.com/identity/token` using `WATSONX_API_KEY`
- Token cached in memory with automatic refresh when expired
- Uses IBM Cloud IAM authentication for secure API access

**API Integration:**
- Calls Text Generation endpoint: `{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29`
- Sends `model_id` (e.g., `ibm/granite-3-3-8b-instruct`) and `project_id` from environment
- Parses `generated_text` from response for structured data extraction
- Handles API errors and implements retry mechanisms

**Configuration:**
- `WATSONX_API_KEY`: IBM Cloud IAM API key for authentication
- `WATSONX_URL`: Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`)
- `WATSONX_PROJECT_ID`: Project identifier for model access
- `GRANITE_MODEL_ID`: Model identifier (`ibm/granite-3-3-8b-instruct`)

#### 2. IBM watsonx Orchestrate Developer Edition (Local)
**Purpose:** Provides the agent platform and UI for local deployment

**Local Deployment:**
- Runs as Docker containers: API, Redis, Postgres, MinIO
- Started via `orchestrate server start` command
- Local environment activated with `orchestrate env activate local`
- Agent imported using `orchestrate agents import -f agent.yaml`

**Agent Configuration:**
- `agent.yaml` with `spec_version: v1` for Developer Edition compatibility
- Skills mapped 1:1 to repository tools (no code duplication)
- Model hard-set to `ibm/granite-3-3-8b-instruct` for clarity
- Instructions reference `config/prompts.py` as single source of truth

**UI and API Access:**
- Local Orchestrate UI: `http://localhost:3000`
- Local API: `http://localhost:4321` with OpenAPI documentation
- Bearer token stored at `~/.cache/orchestrate/credentials.yaml`

#### 3. Slack Socket Mode Listener (`tools/slack_socket_runner.py`)
**Purpose:** Dedicated WebSocket listener for Slack events without public HTTP endpoints

**Implementation:**
- Uses `slack-bolt` and `SocketModeHandler` for WebSocket communication
- Loads environment variables via `python-dotenv` from project root `.env`
- Initializes all components: TextExtractor, GraniteClient, ReceiptProcessor, GoogleSheetsClient, SheetsManager, Controller, SlackInterface
- Runs as blocking process for continuous event handling

**Event Processing:**
- Receives `file_shared`, `app_mention`, `message.channels` events
- Routes events to appropriate handlers in `tools/slack_interface.py`
- Maintains persistent WebSocket connection to Slack

## Data Flow Architecture

### Complete Production Pipeline (Validated E2E)

#### 1. Slack File Upload Trigger
- User uploads receipt (image/PDF) to configured Slack channel
- Slack sends `file_shared` event via WebSocket to Socket Mode listener
- Event received by `tools/slack_socket_runner.py`

#### 2. File Download and Processing
- `tools/slack_interface.py` handles `file_shared` event
- Calls Slack WebClient `files_info` to get file metadata
- Downloads file using `url_private_download` with Bearer bot token authentication
- Creates temporary file with unique prefix and original filename
- Passes `local_path` and `receipt_link` to controller

#### 3. Text Extraction (OCR/PDF)
- `tools/text_extractor.py` processes the temporary file
- **Images:** Uses Tesseract OCR via `pytesseract` with image preprocessing
- **PDFs:** Uses `pdfplumber` for text extraction
- Returns extracted text with confidence scores
- Implements retry mechanisms for OCR failures

#### 4. AI-Powered Data Extraction
- `tools/receipt_processor.py` calls Granite 3.3 via `models/granite_client.py`
- Sends extracted text with prompts from `config/prompts.py`
- Granite 3.3 returns structured JSON with receipt data
- JSON validated against `data/schemas/receipt_schema.json`
- Implements retry mechanisms for API failures

#### 5. Data Persistence
- `tools/sheets_manager.py` processes validated JSON data
- Uses header-driven mapping from `data/templates/sheets_template.json`
- Appends data to Google Sheets via `integrations/google_sheets_api.py`
- Handles duplicate detection and error recovery

#### 6. User Confirmation
- Slack confirmation posted: "✅ Your receipt has been added to Google Sheets"
- Temporary file cleaned up automatically
- Correlation ID logged for audit trail

## Authentication and Security

### IBM Watsonx Authentication
- **IAM Token Management:** Automatic token refresh via IBM Cloud IAM
- **API Key Security:** `WATSONX_API_KEY` stored in environment variables only
- **Project Access:** `WATSONX_PROJECT_ID` ensures proper model access
- **Secure Communication:** All API calls use HTTPS with proper authentication

### Slack Integration Security
- **Bot Token Authentication:** All file downloads use bot token Bearer authentication
- **App Token Security:** Socket Mode uses app-level token for WebSocket connections
- **Request Verification:** `SLACK_SIGNING_SECRET` validates incoming requests
- **Least Privilege:** Minimal Slack scopes: `chat:write`, `files:read`, `channels:history`, `app_mentions:read`

### Google Sheets Security
- **Service Account:** JSON credentials loaded from environment variable path
- **API Permissions:** Service account has minimal required permissions
- **Secure Storage:** Credentials never logged or committed to repository
- **Access Control:** Spreadsheet access controlled via service account permissions

## Observability and Monitoring

### Structured Logging
All components emit structured JSON logs with:
- `timestamp`: ISO 8601 timestamp for event tracking
- `component`: Tool/component name for log categorization
- `action`: Specific operation performed
- `correlation_id`: End-to-end request tracking across all components
- `event`: Event type (success/error/info)
- `status`: Operation status (completed/failed/pending)
- `duration_ms`: Operation duration for performance monitoring
- `error_type`: Error classification for monitoring and alerting
- `error_message`: Detailed error description (if applicable)

### Audit Trail
- **Google Sheets Persistence:** All processed receipts with metadata
- **Slack Confirmations:** Timestamped confirmations with correlation IDs
- **Manual Review Decisions:** Approve/Reject decisions logged with actor and reason
- **Processing History:** Complete audit trail of all receipt processing activities

### Performance Metrics
- **OCR Duration:** Text extraction performance tracking
- **LLM Duration:** Granite 3.3 API response times
- **Sheets Duration:** Google Sheets API operation times
- **E2E Duration:** Complete pipeline performance monitoring
- **Error Rates:** Failure tracking across all components

## Socket Mode vs HTTP Mode

### Socket Mode (Current Implementation)
**Advantages:**
- No public HTTP endpoints required
- Secure WebSocket communication
- No ngrok or public tunnel needed
- Simplified deployment and configuration
- Real-time event handling

**Implementation:**
- `tools/slack_socket_runner.py` runs as dedicated process
- `SocketModeHandler` maintains persistent WebSocket connection
- Events received directly from Slack without HTTP callbacks
- File downloads handled via Slack WebClient with bot token

### HTTP Mode (Optional Alternative)
**Use Cases:**
- Alternative deployment scenarios
- Integration with existing HTTP infrastructure
- Load balancing and scaling requirements

**Implementation:**
- ngrok tunnel to expose local Orchestrate API (`http://localhost:4321`)
- Slack Event Subscriptions configured with ngrok URLs
- Request URLs: `/slack/events` and `/slack/actions`
- Requires public HTTPS endpoint for Slack callbacks

## Error Handling and Resilience

### Retry Mechanisms
- **Tenacity Library:** Exponential backoff for external API calls
- **Granite API:** Automatic retry for temporary API failures
- **Google Sheets API:** Retry mechanisms for network issues
- **OCR Processing:** Retry for temporary OCR failures

### Error Classification
- **Network Errors:** Temporary connectivity issues
- **Authentication Errors:** Token expiration or invalid credentials
- **Validation Errors:** Schema validation failures
- **Processing Errors:** OCR or LLM processing failures
- **Permission Errors:** Access control issues

### Graceful Degradation
- **Service Continuity:** System continues operating with reduced functionality
- **User Feedback:** Clear error messages posted to Slack
- **Error Recovery:** Automatic recovery mechanisms where possible
- **Manual Intervention:** Clear guidance for manual resolution

## Configuration Management

### Environment Variables
All configuration managed via environment variables loaded from `.env`:

**IBM Watsonx Configuration:**
- `WATSONX_API_KEY`: IBM Cloud IAM API key
- `WATSONX_PROJECT_ID`: Watsonx project identifier
- `WATSONX_URL`: Watsonx service URL
- `GRANITE_MODEL_ID`: Model identifier

**Slack Configuration:**
- `SLACK_BOT_TOKEN`: Bot user OAuth token
- `SLACK_APP_TOKEN`: App-level token for Socket Mode
- `SLACK_SIGNING_SECRET`: Request verification secret
- `SLACK_CHANNEL_ID`: Target channel identifier

**Google Sheets Configuration:**
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Service account JSON path
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Spreadsheet identifier
- `GOOGLE_SHEETS_WORKSHEET_NAME`: Worksheet name

**OCR and Business Rules:**
- `TESSERACT_CMD`: Tesseract executable path
- `TESSERACT_LANG`: OCR language configuration
- `OCR_CONFIDENCE_THRESHOLD`: Minimum confidence score
- `DEFAULT_CURRENCY`: Default currency code
- `DUPLICATE_DETECTION_ENABLED`: Duplicate detection flag

### Developer Edition Configuration
- `WO_DEVELOPER_EDITION_SOURCE`: Source configuration
- `WO_ENTITLEMENT_KEY`: IBM entitlement key
- `WO_DEVELOPER_EDITION_SKIP_LOGIN`: Login configuration

## Security Notes

### Data Protection
- **No Secrets in Code:** All credentials managed via environment variables
- **Secure File Handling:** Temporary files cleaned up after processing
- **Token Management:** IAM tokens cached securely with automatic refresh
- **Least Privilege:** Minimal permissions for all external services

### Network Security
- **Local Deployment:** All services running locally in Docker containers
- **Socket Mode:** WebSocket communication without public HTTP exposure
- **Secure APIs:** All external API calls use HTTPS with proper authentication
- **No Public Endpoints:** No public HTTP endpoints required for operation

### Access Control
- **Service Accounts:** Google Sheets access via dedicated service account
- **Bot Permissions:** Slack access via bot user with minimal scopes
- **IAM Authentication:** IBM Watsonx access via IAM tokens
- **Environment Isolation:** Development environment isolated from production

## Deployment Status

### Current Operational Status
- ✅ **Local Deployment:** IBM watsonx Orchestrate Developer Edition operational
- ✅ **Socket Mode Integration:** Slack events handled via WebSocket
- ✅ **E2E Flow Validation:** Complete pipeline tested and operational
- ✅ **Documentation:** Comprehensive technical documentation completed
- ✅ **Testing:** All tests passing (unit, integration, E2E)

### Production Readiness
- ✅ **Security:** All security requirements implemented
- ✅ **Observability:** Structured logging and monitoring operational
- ✅ **Error Handling:** Comprehensive error handling and recovery
- ✅ **Configuration:** Environment-driven configuration management
- ✅ **Testing:** Complete test coverage with validation

The Isabella AI bookkeeping agent is now fully operational with local IBM watsonx Orchestrate Developer Edition deployment and Socket Mode Slack integration, providing enterprise-grade security, observability, and reliability for automated receipt processing. 