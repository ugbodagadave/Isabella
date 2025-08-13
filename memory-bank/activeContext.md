# Active Context

Current Focus:
- M3 finalized: controller orchestration with retries; Sheets mapping includes processed date and confidence

Next Steps:
- Prepare for M4 query flow; keep external calls mocked in tests

Decisions:
- Keep `GraniteClient.generate` mocked for local tests
- Append extended fields to Sheets per template; compute processed date in configured timezone 