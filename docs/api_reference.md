# API Reference

## Tools
- `tools/text_extractor.py`
  - `TextExtractor.extract(path: str) -> str`
    - Detects by extension; routes images to OCR and PDFs to text extraction
    - Applies lightweight image preprocessing (grayscale + sharpen) before OCR
  - `TextExtractor.extract_from_image(image_path: str) -> str`
  - `TextExtractor.extract_from_pdf(pdf_path: str) -> str`
- `tools/receipt_processor.py`
  - `ReceiptProcessor.process(receipt_text: str) -> dict`
    - Sends prompt to Granite, expects pure JSON text
    - Parses JSON and validates against `data/schemas/receipt_schema.json`
    - Raises `ValueError` if model returns invalid JSON; raises schema `ValidationError` for invalid structure
- `tools/query_analyzer.py`
  - `QueryAnalyzer.analyze(user_query: str, current_date: Optional[str] = None) -> dict`
    - Uses `QUERY_ANALYSIS_PROMPT` to produce structured query intent JSON
- `tools/sheets_manager.py`
  - `SheetsManager.append_expense(expense: dict) -> None`
    - Appends a row to Google Sheets via `GoogleSheetsClient`
  - `SheetsManager.query_expenses(filters: dict) -> list[dict]`
    - Returns rows; filtering behavior delegated to client
- `tools/slack_interface.py`
  - Registers handlers for `message` and `file_shared` events that delegate to controller methods
  - `SlackInterface.start() -> None`
- `tools/controller.py`
  - `Controller.handle_file_shared(body: dict) -> dict`
    - Orchestrates OCR → LLM → schema validation → Sheets append with duplicate detection
  - `Controller.handle_query(text: str) -> str`
    - Uses `QueryAnalyzer` to derive filters; supports time range filtering; returns vendor breakdown in summaries; renders a simple table for search requests

## Integrations
- `integrations/google_sheets_api.py`
  - `GoogleSheetsClient.append_row(expense: dict) -> None`
    - Maps to columns including Processed_Date and Confidence_Score
  - `GoogleSheetsClient.query(filters: dict) -> list[dict]`
  - `GoogleSheetsClient.create_spreadsheet(title: str) -> Any`
  - `GoogleSheetsClient.open_worksheet(worksheet_name: str) -> Any`
- `integrations/slack_api.py`
  - `SlackApi.post_message(channel: str, text: str)`
  - `SlackApi.upload_file(channel: str, file_path: str, title: str | None = None)`

## Models
- `models/granite_client.py`
  - `GraniteClient.build_request(prompt: str, temperature: float = 0.1, max_tokens: int = 512) -> dict`
  - `GraniteClient.generate(prompt: str, temperature: float = 0.1, max_tokens: int = 512) -> str` (NotImplemented for local tests; must be mocked)
  - `GraniteClient.parse_json(text: str) -> Any`

## Test Coverage Notes
- Unit tests mock external services: OCR, Granite, Slack, Google Sheets
- Integration-like tests validate:
  - Google Sheets row mapping and query passthrough
  - Slack API message posting and file upload
  - End-to-end mocked flow: OCR -> Granite -> Schema validation -> Sheets append
  - Query flow: analyzer intent parsing; controller summary totals, vendor breakdown, table rendering 