# API Reference

## Core Tools

### Text Extractor (`tools/text_extractor.py`)
Handles text extraction from images and PDFs. Default backend is the IBM watsonx chat vision model; legacy Tesseract/PDF parsing remains available for tests.

**Main Methods:**
- `extract(path: str) -> str` - Detects URL/file; for images and PDFs uses vision chat by default; legacy OCR paths available
- `extract_from_image(image_path: str) -> str` - Vision chat transcription when backend is `vision`; otherwise Tesseract
- `extract_from_pdf(pdf_path: str) -> str` - PDF rasterization to images then vision chat; legacy text extraction path retained

**Features:**
- Vision-first extraction via `meta-llama/llama-3-2-11b-vision-instruct`
- Data URI image embedding to chat API; supports public URLs when permitted
- Optional legacy OCR for tests: set `OCR_BACKEND=tesseract`
- Robust error handling with logging

### Receipt Processor (`tools/receipt_processor.py`)
Processes extracted text using IBM Granite 3.3 LLM and validates structured output.

**Main Methods:**
- `process(receipt_text: str) -> dict` - Sends prompt to Granite, returns validated JSON

**Notable Behavior:**
- Logs a redacted preview of the first 10 lines of the transcript used for structuring
- Uses prompts from `config/prompts.py`
- Robust JSON extraction (handles extra text around JSON, Markdown code fences, braces in strings)
- Schema validation against `data/schemas/receipt_schema.json`

### Query Analyzer (`tools/query_analyzer.py`)
Analyzes natural language queries using Granite LLM to extract search parameters.

**Main Methods:**
- `analyze(user_query: str, current_date: Optional[str] = None) -> dict` - Parses query into structured filters

### Sheets Manager (`tools/sheets_manager.py`)
Manages Google Sheets operations for expense data storage and retrieval.

**Main Methods:**
- `append_expense(expense: dict) -> None` - Appends expense with header-driven mapping
- `query_expenses(filters: dict) -> list[dict]` - Queries expenses with resilient header handling

**Features:**
- Header initialization from `data/templates/sheets_template.json`
- Canonical column name mapping
- Automatic handling of missing fields (filled with blanks)
- Timezone-aware date processing
- Duplicate detection based on vendor, amount, and date

### Controller (`tools/controller.py`)
Orchestrates end-to-end receipt processing and query flows.

**Main Methods:**
- `handle_file_shared(file_info: dict) -> None` - Complete receipt processing flow
- `handle_query(user_query: str) -> str` - Natural language query processing

**Features:**
- End-to-end orchestration with retry mechanisms
- Duplicate detection and handling
- Vendor breakdown and summary calculations
- Tabular result formatting for search queries
- Period normalization (e.g., "last_month" → concrete dates)

### Slack Interface (`tools/slack_interface.py`)
Handles Slack event registration and message routing.

**Main Methods:**
- `start() -> None` - Initializes Slack app and registers event handlers

**Features:**
- File upload event handling
- Message event processing
- Integration with Controller for workflow orchestration
- Safe text responses for Slack: in both production and test modes, handlers always send a valid `text` string. Status mapping for file uploads: `appended` → "✅ Your receipt has been added to Google Sheets", `duplicate` → "⚠️ Possible duplicate detected. Sent for review.", other/error → "❌ Could not process the receipt. Please try again or contact support."

## Integrations

### Google Sheets API (`integrations/google_sheets_api.py`)
Low-level client for Google Sheets operations.

**Main Methods:**
- `append_row(data: dict) -> None` - Appends row with header initialization
- `query(filters: dict) -> list[dict]` - Queries data with filter support
- `create_spreadsheet(title: str) -> str` - Creates new spreadsheet
- `open_worksheet(spreadsheet_id: str, worksheet_name: str) -> Worksheet` - Opens worksheet

**Features:**
- Automatic header initialization for empty sheets
- Canonical column name mapping
- Non-unique header handling
- Service account authentication

### Slack API (`integrations/slack_api.py`)
Low-level client for Slack operations.

**Main Methods:**
- `post_message(channel: str, text: str) -> None` - Posts message to channel
- `upload_file(channel: str, file_path: str, title: str) -> None` - Uploads file
- `file_download_url(file_info: dict) -> str` - Gets direct download URL

**Features:**
- Bot token authentication
- File upload and download support
- Message posting with formatting

### Granite Client (`models/granite_client.py`)
Client for IBM Watsonx Granite 3.3 model interactions.

**Main Methods:**
- `generate(prompt: str, max_new_tokens: int = 1000) -> str` - Generates text response

**Features:**
- IBM IAM token management and caching
- Watsonx API integration
- Project ID handling
- Error handling and retries
- JSON sanitation in `parse_json`: strips Markdown fences and control characters before parsing

## Data Schemas

### Receipt Schema (`data/schemas/receipt_schema.json`)
Defines the structure for extracted receipt data:
```json
{
  "vendor": "string",
  "date": "string (YYYY-MM-DD)",
  "amount": "number",
  "category": "string",
  "description": "string",
  "receipt_number": "string (optional)",
  "tax_amount": "number (optional)",
  "payment_method": "string (optional)",
  "location": "string (optional)"
}
```

### Sheets Template (`data/templates/sheets_template.json`)
Defines Google Sheets column structure:
- Date, Vendor, Amount, Category, Description, Receipt_Link
- Payment_Method, Receipt_Number, Tax_Amount, Location
- Processed_Date, Confidence_Score

## Configuration

### Settings (`config/settings.py`)
Centralized configuration management with environment variable loading:
- IBM Watsonx credentials and project settings
- Google Sheets configuration
- Slack app settings
- OCR and processing parameters
- Business rules and thresholds

### Prompts (`config/prompts.py`)
Centralized prompt management for LLM interactions:
- Receipt extraction prompts
- Query analysis prompts
- Error handling and validation guidance

## End-to-End Flow

### Receipt Processing Flow
1. **Trigger:** Slack file upload or direct file path/URL
2. **Text Extraction:** OCR (images) or PDF parsing (PDFs)
3. **LLM Processing:** Granite 3.3 extracts structured data
4. **Validation:** JSON schema validation with confidence scoring
5. **Duplicate Check:** Vendor/amount/date comparison
6. **Storage:** Append to Google Sheets with correlation ID
7. **Confirmation:** Slack message: "✅ Your receipt has been added to Google Sheets"

### Query Processing Flow
1. **Trigger:** Natural language query in Slack
2. **Query Analysis:** Granite 3.3 parses query into structured filters
3. **Data Retrieval:** Query Google Sheets with filters
4. **Processing:** Apply time ranges, calculate summaries, generate vendor breakdowns
5. **Formatting:** Render results as text table or summary
6. **Response:** Post formatted response to Slack

### Error Handling
- **OCR Failures:** Retry with image preprocessing
- **LLM Errors:** JSON extraction fallback, validation error logging
- **API Failures:** Exponential backoff with tenacity
- **Duplicate Detection:** Manual review path for ambiguous cases

## Testing

### Test Categories
- **Unit Tests:** Individual tool functionality with mocks
- **Integration Tests:** Tool interactions with mocked external services
- **E2E Tests:** Complete flows with real integrations (marked with `@pytest.mark.e2e`)

### Test Coverage
- All tools have comprehensive unit tests
- Integration tests cover external service interactions
- E2E tests validate complete production flows
- Error scenarios and edge cases covered

## Deployment Notes
- Local development mirrors deployment behavior
- ADK primarily handles wiring and event routing
- All business logic remains identical between local and deployed environments
- Environment variables control all configuration
- No secrets in code or documentation 