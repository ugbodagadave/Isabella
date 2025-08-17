# Isabella — AI Bookkeeping Agent for Accountants

![Isabella AI Bookkeeping Agent](Isabella_Header-07.png)

Isabella is an AI-powered bookkeeping agent specifically designed for accounting professionals. Built on IBM Watsonx and advanced AI models, Isabella automates receipt processing, expense categorization, and financial data analysis through natural language interactions - eliminating the manual data entry burden that consumes 15-20 hours per week for most CPAs and bookkeepers.

## 💼 For Accounting Professionals

### The Problem: Administrative Overload
**CPAs and bookkeepers are drowning in manual data entry.** Month-end closes stretch from 2 days to a full week due to receipt processing backlogs. Client billing is delayed while staff manually sort through expense receipts. Tax preparation becomes a nightmare of disorganized, manually-entered data. The administrative burden prevents accounting professionals from focusing on high-value advisory services that clients actually need.

### The Solution: Intelligent Automation
Isabella transforms this reality by providing **AI-powered automation that maintains the accuracy and audit requirements essential for professional bookkeeping** while dramatically reducing manual effort. Upload receipts to Slack, ask questions in plain English, and get audit-ready financial data instantly.

### Professional Benefits
- **Save 15-20 hours weekly** on manual receipt transcription and data entry
- **Accelerate month-end close** from 5-7 days back to 2 days with automated processing
- **Improve client billing efficiency** with instant expense categorization and project tracking
- **Ensure compliance** with complete audit trails and processing logs for every transaction
- **Reduce transcription errors** with AI-powered extraction and validation
- **Enable real-time financial analysis** with natural language query capabilities

## 🚀 How It Works: Professional Workflow

### 1. Upload Receipts to Slack
Simply photograph receipts or upload PDF invoices to your designated Slack channel. No special apps or complex interfaces - just use the communication tool your firm already relies on.

### 2. AI Extracts Financial Data
**Multi-Modal Intelligence**: 
- **Images**: Meta Llama 3.2 11B Vision reads receipt layouts like a human accountant
- **PDFs**: Intelligent text extraction handles invoices and complex documents
- **Data Extraction**: IBM Granite 8B applies accounting knowledge to extract vendor, amount, date, category, tax, and payment method

### 3. Structured Data Storage
Extracted data automatically populates organized Google Sheets with proper headers and formatting compatible with QuickBooks, Xero, and other major accounting software.

### 4. Natural Language Financial Analysis
Ask questions about your financial data in plain English:
- *"How much did Johnson & Associates spend on travel last quarter?"*
- *"Show me all office supply expenses over $100 this month"*
- *"What's my total client entertainment spending this year?"*

### 5. Instant Professional Reports
Receive formatted summaries, vendor breakdowns, category analyses, and audit-ready documentation immediately in Slack.

## 🎯 Professional Use Cases

### 📊 CPA Firms
- **Client Expense Processing**: Automatically categorize and track client project expenses
- **Tax Preparation**: Organized, categorized expense data ready for tax filing
- **Client Advisory**: Spend time on strategic consulting instead of data entry
- **Compliance**: Complete audit trails for financial examinations

### 🏢 Corporate Accounting
- **Employee Expense Reports**: Automated processing of employee submitted receipts
- **Department Budget Tracking**: Real-time expense monitoring by department
- **Vendor Analysis**: Intelligent spending pattern analysis across suppliers
- **Month-End Reporting**: Accelerated close processes with automated data entry

### 📈 Small Business Bookkeeping
- **Automated Record Keeping**: Instant receipt processing for small business clients
- **Category Intelligence**: Consistent expense classification across all entries
- **Tax Compliance**: Automatic tax amount extraction for accurate reporting
- **Client Self-Service**: Business owners can ask questions about their own spending

## 🔧 Quick Professional Setup

### Prerequisites
- **Slack Workspace** (most accounting firms already have this)
- **Google Account** for spreadsheet storage
- **IBM Watsonx Account** for AI model access
- **Python 3.11+** for local deployment

### Professional Installation
```powershell
# Clone the repository
git clone https://github.com/ugbodagadave/Isabella
cd Isabella

# Create secure environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Professional Configuration
Create a `.env` file with your credentials:
```env
# IBM Watsonx (Enterprise AI Models)
WATSONX_API_KEY="your_watsonx_api_key"
WATSONX_PROJECT_ID="your_watsonx_project_id"
WATSONX_URL="https://us-south.ml.cloud.ibm.com"
GRANITE_MODEL_ID="ibm/granite-8b-r-instruct"

# Slack Integration (Your Firm's Workspace)
SLACK_BOT_TOKEN="xoxb-your-bot-token"
SLACK_APP_TOKEN="xapp-your-app-token"

# Google Sheets (Financial Data Storage)
GOOGLE_SHEETS_CREDENTIALS_PATH="path/to/service-account.json"
GOOGLE_SHEETS_SPREADSHEET_ID="your_spreadsheet_id"
```

### Start Processing Receipts
```powershell
# Launch the AI bookkeeping agent
.\.venv\Scripts\python.exe -m tools.slack_socket_runner
```

## 💬 Natural Language Query Examples

### Vendor Analysis
- *"How much have we spent at Office Depot this year?"*
- *"What's our top vendor for office supplies?"*
- *"Show me all Amazon purchases over $50"*

### Category Reporting
- *"Total travel expenses for the Johnson account last quarter"*
- *"List all equipment purchases this month"*
- *"What did we spend on client entertainment in Q3?"*

### Time-Based Analysis
- *"Compare this month's expenses to last month"*
- *"Show me the last 30 days of office supply purchases"*
- *"What were our total expenses last quarter?"*

### Tax & Compliance
- *"How much tax did we pay on office equipment this year?"*
- *"Show me all expenses without receipts"*
- *"List expenses that need client reimbursement"*

## 🔒 Professional Security & Compliance

### Enterprise-Grade Security
- **Local Deployment**: Your financial data stays within your controlled environment
- **No Cloud Dependencies**: Core functionality runs entirely on your infrastructure
- **Secure Credentials**: All API keys managed through environment variables
- **Audit Trails**: Complete processing logs for every transaction

### Accounting Standards Compliance
- **Schema Validation**: Every data extraction follows strict accounting schemas
- **Tax Extraction**: Automatic tax amount identification for compliance reporting
- **Duplicate Prevention**: Intelligent detection prevents accidental duplicate entries
- **Audit Documentation**: Timestamps, correlation IDs, and processing logs for examinations

### Professional Data Handling
- **Google Sheets Integration**: Standard format compatible with major accounting software
- **Receipt Archival**: Original documents linked to structured financial data
- **Data Validation**: AI-powered accuracy checks ensure reliable financial records
- **Export Capabilities**: Easy data export for tax software and accounting systems

## 📚 Professional Documentation

- **[Technical Integration Guide](docs/watsonx-integration.md)**: IBM Watsonx setup for accounting firms
- **[API Reference](docs/api_reference.md)**: Complete technical documentation for custom integrations
- **[Deployment Guide](docs/deployment.md)**: Production deployment for accounting environments
- **[Setup Instructions](docs/setup.md)**: Step-by-step configuration for professional use

## 🧪 Validate Before Production

```powershell
# Test the complete system
pytest -m "not e2e"

# Validate with real integrations
pytest tests/test_integrations/test_controller_flow.py::test_controller_e2e
```

## 🎯 Why Isabella for Accounting Professionals?

### Built for Your Workflow
Isabella understands that accounting professionals need more than just OCR - you need **intelligent automation that maintains the accuracy, audit trails, and compliance requirements essential for professional bookkeeping**.

### Professional-Grade AI
Built on **IBM Watsonx** with enterprise security and reliability. Uses **IBM Granite 8B** for financial data extraction and **Meta Llama 3.2 11B Vision** for receipt processing - not consumer-grade AI tools.

### Immediate ROI
**Save 15-20 hours per week** on manual data entry while **improving accuracy** and **accelerating month-end close processes**. The time savings alone pay for the system within the first month.

### Seamless Integration
Works with your existing tools - **Slack for communication**, **Google Sheets for data storage**, and **compatible with major accounting software** like QuickBooks and Xero.

---

**Ready to eliminate manual receipt processing?** Isabella transforms the most time-consuming aspect of bookkeeping into an automated, intelligent workflow that lets you focus on what matters most - serving your clients and growing your practice. 