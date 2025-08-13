### Isabella AI Bookkeeping Agent — Build Plan

Status: draft v1
Owner: you
Scope: end-to-end scaffolding, config, tooling, test/doc workflow, and deployment outline

---

## Guiding Principles
- **LLM-first**: IBM Granite 3.3 handles receipt understanding and structuring.
- **Minimal tools**: Exactly four tools: `text_extractor`, `receipt_processor`, `sheets_manager`, `slack_interface`.
- **Operational excellence**: Testing → Documentation → Commit → Push for every meaningful change.
- **Security**: Secrets only via environment variables; never committed.

Reference: IBM watsonx Orchestrate docs [`Getting started`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate).

---

## Completed (M0–M2)
- Repository scaffolded with all directories, configs, schemas, docs, and tests
- `.gitignore`, `agent.yaml`, `config/` seeded; Memory Bank established
- Tooling stubs implemented with robust unit tests and mocks (no live calls)
- `TextExtractor` with image/PDF paths, preprocessing hooks, and error handling
- `ReceiptProcessor` with Granite prompt, JSON parsing, and schema validation (`data/schemas/receipt_schema.json`)
- `SheetsManager` basic append/query with logging; Google client wrapper ready
- `SlackInterface` handlers for `message` and `file_shared` with tests using a fake app
- Integration-like tests: Google Sheets mapping, Slack API post and file upload, end-to-end mocked flow
- Granite client interface expanded with `build_request(...)` (generate mocked in tests)
- Docs updated (`docs/api_reference.md`, `docs/setup.md`); Memory Bank updated
- All tests green locally via `pytest`

## Pending (M3–M5)
- M3 — End-to-End Receipt Flow (In Progress)
  - Add controller to orchestrate Slack upload → OCR → LLM extraction → Sheets append
  - Persist file link in Sheets, duplicate detection, confidence handling
  - Error handling + retries (tenacity)
- M4 — Query Flow
  - Natural language queries → Sheets data retrieval
  - Response formatting (table/summary)
- M5 — Deployment and Hardening
  - Package/deploy via Watsonx Orchestrate ADK
  - Observability, audit trail, manual review path

---

## Milestones and Deliverables

### M0 — Repository and Scaffolding (Completed)
Deliverables:
- Project folders and starter files created
- `.env.sample` with placeholders (no secrets)
- `.gitignore` configured
- `agent.yaml` baseline
- `config/` package seeded (`settings.py`, `prompts.py`, `connections.yaml`)
- Docs seeded in `docs/`
- Initial commit and push to GitHub

### M1 — Core Tooling (Completed)
- Implement minimal versions of:
  - `tools/text_extractor.py`
  - `tools/receipt_processor.py`
  - `tools/sheets_manager.py`
  - `tools/slack_interface.py`
- Add unit tests in `tests/test_tools/` covering happy-path basics.
- Ensure tests run locally (pytest) and document commands.

### M2 — Integrations (Completed)
- `models/granite_client.py` interface additions
- `integrations/google_sheets_api.py` (create/read/append helpers)
- `integrations/slack_api.py` (file upload)
- Integration tests with mocks in `tests/test_integrations/`

### M3 — End-to-End Receipt Flow (In Progress)
- Slack upload → OCR → LLM extraction → Sheets append
- Persist file link in Sheets
- Add duplicate-detection logic and confidence scoring
- Error handling + retries (tenacity)

### M4 — Query Flow
- Natural language queries via Slack
- LLM-based query understanding → Sheets data retrieval
- Response formatting (table/summary)

### M5 — Deployment and Hardening
- Package and deploy with Watsonx Orchestrate ADK
- Observability (structured logs), audit trail, and manual review path

---

## Environment Variables — Confirmation Points
Your `.env` is already set and correct per your screenshot. Below are the variables the code will read. Items marked NEED-CONFIRM are places where we would normally confirm semantics or values. Do not share values; just confirm correctness if asked.

IBM Watsonx / Granite
- `WATSONX_API_KEY`
- `WATSONX_PROJECT_ID`
- `WATSONX_URL`
- `GRANITE_MODEL_ID` (e.g., `ibm/granite-3.3-8b-instruct`) — NEED-CONFIRM if you plan to use a different size/variant

Google Sheets
- `GOOGLE_SHEETS_CREDENTIALS_PATH` — you will place the credentials JSON in `./config/`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_WORKSHEET_NAME`

Slack
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SLACK_CHANNEL_ID` — NEED-CONFIRM destination for default notifications

Storage / Database
- `FILE_STORAGE_TYPE` (e.g., `postgres`) — NEED-CONFIRM if using object storage instead
- `DATABASE_URL` — NEED-CONFIRM format and connectivity if used beyond file links

OCR / Extraction
- `TESSERACT_CMD` (Windows path to `tesseract.exe`)
- `TESSERACT_LANG` (e.g., `eng`)
- `OCR_CONFIDENCE_THRESHOLD` (e.g., `70`) — NEED-CONFIRM threshold policy
- `IMAGE_PREPROCESSING` (`true`/`false`)

Business Rules
- `DEFAULT_CURRENCY` (e.g., `USD`)
- `TIMEZONE` (e.g., `America/New_York`)
- `AUTO_CATEGORIZATION_ENABLED` (`true`/`false`)
- `DUPLICATE_DETECTION_ENABLED` (`true`/`false`)
- `REQUIRE_APPROVAL` (`true`/`false`) — NEED-CONFIRM for business workflow

Note: Per workspace rules, I will never read or modify your environment; I’ll only reference keys and expect them to exist.

---

## Step-by-Step Plan

### 1) Local Tooling
- Create Python virtual environment
- Install dev tools and libraries from `requirements.txt`
- Verify `tesseract` binary path is valid on Windows

Commands (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) IBM Watsonx Orchestrate ADK (Deferred to Deployment Phase)
- We will NOT install or use the ADK during development. Keep local focus on tools, tests, and docs.
- ADK initialization and connections will happen only in the Deployment phase.

Reference for later: IBM docs — [`Getting started with IBM watsonx Orchestrate`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate).

### 3) Implement Four Tools (Incrementally)
- `text_extractor.py`:
  - PDFs via `pdfplumber`/`PyPDF2`
  - Images via `pytesseract` with optional preprocessing
- `receipt_processor.py`:
  - Prompt from `config/prompts.py`
  - Call `models/granite_client.py`
  - Validate JSON vs `data/schemas/receipt_schema.json`
- `sheets_manager.py`:
  - Append/search rows in Google Sheets
  - Maintain `Receipt_Link`
- `slack_interface.py`:
  - Handle uploads and queries, orchestrate flow, format replies

### 4) Tests First
- Unit tests for each tool (use `tests/test_tools/*`)
- Integration tests for Sheets and Slack (mock credentials and APIs)
- Add `pytest.ini` if needed for config

Run:
```
pytest -q
```

### 5) Documentation
- Keep `docs/setup.md`, `docs/api_reference.md`, `docs/deployment.md` updated
- Add examples and troubleshooting

### 6) Commit & Push Policy
- Always run tests locally before commit
- Update docs for any new capability
- Commit style:
  - `feat:`, `fix:`, `docs:`, `test:`, `chore:`

Commands:
```
git add . ; git commit -m "feat: scaffold project and planning docs" ; git push origin main
```

### 7) Deployment
- Prepare `agent.yaml` with tool definitions and Slack channel config
- Package and deploy via ADK
- Validate in Orchestrate chat and Slack channel

---

## Acceptance Criteria per Milestone
- M1: All tool stubs implemented; tests for stubs green
- M2: Clients talk to APIs (mocks/real) with tests green
- M3: End-to-end upload → sheet append demo works on a sample
- M4: Query flow answers at least two query types (summary/search)
- M5: Deployed agent usable in Slack with basic observability

---

## Risks and Mitigations
- OCR quality variance → preprocessing and threshold tuning
- Date/currency ambiguity → prompt constraints + post-parse validators
- Slack event complexity → use `slack_bolt` and verify signing secret handling
- Google API quotas → batch writes and caching where appropriate

---

## Next Actions (after this commit)
- Continue M3 controller tests and refine orchestration as needed 