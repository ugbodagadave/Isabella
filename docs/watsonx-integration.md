# IBM watsonx Integration Guide

This document provides a technical overview of how Isabella integrates with the IBM watsonx platform, supporting two primary modes of operation:
1.  **Direct watsonx.ai Integration**: Using the Granite family of models directly via the Watsonx API for maximum control.
2.  **Orchestrate Framework**: Using IBM watsonx Orchestrate to build, manage, and expose skills as part of a larger automation ecosystem.

The current implementation in the `main` branch uses the **direct watsonx.ai integration** method.

## 1. Direct watsonx.ai Integration (Current Method)

This approach involves making direct API calls to the watsonx.ai platform to access the Granite models for receipt processing and query analysis.

### Core Components
- **Granite Client (`models/granite_client.py`)**: A dedicated client that handles authentication and API requests to the watsonx.ai text generation endpoint. It automatically manages IAM token refreshes.
- **Slack Socket Mode Listener (`tools/slack_socket_runner.py`)**: The entrypoint that initializes all components and listens for Slack events. It directly calls the `GraniteClient` as needed.

### Data Flow
1.  **Event Trigger**: A user uploads a receipt or sends a query in Slack.
2.  **Component Invocation**: The `Controller` directly invokes either the `ReceiptProcessor` or the `QueryAnalyzer`.
3.  **API Call**: These tools use the `GraniteClient` to make a secure API call to the watsonx.ai endpoint, passing the relevant text and prompt.
4.  **Response Handling**: The client parses the `generated_text` from the API response and returns it to the controller for further processing.

## 2. IBM watsonx Orchestrate Integration (Alternative Method)

This approach treats Isabella's capabilities as "skills" within the Orchestrate framework. While not the current default, the architecture is designed to support this model.

### Conceptual Architecture
- **Agent Definition (`agent.yaml`)**: Defines the "Isabella" agent and its skills (e.g., `process_receipt`, `answer_query`) for the Orchestrate platform.
- **Orchestrate Server**: A local or cloud-based Orchestrate instance that loads the agent definition.
- **Skill Implementation**: The tools in the `/tools` directory are exposed as the underlying implementation for the skills defined in `agent.yaml`.

### Data Flow with Orchestrate
1.  **External Trigger**: An event (e.g., a new email with a receipt attachment) is received by an Orchestrate-connected app.
2.  **Orchestrate Flow**: A pre-defined automation flow in Orchestrate is triggered.
3.  **Skill Execution**: The flow invokes the `process_receipt` skill from the Isabella agent.
4.  **Tool Invocation**: Orchestrate calls the underlying tool (e.g., `tools.controller.handle_file`) to execute the logic.
5.  **Response**: The result is returned to the Orchestrate flow, which could then perform further actions, like sending a notification or updating a database.

For a complete guide to setting up and running the local Orchestrate Developer Edition, see the **[Orchestrate Setup Guide](docs/setup.md)**. 