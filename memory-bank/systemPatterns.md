# System Patterns

## Core Architecture
- **LLM-first Design:** Granite 3.3 (`ibm/granite-3-3-8b-instruct`) for receipt understanding and structured data extraction
- **Local Orchestration:** IBM watsonx Orchestrate Developer Edition running locally via Docker containers
- **Event-Driven Processing:** Controller manages complete OCR → LLM → validation → Sheets → Slack pipeline
- **Runtime Architecture:** Local Orchestrate Developer Edition provides agent UI; Slack events handled by dedicated Socket Mode listener
- **Production Flow:** Validated end-to-end receipt processing with real integrations

## Deployment Architecture

### IBM watsonx Orchestrate Developer Edition (Local)
- **Docker-based Deployment:** Core services (API, Redis, Postgres, MinIO) running in containers
- **Local Environment:** `orchestrate env activate local` for development and testing
- **Agent Import:** `agent.yaml` with `spec_version: v1` imported into local Orchestrate instance
- **UI Access:** Local Orchestrate UI available at `http://localhost:3000` for agent management
- **API Access:** Local API available at `http://localhost:4321` with OpenAPI documentation

### Socket Mode Integration
- **WebSocket-based Events:** Slack events received via `SocketModeHandler` without public HTTP endpoints
- **Dedicated Listener:** `tools/slack_socket_runner.py` runs as standalone process for event handling
- **File Processing:** `file_shared` events trigger download → temp file → controller processing
- **Authentication:** Bot token used for file downloads via `url_private_download` with Bearer authentication
- **Security:** No public HTTP exposure required; all communication via secure WebSocket

## Event Handling
- **Slack Socket Mode:** `SocketModeHandler` receives events; `file_shared` triggers download → temp file → controller `handle_file_shared`
- **Message Events:** Route to controller `handle_query` for natural language processing
- **File Downloads:** `tools/slack_interface.py` uses Slack WebClient `files_info` + `url_private_download` with Bearer token
- **Temporary File Management:** Files downloaded to temp paths with automatic cleanup after processing

## Data Flow Architecture

### Production Pipeline (Validated E2E)
1. **Slack File Upload:** User uploads receipt to Slack channel
2. **Socket Mode Event:** `file_shared` event received by `tools/slack_socket_runner.py`
3. **File Download:** `tools/slack_interface.py` downloads file using Slack WebClient with bot token
4. **Text Extraction:** `tools/text_extractor.py` performs OCR (Tesseract) or PDF parsing (pdfplumber)
5. **AI Processing:** `tools/receipt_processor.py` calls Granite 3.3 for structured JSON extraction
6. **Schema Validation:** JSON validated against `data/schemas/receipt_schema.json`
7. **Data Persistence:** `tools/sheets_manager.py` appends to Google Sheets using header-driven mapping
8. **User Confirmation:** Slack confirmation posted: "✅ Your receipt has been added to Google Sheets"

### Error Handling and Recovery
- **Retry Mechanisms:** Tenacity-based retries for external API calls (OCR, LLM, Sheets)
- **Duplicate Detection:** Vendor/amount/date comparison logic implemented
- **Schema Validation:** All LLM outputs validated against predefined schemas
- **Graceful Degradation:** Error messages posted to Slack for user awareness

## Observability and Monitoring
- **Structured Logging:** JSON logs with timestamp, component, action, correlation_id, event, status, duration_ms, error_type, error_message
- **Correlation IDs:** End-to-end request tracking across all components
- **Duration Metrics:** Performance tracking for OCR, LLM, and Sheets operations
- **Error Classification:** Categorized error types for monitoring and alerting
- **Audit Trail:** Google Sheets persistence with metadata and Slack confirmation timestamps

## Manual Review Architecture
- **Duplicate Detection:** Implemented with vendor/amount/date comparison
- **Confidence Thresholds:** OCR confidence and schema validation triggers
- **Review Workflow:** Planned interactive Approve/Reject buttons for Slack review path
- **Decision Logging:** Manual approvals logged with actor, action, correlation_id, and reason

## Security Architecture
- **Environment Variables:** All secrets managed via `.env` file; no credentials in code or logs
- **Token Authentication:** Slack file downloads use bot token Bearer authentication
- **Least Privilege:** Minimal Slack scopes and Google Sheets permissions
- **Temporary Files:** Secure file handling with automatic cleanup after processing
- **IAM Integration:** IBM Watsonx API access via IAM tokens with automatic refresh

## Configuration Management
- **Environment-driven:** All configuration via environment variables
- **Single Source of Truth:** `config/prompts.py` for all Granite prompts
- **Header-driven Mapping:** Google Sheets operations use `data/templates/sheets_template.json`
- **Schema Validation:** JSON validation against `data/schemas/receipt_schema.json`
- **Business Rules:** Configurable thresholds and settings via environment variables

## Testing Architecture
- **Unit Tests:** Component-level testing with mocked external services
- **Integration Tests:** Service integration testing with mocked APIs
- **End-to-End Tests:** Complete pipeline validation with real or test data
- **Test Isolation:** `_test_mode` flag for Slack interface to bypass real API calls
- **Environment Loading:** Proper environment variable loading for test sessions

## Deployment Patterns
- **Local Development:** IBM watsonx Orchestrate Developer Edition for local deployment
- **Socket Mode Primary:** WebSocket-based event handling (no public HTTP required)
- **HTTP Mode Optional:** ngrok-based deployment for alternative scenarios
- **Container-based:** Docker containers for Orchestrate services
- **Process-based:** Dedicated Python process for Socket Mode listener

## Error Recovery and Resilience
- **Exponential Backoff:** Retry mechanisms with increasing delays
- **Circuit Breaker:** Protection against cascading failures
- **Graceful Degradation:** Service continues operating with reduced functionality
- **User Feedback:** Clear error messages and status updates via Slack
- **Monitoring Integration:** Error tracking and alerting capabilities 