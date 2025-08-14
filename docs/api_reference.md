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
    - Sends prompt to Granite, expects pure JSON text (with fallback JSON recovery)
    - Validates against `data/schemas/receipt_schema.json`
- `tools/query_analyzer.py`
  - `QueryAnalyzer.analyze(user_query: str, current_date: Optional[str] = None) -> dict`
- `tools/sheets_manager.py`
  - `SheetsManager.append_expense(expense: dict) -> None` (header-driven mapping)
  - `SheetsManager.query_expenses(filters: dict) -> list[dict]` (resilient headers)
- `tools/slack_interface.py`
  - `SlackInterface.start() -> None`
- `tools/controller.py`
  - Orchestrates file flow and query flow

## Integrations
- `integrations/google_sheets_api.py`
  - Header initialization from `data/templates/sheets_template.json`
  - Canonical name mapping; blanks filled when fields are missing
- `integrations/slack_api.py`
  - Post messages; optional file helpers for E2E

## Models
- `models/granite_client.py`
  - Real IBM Watsonx invocation for Granite (used in E2E)

## End-to-End Flow
- File URL or path → OCR (Tesseract) → Granite JSON → Schema validation → Google Sheets append → Slack confirmation message.
- This mirrors deployment behavior; only the ADK wiring differs (added at M5). 