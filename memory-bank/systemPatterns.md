# System Patterns

## Core Architecture
- **LLM-first Design:** IBM Granite 3.3 handles receipt understanding and query analysis
- **Minimal Tools:** Four core tools with focused responsibilities
- **Orchestration:** Controller manages end-to-end flows with retry mechanisms
- **Environment-driven Configuration:** All settings via `config/settings.py`

## Data Flow Patterns
- **Receipt Processing:** File → OCR/PDF → Granite → Schema Validation → Sheets → Slack Confirmation
- **Query Processing:** Natural Language → Granite Analysis → Sheets Query → Filtering → Summary → Slack Response
- **Error Handling:** Retry with exponential backoff, graceful degradation, structured logging

## Integration Patterns
- **Header-driven Mapping:** Google Sheets uses canonical column names from templates
- **Correlation IDs:** End-to-end request tracking across all components
- **Schema Validation:** All LLM outputs validated against JSON schemas
- **Mock-first Testing:** Unit tests use mocks, E2E tests use real integrations

## Configuration Patterns
- **Single Source of Truth:** Prompts centralized in `config/prompts.py`
- **Environment Variables:** All secrets and settings via environment
- **Business Rules:** Configurable thresholds and limits via settings
- **Template-driven:** Data structures defined in `data/templates/`

## Testing Patterns
- **Test Categories:** Unit (mocked), Integration (partial mocks), E2E (real services)
- **E2E Markers:** `@pytest.mark.e2e` for live integration tests
- **Correlation Tracking:** Tests verify end-to-end request flow
- **Validation Points:** Schema validation, confidence scoring, duplicate detection

## Deployment Patterns
- **Local Parity:** Development environment mirrors production behavior
- **ADK Wiring:** IBM Watsonx Orchestrate handles event routing and connections
- **Observability:** Structured logging with correlation IDs and metrics
- **Audit Trail:** All transactions logged with metadata and decisions

## Error Handling Patterns
- **Tenacity Retries:** Exponential backoff for external API calls
- **Graceful Degradation:** Continue processing with partial data when possible
- **Structured Logging:** JSON logs with error types, correlation IDs, and context
- **Manual Review:** Low-confidence or duplicate receipts routed for human review

## Security Patterns
- **No Secrets in Code:** All credentials via environment variables
- **Least Privilege:** Minimal required permissions for external services
- **Audit Logging:** All actions tracked with correlation IDs
- **Data Validation:** Input validation and schema enforcement throughout 