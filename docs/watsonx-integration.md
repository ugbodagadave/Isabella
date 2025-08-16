# IBM watsonx Integration (Granite + Orchestrate)

This document provides comprehensive technical details on how IBM watsonx.ai (Granite) is integrated within the Isabella AI bookkeeping agent.

## Architecture Overview

### Core Components

#### 1. Granite Client (`models/granite_client.py`)
**Purpose:** Manages IBM Watsonx API interactions for the Granite model.

**Authentication Flow:**
- Obtains an IAM access token from `https://iam.cloud.ibm.com/identity/token` using `WATSONX_API_KEY`.
- The token is cached in memory with automatic refresh when expired.

**API Integration:**
- Calls the Text Generation endpoint: `{WATSONX_URL}/ml/v1/text/generation`.
- Sends `model_id` (e.g., `ibm/granite-8b-r-instruct`) and `project_id` from the environment.
- Parses `generated_text` from the response for structured data extraction or query analysis.

**Configuration:**
- `WATSONX_API_KEY`: IBM Cloud IAM API key for authentication.
- `WATSONX_URL`: Watsonx service URL (e.g., `https://us-south.ml.cloud.ibm.com`).
- `WATSONX_PROJECT_ID`: Project identifier for model access.
- `GRANITE_MODEL_ID`: The specific model identifier to be used.

#### 2. Slack Socket Mode Listener (`tools/slack_socket_runner.py`)
**Purpose:** A dedicated WebSocket listener for Slack events that avoids the need for public HTTP endpoints, making it ideal for local development and secure deployments.

**Implementation:**
- Uses `slack-bolt` and `SocketModeHandler` for WebSocket communication.
- Initializes all core components, including the `GraniteClient`, `Controller`, and `SlackInterface`.
- Runs as a blocking process for continuous event handling.

## Data Flow Architecture

### Receipt Processing Pipeline
1.  **Slack File Upload Trigger**: A `file_shared` event is received by the Socket Mode listener.
2.  **Text Extraction (OCR)**: The file is downloaded, and a vision model (`meta-llama/llama-3-2-11b-vision-instruct`) transcribes the text.
3.  **AI-Powered Data Extraction**: `tools/receipt_processor.py` calls the Granite model via `models/granite_client.py` with the extracted text and a specific prompt to get structured JSON data.
4.  **Data Persistence & Confirmation**: The validated JSON is appended to Google Sheets, and a confirmation is sent to Slack.

### Query Analysis Pipeline
1.  **Slack Message Trigger**: A `message` event containing a natural language query is received.
2.  **AI-Powered Query Analysis**: `tools/query_analyzer.py` calls the Granite model with the user's text and a prompt designed to translate the query into a structured JSON "query plan".
3.  **Execution**: `tools/controller.py` receives the plan, fetches all data from Google Sheets, and executes the query logic (filtering, aggregation) locally.
4.  **Response**: A formatted response is sent back to Slack. 