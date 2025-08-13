# API Reference

## Tools
- `tools/text_extractor.py`
  - `TextExtractor.extract(path: str) -> str`
- `tools/receipt_processor.py`
  - `ReceiptProcessor.process(receipt_text: str) -> dict`
- `tools/sheets_manager.py`
  - `SheetsManager.append_expense(expense: dict) -> None`
  - `SheetsManager.query_expenses(filters: dict) -> list[dict]`
- `tools/slack_interface.py`
  - `SlackInterface.start() -> None`

## Integrations
- `integrations/google_sheets_api.py`
  - `GoogleSheetsClient.append_row(expense: dict) -> None`
  - `GoogleSheetsClient.query(filters: dict) -> list[dict]`
- `integrations/slack_api.py`
  - `SlackApi.post_message(channel: str, text: str)`

## Models
- `models/granite_client.py`
  - `GraniteClient.generate(prompt: str) -> str`
  - `GraniteClient.parse_json(text: str) -> Any` 