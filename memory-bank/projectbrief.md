# Project Brief

## Overview
Isabella is an AI-powered bookkeeping agent built on IBM Watsonx Orchestrate and IBM Granite 3.3. The agent processes receipts from Slack, extracts structured expense data using advanced LLM capabilities, and manages expense tracking in Google Sheets with natural language querying capabilities.

## Current Status
- **Phase:** M5 Deployment Preparation
- **Milestones Completed:** M0-M4 (Repository setup, Core tools, Integrations, E2E flow, Query processing)
- **Next Phase:** M5 (IBM Watsonx Orchestrate ADK deployment with observability and audit trails)

## Core Capabilities
- **Receipt Processing:** OCR/PDF text extraction with IBM Granite 3.3 LLM analysis
- **Intelligent Categorization:** AI-powered expense categorization with confidence scoring
- **Natural Language Queries:** Ask questions about expenses in plain English
- **Slack Integration:** Upload receipts and query expenses through familiar interface
- **Google Sheets Management:** Automated expense tracking with structured data storage
- **Duplicate Detection:** Identify and flag potential duplicate receipts
- **Audit Trails:** Complete tracking with correlation IDs and processing metadata

## Technical Architecture
- **LLM-first Design:** IBM Granite 3.3 for receipt understanding and query analysis
- **Minimal Tools:** Four core tools with focused responsibilities
- **Environment-driven Configuration:** All settings via environment variables
- **Comprehensive Testing:** Unit, integration, and end-to-end tests with real integrations
- **Production Ready:** Structured logging, error handling, and retry mechanisms

## Development Workflow
- **Strict Process:** Test → Document → Commit → Push for every change
- **Memory Bank:** Comprehensive documentation maintained in markdown format
- **Quality Assurance:** All tests must pass before deployment
- **Documentation:** API reference, setup guides, and deployment instructions

## Deployment Strategy
- **Platform:** IBM Watsonx Orchestrate ADK for production deployment
- **Observability:** Structured logging with correlation IDs and metrics
- **Manual Review:** Human oversight for low-confidence or ambiguous cases
- **Security:** Environment variables for all secrets, no credentials in code 