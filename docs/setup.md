## Setup

1. Create and activate a virtualenv
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Create `.env` based on `.env.sample` and ensure variables are set (do not commit the `.env`). See `config/settings.py` for keys used. IBM ADK is deferred to deployment.

4. Place Google service credentials at `./config/google-credentials.json` (you have provided this).

5. Run tests
```
pytest -q
```

### Live E2E tests (fully real integrations)
- E2E tests run only when selected via marker; they use live services, not mocks.
- Provide either `E2E_RECEIPT_PATH` (local path) or `E2E_RECEIPT_URL` (http/https, Slack links supported with `SLACK_BOT_TOKEN`).

Run only E2E tests (PowerShell):
```
pytest -m e2e -q
```

Note: E2E writes a row with `Description=E2E_TEST` to your sheet; you can remove it afterward if desired.

6. Commit and push (PowerShell)
```
git add . ; git commit -m "chore: deps update and docs" ; git push origin main
``` 