# System Patterns

## Core Architecture
- LLM-first: Granite 3.3 for receipt understanding
- Orchestration: Controller manages OCR → LLM → validation → Sheets → Slack
- Runtime: Local Orchestrate Developer Edition for agent UI; Slack events handled by socket runner

## Event Handling
- Slack Socket Mode with `SocketModeHandler`; `file_shared` triggers download → temp file → controller `handle_file_shared`
- Message events route to controller `handle_query`

## Data Flow
- File → OCR/PDF → Granite → JSON schema validation → Sheets append → Slack confirmation

## Observability
- Log success/fail at each step; expand to structured JSON with correlation_id and duration metrics

## Manual Review
- Duplicate detection implemented; interactive Approve/Reject buttons planned for Slack review path

## Security
- No secrets in code or logs; env-only configuration; Slack file downloads authenticated via bot token 