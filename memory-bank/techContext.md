# Tech Context

## Development Environment
- **Language:** Python 3.11+
- **Platform:** Windows PowerShell (C:\Users\HP\Isabella)
- **Package Management:** pip with requirements.txt
- **Virtual Environment:** .venv with PowerShell activation

## Core Technologies
- **AI/LLM:** IBM Granite 3.3 (ibm/granite-3-3-8b-instruct) via Watsonx API
- **OCR:** Tesseract (pytesseract) with image preprocessing (PIL/Pillow)
- **PDF Processing:** pdfplumber for text extraction
- **Testing:** pytest with coverage and custom markers

## External Integrations
- **Google Sheets:** gspread with service account authentication
- **Slack:** slack-bolt and slack-sdk for bot interactions
- **IBM Watsonx:** Direct API calls with IAM token management
- **File Handling:** Local, HTTP/HTTPS, and Slack file URLs

## Development Tools
- **Version Control:** Git with conventional commit messages
- **Documentation:** Markdown with Memory Bank structure
- **Configuration:** Environment variables via config/settings.py
- **Logging:** Structured JSON logging with correlation IDs

## Testing Strategy
- **Unit Tests:** Individual tool functionality with mocks
- **Integration Tests:** Tool interactions with mocked external services
- **E2E Tests:** Complete flows with real integrations (marked with @pytest.mark.e2e)
- **Test Framework:** pytest with custom configuration (pytest.ini)

## Deployment Technology
- **Platform:** IBM Watsonx Orchestrate ADK (planned for M5)
- **Orchestration:** ADK skill packaging and connection management
- **Monitoring:** Structured logging with correlation IDs and metrics
- **Security:** Environment variables for all secrets and credentials

## Data Management
- **Storage:** Google Sheets as primary data store
- **Schemas:** JSON schema validation for all LLM outputs
- **Templates:** Header-driven mapping for Google Sheets
- **Audit Trail:** Processing metadata and correlation IDs

## Performance & Reliability
- **Retry Logic:** Tenacity for exponential backoff on API failures
- **Error Handling:** Graceful degradation and structured error logging
- **Validation:** Schema validation and confidence scoring
- **Duplicate Detection:** Vendor/amount/date comparison logic

## Security & Compliance
- **Secret Management:** Environment variables only, no secrets in code
- **Access Control:** Least privilege permissions for external services
- **Data Protection:** No sensitive data in logs, correlation IDs for tracking
- **Audit Logging:** All actions tracked with metadata and decisions 