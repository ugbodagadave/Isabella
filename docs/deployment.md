# Deployment

- Local development uses direct clients for OCR, Granite, Google Sheets, and Slack.
- Deployment with IBM watsonx Orchestrate ADK wires these tools into an agent; business logic remains identical to the E2E flow:
  - OCR → Granite → Schema validation → Sheets append → Slack confirmation.
- Ensure environment variables in production match those in `config/settings.py`.
- Recommended: create the target Google Sheets with the header row from `data/templates/sheets_template.json`.

1. Ensure `.env` is complete. Do not commit it. Keys are read by `config/settings.py`.
2. Verify Google credentials exist at `./config/google-credentials.json`.
3. Install ADK and initialize:
```
pip install watsonx-orchestrate-adk
orchestrate dev init
orchestrate connections create
```
4. Validate the `agent.yaml` tool paths.
5. Dry-run locally and run tests:
```
pytest -q
```
6. Commit and push to GitHub.
7. Deploy agent using ADK or Orchestrate UI per IBM docs: [`Getting started`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate). 