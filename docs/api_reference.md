# API Reference

## Core Tools

### Text Extractor (`tools/text_extractor.py`)
Handles text extraction from images and PDFs. Default backend is the IBM watsonx chat vision model; legacy Tesseract/PDF parsing remains available for tests.

**Main Methods:**
- `extract(path: str) -> str` - Detects URL/file; for images and PDFs uses vision chat by default; legacy OCR paths available
- `extract_from_image(image_path: str) -> str` - Vision chat transcription when backend is `vision`; otherwise Tesseract
- `extract_from_pdf(pdf_path: str) -> str` - PDF text via `pdfplumber` (no vision)

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
- Logs a redacted preview of the first 10 lines of the transcript used for structuring; strips markdown headings and sensitive tokens
- Uses prompts from `config/prompts.py`; performs one strict JSON-only retry on invalid JSON
- Robust JSON extraction (handles extra text around JSON, Markdown code fences, braces in strings)
- Schema validation against `data/schemas/receipt_schema.json`; heuristic fallback in controller if JSON still fails

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

## Query Analyzer

Isabella translates natural-language questions about your Expenses Google Sheet into a structured JSON "query plan". This plan is executed to filter, aggregate, and present results.

Schema (all fields required; use null where unknown):

```json
{
  "intent": "summary|search|aggregate|trend|top_n|compare",
  "time_range": {
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "relative": "last_month|this_month|this_year|last_quarter|last_7_days|last_90_days|custom|null"
  },
  "filters": {
    "vendors": ["..."] or null,
    "categories": ["..."] or null,
    "min_amount": 0 or null,
    "max_amount": 0 or null,
    "text_search": "string or null"
  },
  "group_by": "none|vendor|category|date",
  "trend": {
    "enabled": true,
    "granularity": "day|week|month|quarter|year"
  },
  "top_n": {
    "enabled": true,
    "dimension": "vendor|category",
    "limit": 5
  },
  "compare": {
    "enabled": true,
    "baseline": { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" } or null,
    "target": { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" } or null
  },
  "sort": {
    "by": "amount|date|vendor|category|count|total",
    "direction": "asc|desc"
  },
  "output": {
    "format": "summary|table|detailed|chart",
    "chart": {
      "type": "bar|line|pie|area|null",
      "dimension": "vendor|category|date|null",
      "metric": "amount|count|total|null"
    }
  }
}
```

Example queries → plans:
- Top 5 vendors last 90 days
```json
{"intent":"top_n","time_range":{"start_date":null,"end_date":null,"relative":"last_90_days"},"filters":{"vendors":null,"categories":null,"min_amount":null,"max_amount":null,"text_search":null},"group_by":"vendor","trend":{"enabled":false,"granularity":"month"},"top_n":{"enabled":true,"dimension":"vendor","limit":5},"compare":{"enabled":false,"baseline":null,"target":null},"sort":{"by":"total","direction":"desc"},"output":{"format":"summary","chart":{"type":null,"dimension":null,"metric":null}}}
```
- Show total spend last month by category as a chart
```json
{"intent":"aggregate","time_range":{"start_date":null,"end_date":null,"relative":"last_month"},"filters":{"vendors":null,"categories":null,"min_amount":null,"max_amount":null,"text_search":null},"group_by":"category","trend":{"enabled":true,"granularity":"month"},"top_n":{"enabled":false,"dimension":"category","limit":5},"compare":{"enabled":false,"baseline":null,"target":null},"sort":{"by":"total","direction":"desc"},"output":{"format":"chart","chart":{"type":"bar","dimension":"category","metric":"total"}}}
```
- List groceries at Trader Joe’s over $20 this year
```json
{"intent":"search","time_range":{"start_date":null,"end_date":null,"relative":"this_year"},"filters":{"vendors":["Trader Joe's"],"categories":["Groceries"],"min_amount":20,"max_amount":null,"text_search":null},"group_by":"none","trend":{"enabled":false,"granularity":"month"},"top_n":{"enabled":false,"dimension":"vendor","limit":5},"compare":{"enabled":false,"baseline":null,"target":null},"sort":{"by":"date","direction":"desc"},"output":{"format":"table","chart":{"type":null,"dimension":null,"metric":null}}}
```
- Compare this month vs last month for office supplies
```json
{"intent":"compare","time_range":{"start_date":null,"end_date":null,"relative":"this_month"},"filters":{"vendors":null,"categories":["Office Supplies"],"min_amount":null,"max_amount":null,"text_search":null},"group_by":"none","trend":{"enabled":false,"granularity":"month"},"top_n":{"enabled":false,"dimension":"vendor","limit":5},"compare":{"enabled":true,"baseline":{"start_date":"2024-01-01","end_date":"2024-01-31"},"target":{"start_date":"2024-02-01","end_date":"2024-02-29"}},"sort":{"by":"total","direction":"desc"},"output":{"format":"summary","chart":{"type":null,"dimension":null,"metric":null}}}
```

Execution
- The controller applies filters (dates, vendors, categories, amount, text_search), groups/aggregates if requested, computes trends or top-N, sorts, and returns one of:
  - summary: totals with top vendors/categories
  - table: simple text table
  - detailed: count-only detail
  - chart: textual indication of prepared series (no image rendering) 