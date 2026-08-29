# TDEM Secure Vault Backend

Stage A FastAPI orchestration backend for the Time-Dependent Encryption Model.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The crypto and AI engines are intentionally loaded from their existing branch packages through adapters. Configure `TDEM_KSEED` from AWS Secrets Manager; the backend fails closed when the engines or secret are unavailable. Use `X-User-Id` only for local development. Production authentication should be backed by Cognito token validation.

## Test

```bash
pytest -q
```

The frontend is intentionally not included until the backend contract and integration tests are complete.
