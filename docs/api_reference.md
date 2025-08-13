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
- `tools/sheets_manager.py`
  - `SheetsManager.append_expense(expense: dict) -> None`
    - Appends a row to Google Sheets via `GoogleSheetsClient`
  - `SheetsManager.query_expenses(filters: dict) -> list[dict]`
    - Returns rows; filtering behavior delegated to client
- `tools/slack_interface.py`
  - Registers handlers for `message` and `file_shared` events that delegate to controller methods
  - `SlackInterface.start() -> None`

## Integrations
- `integrations/google_sheets_api.py`
  - `GoogleSheetsClient.append_row(expense: dict) -> None`
  - `GoogleSheetsClient.query(filters: dict) -> list[dict]`
- `integrations/slack_api.py`
  - `SlackApi.post_message(channel: str, text: str)`

## Models
- `models/granite_client.py`
  - `GraniteClient.generate(prompt: str) -> str` (NotImplemented for local tests; must be mocked)
  - `GraniteClient.parse_json(text: str) -> Any` 