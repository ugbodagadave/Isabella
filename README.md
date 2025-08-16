# Isabella — AI Bookkeeping Agent

Isabella is an AI bookkeeping agent that streamlines expense management. It uses **IBM Granite** to extract structured data from receipts, stores it in Google Sheets, and allows you to ask natural-language questions about your spending through Slack. The system is designed for extensibility, with an architecture that supports both direct AI model integration and orchestration via **IBM watsonx Orchestrate**.

### High-Value Use Cases
Isabella's automated data entry and analysis capabilities are valuable across various industries:
- **Consulting & Professional Services**: Effortlessly track project-related expenses, client dinners, and travel costs, simplifying client billing and reimbursement.
- **Retail & Small Business**: Automate the logging of supplier invoices, utility bills, and daily sales receipts, providing a real-time overview of operational costs.
- **Startups & Tech**: Manage subscriptions for SaaS tools, cloud infrastructure bills, and hardware purchases with minimal administrative overhead.
- **Freelancers & Solopreneurs**: Simplify tax preparation by automatically categorizing business lunches, travel, and equipment costs throughout the year.

## How It Works: A Step-by-Step Guide
1.  **Receipt Upload**: A user uploads a receipt (image or PDF) to a designated Slack channel.
2.  **Intelligent OCR**: A vision model extracts the raw text from the receipt.
3.  **AI-Powered Structuring**: The text is sent to the **IBM Granite** model, which intelligently extracts key details like vendor, date, amount, and category, returning a structured JSON object.
4.  **Data Storage**: The structured data is securely appended as a new row in a Google Sheet, creating a permanent, auditable record.
5.  **Natural Language Query**: Users can ask questions in the same Slack channel, like `How much did I spend on travel last month?`.
6.  **AI-Powered Analysis**: **IBM Granite** analyzes the question and converts it into a precise "query plan."
7.  **Execution & Response**: The system uses the plan to filter and aggregate data from the Google Sheet and delivers a clear, formatted answer back to the user in Slack.

For a deeper technical breakdown of the architecture and components, see the **[How It Works](how-it-works.md)** document.

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- A Slack App with Socket Mode enabled
- Google Service Account credentials
- IBM Watsonx Account for Granite model access

### Environment Setup
1.  **Clone the repository** and navigate into the directory.
2.  **Create and activate a virtual environment:**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```
3.  **Install dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file** in the project root and populate it with your credentials.

### Key Environment Variables
```
# IBM Watsonx (for Granite Model)
WATSONX_API_KEY="your_watsonx_api_key"
WATSONX_PROJECT_ID="your_watsonx_project_id"
WATSONX_URL="https://us-south.ml.cloud.ibm.com"
GRANITE_MODEL_ID="ibm/granite-8b-r-instruct"

# Slack Integration
SLACK_BOT_TOKEN="xoxb-your-bot-token"
SLACK_APP_TOKEN="xapp-your-app-token-for-socket-mode"

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH="path/to/your/credentials.json"
GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id"
```

### Run the Agent
```powershell
# Start the Socket Mode listener (leave running in a terminal)
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

## 📚 Documentation
- **[How It Works](how-it-works.md)**: A detailed technical breakdown of the architecture.
- **[IBM watsonx Integration](docs/watsonx-integration.md)**: Technical details on how to integrate with both IBM Granite and IBM watsonx Orchestrate.
- **[API Reference](docs/api_reference.md)**: Details on tool contracts and the query plan schema.

## 🧪 Testing
```powershell
# Run all non-end-to-end tests
pytest -m "not e2e"
``` 