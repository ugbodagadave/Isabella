# Isabella — AI Bookkeeping Agent

Isabella is an AI bookkeeping agent that ingests receipts from Slack, extracts structured data using IBM Granite, appends it to Google Sheets, and allows you to ask natural-language questions about your expenses.

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- A Slack App with Socket Mode enabled
- Google Service Account credentials

### Environment Setup
1.  **Clone the repository**
2.  **Create and activate a virtual environment:**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```
3.  **Install dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file** in the project root and populate it with your credentials for Slack, Google Sheets, and IBM Watsonx. See `how-it-works.md` for a full list of required variables.

### Run the Agent
```powershell
# Start the Socket Mode listener (leave running in a terminal)
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

### Usage
- **Upload a receipt** (image or PDF) to your configured Slack channel to automatically process it.
- **Ask questions** in natural language, such as:
    - `What is the total I have spent at Walmart?`
    - `Top 3 categories this month`
    - `Show a table of all travel expenses from last quarter`

## 📚 Documentation
- **[How It Works](how-it-works.md)**: A detailed technical breakdown of the architecture, data flow, and components.
- **[IBM watsonx Integration](docs/watsonx-integration.md)**: Technical details on Granite integration.
- **[API Reference](docs/api_reference.md)**: Tool contracts and the query plan schema.

## 🧪 Testing
```powershell
# Run all non-end-to-end tests
pytest -m "not e2e"

# Run all tests, including e2e (requires environment variables to be set)
pytest
``` 