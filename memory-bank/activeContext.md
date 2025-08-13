# Active Context

Current Focus:
- M3 In Progress: controller orchestration for Slack upload → OCR → LLM → Sheets with duplicate detection

Next Steps:
- Maintain mocks for external services; no live network calls in tests
- Finalize controller tests; prepare for M4 query flow

Decisions:
- Keep `GraniteClient.generate` unimplemented locally; rely on mocks
- Persist `receipt_link` when provided; log duplicates instead of appending 