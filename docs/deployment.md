# Deployment Guide

## Overview
This guide covers deploying Isabella to production using IBM Watsonx Orchestrate ADK. The deployment process transforms the local development environment into a production-ready AI agent with observability, audit trails, and manual review capabilities.

## Prerequisites

### Environment Setup
- All environment variables configured (see `docs/setup.md`)
- Google service account credentials at `./config/google-credentials.json`
- IBM Watsonx project with Granite 3.3 access
- Slack app with required scopes and event subscriptions

### Required Slack App Scopes
- `chat:write` - Post messages to channels
- `files:read` - Access uploaded files
- `channels:history` - Read channel messages
- `app_mentions:read` - Respond to app mentions

### Google Sheets Setup
Ensure your target Google Sheet has the header row from `data/templates/sheets_template.json`:
```
Date | Vendor | Amount | Category | Description | Receipt_Link | Payment_Method | Receipt_Number | Tax_Amount | Location | Processed_Date | Confidence_Score
```

## Deployment Architecture

### Component Mapping
The deployment maps local tools to ADK skills:

**Core Tools → ADK Skills:**
- `tools/text_extractor.py` → "Extract text from receipt"
- `tools/receipt_processor.py` → "Parse receipt to structured JSON"
- `tools/sheets_manager.py` → "Append expense to Google Sheets" + "Query expenses"
- `tools/controller.py` → "Handle file uploads" + "Handle user queries"
- `tools/query_analyzer.py` → "Analyze natural language queries"

**Integrations → ADK Connections:**
- `models/granite_client.py` → IBM Watsonx connection
- `integrations/google_sheets_api.py` → Google Sheets connection
- `integrations/slack_api.py` → Slack connection

### Runtime Flow (Production)
1. **Trigger:** Slack file upload or user message
2. **Text Extraction:** OCR/PDF parsing with preprocessing
3. **LLM Processing:** Granite 3.3 structured data extraction
4. **Validation:** JSON schema validation with confidence scoring
5. **Duplicate Detection:** Vendor/amount/date comparison
6. **Storage:** Google Sheets append with correlation ID
7. **Confirmation:** Slack message: "✅ Your receipt has been added to Google Sheets"

## Deployment Steps

### 1. Install IBM Watsonx Orchestrate ADK
```bash
pip install watsonx-orchestrate-adk
```

### 2. Initialize ADK Project
```bash
# Initialize ADK project
orchestrate dev init

# Create connections for external services
orchestrate connections create
```

### 3. Configure Connections
Set up the following connections in ADK:

**IBM Watsonx Connection:**
- Type: IBM Watsonx
- API Key: `WATSONX_API_KEY`
- Project ID: `WATSONX_PROJECT_ID`
- URL: `WATSONX_URL`
- Model ID: `GRANITE_MODEL_ID`

**Google Sheets Connection:**
- Type: Google Sheets
- Credentials: Service account JSON from `./config/google-credentials.json`
- Spreadsheet ID: `GOOGLE_SHEETS_SPREADSHEET_ID`
- Worksheet Name: `GOOGLE_SHEETS_WORKSHEET_NAME`

**Slack Connection:**
- Type: Slack
- Bot Token: `SLACK_BOT_TOKEN`
- App Token: `SLACK_APP_TOKEN`
- Signing Secret: `SLACK_SIGNING_SECRET`
- Channel ID: `SLACK_CHANNEL_ID`

### 4. Package Tools as Skills
Create ADK skills for each tool function:

**Text Extraction Skill:**
```yaml
name: extract_text_from_receipt
description: Extract text from receipt images and PDFs using OCR
inputs:
  file_path: string
outputs:
  extracted_text: string
```

**Receipt Processing Skill:**
```yaml
name: parse_receipt_to_json
description: Parse receipt text to structured JSON using Granite 3.3
inputs:
  receipt_text: string
outputs:
  structured_data: object
  confidence_score: number
```

**Sheets Management Skills:**
```yaml
name: append_expense_to_sheets
description: Append expense data to Google Sheets
inputs:
  expense_data: object
outputs:
  success: boolean
  correlation_id: string
```

### 5. Configure Agent
Update `agent.yaml` with skill definitions and event handlers:

```yaml
name: isabella
description: AI Bookkeeping Agent
version: 1.0.0

skills:
  - extract_text_from_receipt
  - parse_receipt_to_json
  - append_expense_to_sheets
  - query_expenses
  - handle_file_upload
  - handle_user_query

events:
  slack:
    file_shared: handle_file_upload
    message: handle_user_query

connections:
  - watsonx
  - google_sheets
  - slack
```

### 6. Deploy Agent
```bash
# Build and deploy
orchestrate deploy

# Verify deployment
orchestrate status
```

## Observability and Monitoring

### Structured Logging
All components emit structured JSON logs with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "component": "receipt_processor",
  "action": "process_receipt",
  "correlation_id": "uuid-1234-5678",
  "event": "llm_processing_start",
  "status": "success",
  "duration_ms": 1250,
  "confidence_score": 0.85
}
```

### Metrics to Monitor
- **Processing Times:** OCR duration, LLM response time, Sheets append time
- **Success Rates:** E2E success rate, schema validation pass rate
- **Error Rates:** OCR failures, LLM errors, API failures
- **Business Metrics:** Receipts processed, duplicates detected, manual reviews

### Log Aggregation
- Use your preferred log aggregation service (ELK, Splunk, etc.)
- Ensure correlation IDs are preserved across all log entries
- Set up alerts for error rate thresholds

## Audit Trail

### Data Persistence
All transactions are recorded in Google Sheets with:
- **Receipt Data:** Vendor, date, amount, category, description
- **Processing Metadata:** Processed date, confidence score, correlation ID
- **Receipt Link:** Original file reference for audit purposes

### Manual Review Tracking
When manual review is triggered:
- Log review request with correlation ID
- Track approval/rejection decisions
- Record reviewer identity and reasoning
- Maintain audit trail in separate review log

### Compliance Considerations
- All data processing is logged with correlation IDs
- Original receipts are preserved via links
- Processing decisions are auditable
- Manual review decisions are tracked

## Manual Review Path

### Trigger Conditions
Manual review is triggered when:
- `confidence_score < OCR_CONFIDENCE_THRESHOLD`
- Schema validation fails
- Duplicate detected with ambiguity
- `REQUIRE_APPROVAL = true` (business rule)

### Review Process
1. **Notification:** Post to reviewers Slack channel with:
   - Receipt summary (vendor/date/amount)
   - Confidence score and duplicate status
   - Receipt link and correlation ID
   - Approve/Reject buttons

2. **Decision Handling:**
   - **Approve:** Proceed with Google Sheets append
   - **Reject:** Log rejection reason, do not append
   - **Timeout:** Escalate after configured timeout period

3. **Audit Logging:**
   - Record all review decisions with timestamps
   - Track reviewer identity and reasoning
   - Maintain correlation ID throughout process

## Production Validation

### Smoke Tests
After deployment, run these validation tests:

1. **Receipt Processing Test:**
   - Upload test receipt to Slack
   - Verify Google Sheets append
   - Confirm Slack confirmation message

2. **Query Processing Test:**
   - Send natural language query
   - Verify response formatting
   - Check data accuracy

3. **Error Handling Test:**
   - Test with invalid receipt
   - Verify error logging
   - Check manual review triggers

### Monitoring Checklist
- [ ] Structured logs are being generated
- [ ] Correlation IDs are preserved across components
- [ ] Error rates are within acceptable thresholds
- [ ] Processing times meet performance requirements
- [ ] Manual review process is working correctly

## Troubleshooting

### Common Issues
- **ADK Connection Failures:** Verify credentials and permissions
- **Slack Event Issues:** Check app scopes and event subscriptions. If Slack returns `no_text` on `chat.postMessage`, ensure the listener uses `verify_tokens=True` and update to latest code which ensures `text` is always provided.
- **Google Sheets Errors:** Verify service account permissions
- **Granite API Errors:** Check Watsonx project access and model availability

### Debug Mode
Enable debug logging in production for troubleshooting:
```bash
# Set log level
export LOG_LEVEL=DEBUG
```

### Rollback Procedure
If deployment issues occur:
1. Revert to previous ADK version
2. Check logs for correlation IDs
3. Verify all connections are working
4. Re-run smoke tests

## Security Considerations

### Secret Management
- Never commit secrets to code repository
- Use environment variables for all sensitive data
- Rotate credentials regularly
- Monitor for credential exposure in logs

### Access Control
- Limit Google Sheets access to required columns
- Use least-privilege Slack app scopes
- Monitor API usage and rate limits
- Implement audit logging for all actions

### Data Protection
- Receipt data is stored in Google Sheets (encrypted at rest)
- Original files are preserved via links
- Processing logs contain no sensitive data
- Correlation IDs enable audit trails without exposing data

## Post-Deployment

### Maintenance
- Monitor error rates and processing times
- Review manual review queue regularly
- Update prompts and schemas as needed
- Rotate credentials on schedule

### Scaling Considerations
- Monitor API rate limits (Watsonx, Google Sheets, Slack)
- Consider caching for frequently accessed data
- Implement queue processing for high-volume scenarios
- Plan for geographic distribution if needed

### Future Enhancements
- Add more sophisticated duplicate detection
- Implement expense categorization learning
- Add reporting and analytics capabilities
- Integrate with accounting software APIs 