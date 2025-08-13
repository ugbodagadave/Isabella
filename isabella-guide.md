# Isabella AI Bookkeeping Agent - Complete Implementation Guide

This document mirrors your high-level implementation guidance and adds explicit references.

## Overview

Isabella is an AI-powered bookkeeping agent using IBM Watsonx Orchestrate and IBM Granite 3.3. It processes receipt uploads via Slack, extracts financial data, and manages Google Sheets for expense tracking.

Reference: IBM watsonx Orchestrate — [`Getting started`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate).

## Core Philosophy

**LLM-First Processing**: Let IBM Granite 3.3 understand, extract, and structure information from unstructured receipt text, replacing complex parsing pipelines.

## Architecture Overview

- `agent.yaml` defines behavior, instructions, and tools
- Four Python tools
- IBM Watsonx Orchestrator intelligently chooses tools
- Granite 3.3 handles extraction and analysis

## IBM Granite 3.3 Model

Granite 3.3 handles:
- Receipt text analysis and structured data extraction
- Expense categorization and validation
- Natural language query processing
- Data cleaning and standardization

## Essential Tools

1. `text_extractor.py`: PDF/Image → text using `PyPDF2`/`pdfplumber` and Tesseract OCR
2. `receipt_processor.py`: Send text to Granite 3.3; get structured JSON
3. `sheets_manager.py`: Write/query Google Sheets
4. `slack_interface.py`: File uploads, orchestration, responses

## Project Structure (Streamlined)

```
├── agent.yaml
├── requirements.txt
├── .env
├── .env.sample
├── .gitignore
│
├── tools/
│   ├── __init__.py
│   ├── text_extractor.py
│   ├── receipt_processor.py
│   ├── sheets_manager.py
│   └── slack_interface.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── prompts.py
│   └── connections.yaml
│
├── models/
│   ├── __init__.py
│   └── granite_client.py
│
├── integrations/
│   ├── __init__.py
│   ├── google_sheets_api.py
│   └── slack_api.py
│
├── data/
│   ├── schemas/
│   │   ├── receipt_schema.json
│   │   └── expense_schema.json
│   ├── templates/
│   │   ├── expense_categories.json
│   │   └── sheets_template.json
│   └── receipts/
│       ├── processed/
│       └── backups/
│
├── tests/
│   ├── __init__.py
│   ├── test_tools/
│   │   ├── test_text_extractor.py
│   │   ├── test_receipt_processor.py
│   │   ├── test_sheets_manager.py
│   │   └── test_slack_interface.py
│   ├── test_integrations/
│   │   ├── test_google_sheets_api.py
│   │   └── test_slack_api.py
│   └── test_data/
│       ├── sample_receipts/
│       │   ├── sample_receipt_1.pdf
│       │   ├── sample_receipt_2.jpg
│       │   └── sample_receipt_3.png
│       ├── mock_responses/
│       └── expected_outputs/
│
└── docs/
    ├── setup.md
    ├── api_reference.md
    └── deployment.md
```

## Workflow Designs

### Receipt Processing
1. Upload file in Slack
2. Extract text (PDF/image)
3. LLM processing with Granite 3.3 → structured JSON
4. Store in Google Sheets with file reference

### Query Processing
1. User question in Slack
2. Retrieve data from Sheets based on LLM understanding
3. Granite 3.3 formats the answer

## agent.yaml Template

```yaml
agent:
  name: "Isabella"
  description: "AI bookkeeping agent for intelligent receipt processing and expense analysis"
  model: "ibm/granite-3.3-8b-instruct"
  instructions: |
    You are Isabella, a professional AI bookkeeping agent that helps users manage their business expenses efficiently.
    You excel at processing receipts, extracting financial data with high accuracy, and providing insights about spending patterns.
    Always maintain a helpful, professional tone while ensuring data accuracy and user satisfaction.
  
tools:
  - name: "text_extractor"
    description: "Extract text content from PDF receipts and images using OCR"
    file: "tools/text_extractor.py"
  
  - name: "receipt_processor"
    description: "Process receipt text using AI to extract structured expense data"
    file: "tools/receipt_processor.py"
  
  - name: "sheets_manager"
    description: "Manage Google Sheets operations for expense tracking and queries"
    file: "tools/sheets_manager.py"
  
  - name: "slack_interface"
    description: "Handle Slack interactions, file uploads, and user communications"
    file: "tools/slack_interface.py"

channels:
  - name: "slack"
    type: "slack_app"
    config:
      app_token: "${SLACK_APP_TOKEN}"
      bot_token: "${SLACK_BOT_TOKEN}"
      signing_secret: "${SLACK_SIGNING_SECRET}"
```

## Prompt Design

```python
RECEIPT_EXTRACTION_PROMPT = """
You are Isabella, an expert AI bookkeeping agent. Analyze this receipt text and extract structured financial data.

EXTRACT THE FOLLOWING AS JSON:

REQUIRED FIELDS:
- vendor: Company/store name (cleaned, proper capitalization)
- amount: Total amount as number (no currency symbols)
- date: Date in YYYY-MM-DD format
- category: Best matching expense category from list below

OPTIONAL FIELDS (if clearly available):
- payment_method: Payment type (Cash, Credit, Debit, etc.)
- receipt_number: Transaction/receipt number
- tax_amount: Tax amount if separately shown
- location: Store location/address
- description: Brief description of purchase
- items: Array of purchased items (for detailed receipts)

EXPENSE CATEGORIES:
- Office Supplies
- Meals & Entertainment  
- Travel & Transportation
- Equipment & Software
- Marketing & Advertising
- Professional Services
- Utilities & Communications
- Training & Education
- Maintenance & Repairs
- Other Business Expenses

PROCESSING RULES:
1. Clean vendor names: remove extra spaces, fix capitalization, expand abbreviations
2. For ambiguous dates, use context clues or receipt layout
3. Choose the most specific appropriate category
4. If amount is unclear, extract the largest clearly visible total
5. Handle multiple currencies by noting the currency type
6. Return ONLY valid JSON - no explanations or additional text

RECEIPT TEXT:
{receipt_text}

JSON RESPONSE:
"""
```

```python
QUERY_ANALYSIS_PROMPT = """
You are Isabella, an AI bookkeeping agent. Analyze this user query about their expenses.

USER QUERY: {user_query}

CURRENT DATE: {current_date}

DETERMINE:
1. Query type: summary, search, analysis, or report
2. Time range: specific dates, relative periods (last month, this year, etc.)
3. Filters needed: categories, vendors, amounts, etc.
4. Response format: table, list, chart, or narrative

Return as JSON:
{
  "query_type": "summary|search|analysis|report",
  "time_range": {
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "period": "last_month|this_year|etc or null"
  },
  "filters": {
    "categories": ["category1", "category2"] or null,
    "vendors": ["vendor1", "vendor2"] or null,
    "min_amount": number or null,
    "max_amount": number or null
  },
  "response_format": "table|summary|chart|detailed"
}
"""
```

## Development Environment Setup

### IBM Watsonx Orchestrate ADK
```
pip install watsonx-orchestrate-adk
orchestrate dev init
orchestrate connections create
```

### Local Steps
1. Install ADK and dependencies
2. Configure IBM Cloud credentials
3. Set up Google Sheets and Slack integrations
4. Test tools locally before deployment
5. Deploy to Watsonx Orchestrate platform

## Google Sheets Structure

Core columns: Date, Vendor, Amount, Category, Description, Receipt_Link
Optional: Payment_Method, Receipt_Number, Tax_Amount, Location, Processed_Date, Confidence_Score

## Capabilities
- OCR and text extraction
- Intelligent categorization
- Validation and error handling
- File management and links
- Natural language queries, flexible reporting, time-based analysis
- Advanced features: duplicate detection, multiple formats, confidence scoring, audit trail

## Development Workflow
- Phase 1: Core setup
- Phase 2: LLM integration
- Phase 3: Enhancements & testing
- Phase 4: Deployment & optimization

## Best Practices
- Prompt engineering, context management, robust error handling, validation
- Unit and integration tests with realistic samples

## References
- IBM watsonx Orchestrate — [`Getting started`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate) 