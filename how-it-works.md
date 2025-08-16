# How It Works: Isabella Technical Deep Dive

This document provides a comprehensive technical breakdown of the Isabella AI bookkeeping agent, covering architecture, data flow, component design, and operational details.

## 🏗️ Architecture Overview

### Core Components
- **IBM Granite 8B** (`ibm/granite-8b-r-instruct`): LLM for structured data extraction and natural language query analysis.
- **Slack Socket Mode**: WebSocket-based event handling that avoids the need for public HTTP endpoints.
- **Google Sheets API**: Serves as the database for expense data persistence.
- **Vision Model** (`meta-llama/llama-3-2-11b-vision-instruct`): Used via IBM watsonx chat API for OCR on images and rasterized PDFs.

### Production Flow (Receipt Ingestion)
1.  **Slack File Upload** → `file_shared` event received via Socket Mode.
2.  **Text Extraction** → Vision model transcribes images; PDFs are rasterized and then transcribed.
3.  **AI Processing** → `tools/receipt_processor.py` uses Granite to extract a structured JSON object from the text.
4.  **Data Persistence** → `tools/sheets_manager.py` appends the validated data to Google Sheets.
5.  **Confirmation** → A confirmation message is posted back to the Slack channel.

### Production Flow (Query Analysis)
1.  **Slack Message** → A natural-language query is sent in the channel.
2.  **Query Analysis** → `tools/query_analyzer.py` uses Granite to convert the query into a structured JSON "query plan".
3.  **Execution** → `tools/controller.py` fetches all data from Google Sheets and executes the plan locally (filtering, aggregating, sorting).
4.  **Response** → A formatted summary, table, or message is posted back to Slack.

## 📁 Project Structure

```
Isabella/
├── how-it-works.md               # This detailed technical document
├── tools/
│   ├── slack_socket_runner.py    # Socket Mode listener (production entrypoint)
│   ├── controller.py             # Main orchestration logic for receipts and queries
│   ├── query_analyzer.py         # NLQ-to-JSON plan conversion
│   ├── text_extractor.py         # OCR and PDF text extraction
│   ├── receipt_processor.py      # Granite integration for receipts
│   ├── sheets_manager.py         # Google Sheets operations
│   └── slack_interface.py        # Slack event handling
├── models/
│   └── granite_client.py         # IBM Watsonx API client
├── integrations/
│   ├── google_sheets_api.py      # Google Sheets API wrapper
│   └── slack_api.py              # Slack API utilities
├── config/
│   ├── settings.py               # Environment configuration
│   └── prompts.py                # Granite prompts (single source of truth)
├── data/
│   ├── schemas/                  # JSON validation schemas
│   └── templates/                # Google Sheets templates
└── tests/                        # Comprehensive test suite
```

## ⚙️ Component Deep Dive

### 1. Granite Client (`models/granite_client.py`)
- **Purpose**: Manages all IBM Watsonx API interactions for the Granite model.
- **Authentication**: Obtains an IAM access token from `https://iam.cloud.ibm.com/identity/token` using the `WATSONX_API_KEY`. The token is cached in memory and automatically refreshed upon expiration.
- **API Integration**: Calls the Text Generation endpoint (`/ml/v1/text/generation`). It sends the `model_id` and `project_id` from the environment and parses the `generated_text` from the response. It includes helpers for safely parsing JSON from the model's text output, stripping common markdown fences.

### 2. Slack Socket Mode Listener (`tools/slack_socket_runner.py`)
- **Purpose**: A dedicated WebSocket listener for Slack events, enabling local development and deployment without public HTTP endpoints.
- **Implementation**: Uses `slack-bolt` and `SocketModeHandler`. It initializes all core components (Extractor, Granite Client, Controller, etc.) and starts a blocking process to handle events continuously.
- **Event Processing**: Receives `file_shared` and `message` events and routes them to the appropriate handlers in `tools/slack_interface.py`.

### 3. Controller (`tools/controller.py`)
- **Purpose**: The central orchestrator that connects all other tools.
- **`handle_file_shared`**: Manages the receipt ingestion pipeline: calls the text extractor, then the receipt processor, checks for duplicates, and appends to the sheet.
- **`handle_query`**: Manages the query pipeline: calls the query analyzer to get a plan, fetches all data from the sheet, and then executes the plan's logic (filtering, aggregation, etc.) in-memory. It contains fallback logic to handle old receipts by re-querying on `processed_date` if the initial query by `date` yields no results.

### 4. Query Analyzer (`tools/query_analyzer.py`)
- **Purpose**: Translates a natural-language question into a precise JSON query plan.
- **Workflow**:
    1.  Injects the user query and current date into a robust prompt from `config/prompts.py`.
    2.  Calls the Granite model to generate a JSON string.
    3.  Parses the JSON robustly, with logic to extract a valid JSON object even if it's embedded in surrounding text.
    4.  Normalizes the raw JSON into a validated plan, filling in default values and coercing types to ensure the executor receives a predictable schema.
    5.  Resolves relative dates (e.g., "last month") into explicit `YYYY-MM-DD` start and end dates.

## 🔧 Configuration

All secrets and configuration are managed via environment variables loaded from a `.env` file in the project root.

**IBM Watsonx (Granite)**
- `WATSONX_API_KEY`: IBM Cloud IAM API key.
- `WATSONX_PROJECT_ID`: Watsonx project identifier.
- `WATSONX_URL`: Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`).
- `GRANITE_MODEL_ID`: Model identifier (`ibm/granite-8b-r-instruct`).

**Slack Integration**
- `SLACK_BOT_TOKEN`: Bot user OAuth token (`xoxb-...`).
- `SLACK_APP_TOKEN`: App-level token for Socket Mode (`xapp-...`).
- `SLACK_SIGNING_SECRET`: Request verification secret.

**Google Sheets**
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Path to the service account JSON credentials file.
- `GOOGLE_SHEETS_SPREADSHEET_ID`: ID of the target spreadsheet.
- `GOOGLE_SHEETS_WORKSHEET_NAME`: Name of the worksheet for data.

**Business Rules**
- `DUPLICATE_DETECTION_ENABLED`: `true` or `false` to enable vendor/amount/date duplicate checks.

## 🚨 Error Handling and Resilience

- **Retry Mechanisms**: The `tenacity` library is used to implement exponential backoff for all external API calls (Granite, Google Sheets, OCR), making the system resilient to transient network failures.
- **Robust Parsing**: The Query Analyzer and Receipt Processor can handle malformed JSON outputs from the LLM by stripping markdown fences and extracting the first valid JSON object.
- **Fallback Logic**: The Controller's query handler will automatically retry date-filtered queries on the `processed_date` column if the initial filter on the receipt's `date` returns no results, which is useful for querying historical data. It also relaxes category filters on "no data" scenarios to improve user experience.
- **Graceful Degradation**: If AI-based receipt processing fails, the system falls back to a set of basic heuristics (regex) to extract the vendor, amount, and date, ensuring that some data is captured rather than none.

## 🔒 Security

- **No Secrets in Code**: All credentials and sensitive configurations are managed exclusively through environment variables.
- **Least Privilege Principle**: The Slack bot is configured with the minimal set of scopes required for its operation (`chat:write`, `files:read`). The Google Sheets service account has editor access only to the specific target spreadsheet.
- **Secure File Handling**: Receipts downloaded from Slack are stored in temporary files that are automatically cleaned up after processing.
- **Token Authentication**: All API calls use industry-standard token-based authentication (IAM for IBM Cloud, OAuth2 for Slack and Google).
- **No Public Endpoints**: The use of Slack's Socket Mode means the application does not need to expose any public HTTP endpoints, significantly reducing the attack surface. 