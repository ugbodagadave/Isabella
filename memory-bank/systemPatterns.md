# System Patterns

## Architectural Overview

Isabella follows a **multi-agent AI architecture** specifically designed for accounting professionals, where specialized AI models collaborate to deliver comprehensive expense management with the accuracy and audit requirements essential for professional bookkeeping.

## Core Design Patterns

### 1. Multi-Modal Document Processing Pattern
**Problem**: Accounting professionals receive financial documents in various formats (receipt images, PDF invoices, scanned documents) requiring different processing approaches.

**Solution**: Dual-pathway processing architecture that intelligently routes documents based on type:

```
Document Input → Format Detection → Processing Route
├── Images → Meta Llama 3.2 11B Vision → Text Extraction
├── PDFs → pdfplumber Library → Text Extraction  
└── Text → IBM Granite 8B → Structured Data Extraction
```

**Implementation**:
- `TextExtractor` automatically detects document type and selects optimal processing method
- Vision model handles complex receipt layouts, handwritten notes, and poor image quality
- PDF library provides reliable text extraction for digital invoices
- Unified output format ensures consistent downstream processing

### 2. Schema-Driven Financial Data Extraction
**Problem**: Professional bookkeeping requires consistent, validated financial data structure for compliance and audit requirements.

**Solution**: Strict schema enforcement with AI-powered extraction and validation:

```json
{
  "vendor": "string (cleaned, proper capitalization)",
  "amount": "number (validated, no currency symbols)",
  "date": "string (YYYY-MM-DD format)",
  "category": "string (from accounting standard categories)",
  "tax_amount": "number (required, 0 if not found)"
}
```

**Implementation**:
- `ReceiptProcessor` applies accounting knowledge through structured prompts
- Schema validation ensures every field meets professional standards
- Fallback mechanisms handle edge cases while maintaining data integrity
- Audit trail captures all processing decisions for compliance

### 3. Agentic AI Coordination Pattern
**Problem**: Complex financial document processing requires multiple specialized AI capabilities working in coordination.

**Solution**: Multi-agent system where each AI agent has specific expertise:

**Vision Agent** (Meta Llama 3.2 11B Vision):
- Understands receipt layouts and visual elements
- Extracts text from images with high accuracy
- Handles poor image quality and various formats

**Financial Extraction Agent** (IBM Granite 8B):
- Applies accounting knowledge for data structuring
- Understands vendor names, tax calculations, and expense categories
- Produces consistent JSON output for downstream processing

**Query Analysis Agent** (IBM Granite 8B):
- Processes natural language financial questions
- Converts conversational queries to structured search plans
- Understands accounting terminology and time periods

**Coordination Controller**:
- Orchestrates multi-agent workflows
- Manages error handling and retry mechanisms
- Maintains audit trails across all agent interactions

### 4. Natural Language Financial Intelligence
**Problem**: Accounting professionals need to query expense data without learning complex interfaces or spreadsheet formulas.

**Solution**: Conversational AI that understands accounting terminology and financial concepts:

```
Natural Language → Query Analysis → Structured Plan → Data Filtering → Professional Report
```

**Examples**:
- *"Show me travel expenses over $100 last quarter"* → Time filter + Category filter + Amount filter
- *"What's our total spending at Office Depot?"* → Vendor aggregation across all time
- *"Compare this month to last month"* → Comparative analysis with percentage changes

**Implementation**:
- `QueryAnalyzer` converts natural language to structured JSON query plans
- Controller executes plans with filters, aggregations, and sorting
- Output formatting provides professional-grade summaries and tables

### 5. Professional Integration Pattern
**Problem**: Accounting workflows require seamless integration with existing professional tools and security requirements.

**Solution**: Multi-layered integration that respects professional security and workflow needs:

**Slack Integration Layer**:
- Socket Mode WebSocket connection (no public HTTP endpoints)
- File upload handling with temporary storage and cleanup
- Professional confirmation messages with processing status

**Google Sheets Integration Layer**:
- Header-driven mapping compatible with accounting software
- Canonical field mapping for consistent data structure
- Service account authentication for enterprise security

**IBM Watsonx Integration Layer**:
- Enterprise-grade AI model access with IAM authentication
- Local deployment option for data privacy requirements
- Comprehensive error handling and retry mechanisms

### 6. Audit Trail and Compliance Pattern
**Problem**: Professional bookkeeping requires complete audit trails and compliance documentation for financial examinations.

**Solution**: Comprehensive logging and correlation tracking throughout the entire processing pipeline:

```
Receipt Upload → Correlation ID Assignment → Processing Logs → Data Validation → Audit Documentation
```

**Implementation**:
- Every transaction receives unique correlation ID for end-to-end tracking
- Tool-level logging captures specific actions taken by each component
- Processing timestamps and status tracking for compliance requirements
- Schema validation logs for data integrity verification

## Critical Design Decisions

### 1. Local-First Architecture
**Decision**: IBM Watsonx Orchestrate Developer Edition with local deployment
**Rationale**: Accounting firms require data privacy and control over financial information
**Impact**: Enterprise security without cloud dependencies, full audit control

### 2. Multi-Modal AI Selection
**Decision**: Separate specialized models for vision and text processing
**Rationale**: Different AI models excel at different tasks - vision vs. structured data extraction
**Impact**: Higher accuracy than single-model approaches, professional-grade reliability

### 3. Schema-First Data Structure
**Decision**: Strict JSON schema enforcement for all extracted data
**Rationale**: Professional bookkeeping requires consistent, validated data structure
**Impact**: Reliable data for accounting software integration, audit compliance

### 4. Slack-Centric Interface
**Decision**: Slack as primary user interface rather than custom application
**Rationale**: Accounting firms already use Slack for communication
**Impact**: Zero learning curve, seamless workflow integration

### 5. Google Sheets as Data Store
**Decision**: Google Sheets rather than database for structured data storage
**Rationale**: Familiar format for accounting professionals, easy export/import
**Impact**: Compatible with existing accounting software workflows

## Error Handling and Resilience

### Multi-Level Fallback Strategy
1. **AI Model Fallbacks**: If Granite returns invalid JSON, retry with stricter prompts
2. **Heuristic Extraction**: If AI fails completely, extract key data using text patterns
3. **Human Review Path**: Flag low-confidence extractions for manual verification
4. **Data Validation**: Schema enforcement catches and corrects structural issues

### Retry Mechanisms
- **Exponential Backoff**: For API failures and temporary service issues
- **Smart Retries**: Different strategies for different failure types
- **Circuit Breakers**: Prevent cascade failures in external service dependencies

### Professional Error Communication
- **User-Friendly Messages**: Clear explanations in Slack without technical jargon
- **Processing Status**: Real-time updates on receipt processing progress
- **Error Recovery**: Suggestions for resolving common issues

## Performance and Scalability

### Context Window Optimization
- **Smart Text Trimming**: Keep first 40 and last 40 lines of long receipts
- **Efficient Prompting**: Structured prompts that fit within model context limits
- **Batch Processing**: Handle multiple receipts efficiently

### Caching and Optimization
- **Token Management**: Efficient IBM Watsonx API token reuse
- **Image Processing**: PIL-based optimization with fallback handling
- **Database Queries**: Efficient Google Sheets API usage patterns

This architecture provides the foundation for reliable, professional-grade expense management that meets the accuracy, security, and audit requirements essential for accounting professionals while maintaining the simplicity and efficiency that drives adoption. 