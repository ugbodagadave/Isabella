# Active Context

Current Focus:
- M5 Deployment: IBM Watsonx Orchestrate ADK deployment with observability, audit trails, and manual review paths

Next Steps:
- Package tools as ADK skills with proper input/output mapping
- Configure ADK connections for IBM Watsonx, Google Sheets, and Slack
- Implement structured logging with correlation IDs across all components
- Add manual review path for low-confidence or duplicate receipts
- Deploy and validate production environment

Recent Achievements:
- ✅ M4 Completed: Query flow with natural language processing, vendor breakdowns, time range filtering, and tabular results
- ✅ Live E2E Test Verified: Complete end-to-end flow with real integrations (Granite, Google Sheets, Slack)
- ✅ Header-driven Sheets mapping implemented with proper column alignment
- ✅ All tests passing (unit, integration, E2E)

Key Decisions:
- Vendor breakdown limited by `TOP_VENDORS_LIMIT` (env, default 5)
- Period keywords supported: `last_month`, `this_month`, `this_year`
- Manual review triggered by confidence threshold or duplicate detection
- Structured JSON logging with correlation IDs for observability
- Audit trail maintained in Google Sheets with processing metadata

Technical Patterns:
- LLM-first design with Granite 3.3 for receipt understanding
- Header-driven Google Sheets mapping for resilience
- Retry mechanisms with tenacity for external API calls
- Schema validation for all LLM outputs
- Environment-driven configuration via `config/settings.py`

Deployment Architecture:
- Local development mirrors production behavior
- ADK primarily handles wiring and event routing
- All business logic remains identical between environments
- Observability and audit trails added in M5
- Manual review path for production safety 