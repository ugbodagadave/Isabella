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

3. Create `.env` based on `.env.sample` and ensure variables are set (do not commit the `.env`). See `config/settings.py` for keys used. Reference IBM docs: [`Getting started`](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=getting-started-watsonx-orchestrate).

4. Place Google service credentials at `./config/google-credentials.json` (you will provide this).

5. Run tests
```
pytest -q
```

6. Commit and push (PowerShell)
```
git add . ; git commit -m "feat: scaffold project" ; git push origin main
``` 