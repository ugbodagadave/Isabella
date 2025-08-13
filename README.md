# Isabella AI Bookkeeping Agent

An intelligent AI-powered bookkeeping agent built with IBM Watsonx Orchestrate and IBM Granite 3.3. Isabella processes receipt uploads via Slack, extracts financial data using advanced LLM capabilities, and manages expense tracking in Google Sheets.

## 🚀 Features

- **Smart Receipt Processing**: Extract text from PDF and image receipts using OCR
- **AI-Powered Data Extraction**: IBM Granite 3.3 intelligently parses and categorizes expenses
- **Slack Integration**: Upload receipts and query expenses through natural language
- **Google Sheets Management**: Automated expense tracking with structured data storage
- **Intelligent Categorization**: Automatic expense categorization with confidence scoring
- **Duplicate Detection**: Identify and flag potential duplicate receipts
- **Natural Language Queries**: Ask questions about your expenses in plain English

## 🏗️ Architecture

Isabella follows an **LLM-first** approach with minimal, focused tools:

- **Text Extractor**: PDF/Image → Text (OCR + PDF parsing)
- **Receipt Processor**: Text → Structured JSON (via Granite 3.3)
- **Sheets Manager**: JSON ↔ Google Sheets operations
- **Slack Interface**: User interactions and workflow orchestration

## 📋 Prerequisites

- Python 3.11+
- IBM Watsonx Orchestrate account
- Google Sheets API credentials
- Slack App configuration
- Tesseract OCR (for image processing)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ugbodagadave/Isabella.git
   cd Isabella
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.sample .env
   # Edit .env with your credentials
   ```

4. **Add Google credentials**
   - Place your Google service account JSON at `./config/google-credentials.json`

5. **Run tests**
   ```bash
   pytest
   ```

## 🔧 Configuration

### Environment Variables

Key configuration variables (see `.env.sample` for complete list):

- `WATSONX_API_KEY`: IBM Watsonx API key
- `WATSONX_PROJECT_ID`: Watsonx project identifier
- `GRANITE_MODEL_ID`: IBM Granite model (default: `ibm/granite-3.3-8b-instruct`)
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Target Google Sheets ID
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_APP_TOKEN`: Slack app token

### Google Sheets Structure

Isabella expects a Google Sheet with these columns:
- Date, Vendor, Amount, Category, Description, Receipt_Link
- Optional: Payment_Method, Receipt_Number, Tax_Amount, Location, Processed_Date, Confidence_Score

## 📖 Usage

### Receipt Processing

1. Upload a receipt (PDF or image) to your configured Slack channel
2. Isabella automatically:
   - Extracts text using OCR/PDF parsing
   - Processes with Granite 3.3 for structured data
   - Categorizes the expense
   - Stores in Google Sheets with receipt link

### Querying Expenses

Ask natural language questions in Slack:
- "How much did I spend on office supplies last month?"
- "Show me all expenses from Starbucks"
- "What's my total spending this year?"

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov
```

## 📚 Documentation

- [Setup Guide](docs/setup.md)
- [API Reference](docs/api_reference.md)
- [Deployment Guide](docs/deployment.md)
- [Project Plan](isabella-plan.md)
- [Implementation Guide](isabella-guide.md)

## 🏛️ Project Structure

```
├── agent.yaml                 # Isabella's configuration
├── tools/                     # Core processing tools
│   ├── text_extractor.py     # OCR and PDF text extraction
│   ├── receipt_processor.py  # LLM-powered data extraction
│   ├── sheets_manager.py     # Google Sheets operations
│   └── slack_interface.py    # Slack integration
├── config/                    # Configuration and prompts
├── models/                    # AI model clients
├── integrations/              # External service clients
├── data/                      # Schemas and templates
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- IBM Watsonx Orchestrate for the AI agent platform
- IBM Granite 3.3 for intelligent text processing
- Google Sheets API for data storage
- Slack API for user interface

## 📞 Support

For questions or issues, please open an issue on GitHub or contact the maintainers.

---

**Isabella** - Making bookkeeping intelligent, one receipt at a time. 📊✨ 