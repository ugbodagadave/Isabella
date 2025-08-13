# Active Context

Current Focus:
- M1 tooling solidity: extraction, processing, sheets, and slack orchestration with mocks
- Added schema validation in `ReceiptProcessor` and preprocessing/error handling in `TextExtractor`

Next Steps:
- Maintain mocks for Granite/Slack/Sheets in unit tests; keep ADK out until deployment
- Review NEED-CONFIRM env semantics in `isabella-plan.md` as needed

Decisions:
- Validate receipts against `data/schemas/receipt_schema.json` and raise on invalid
- Keep Slack token verification disabled in tests; simulate handlers with a fake app 