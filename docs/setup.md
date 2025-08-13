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

6. Commit and push (PowerShell)
```
git add . ; git commit -m "chore: deps update and docs" ; git push origin main
``` 