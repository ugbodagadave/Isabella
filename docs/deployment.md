# Deployment

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