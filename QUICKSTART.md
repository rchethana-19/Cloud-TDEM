# TDEM Quick Start Guide

Get the TDEM Secure Vault running in under 5 minutes!

## Prerequisites

- Python 3.9+
- pip
- Terminal/Command line

## Installation (2 minutes)

### 1. Setup Python Environment

```bash
cd Cloud-TDEM
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
make install
# OR manually: pip install -r requirements.txt
```

### 3. Setup Configuration

```bash
make setup
# This will:
# - Copy .env.example to .env
# - Create data directories
# - Initialize storage paths
```

## Running the Backend (1 minute)

### Start Development Server

```bash
make run
# Server will start at http://127.0.0.1:8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Verify Health

Open in browser or curl:
```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "crypto_available": true,
  "ai_available": true,
  "storage_available": true
}
```

## API Documentation (Visit Now!)

Open your browser:
```
http://127.0.0.1:8000/docs
```

This gives you interactive Swagger documentation where you can:
- Try all endpoints
- See request/response schemas
- Test without external tools

## Quick Demo Workflow (2 minutes)

### 1. Upload a File

**Using Swagger (/docs):**
1. Click "Try it out" on POST /api/v1/files/ingest
2. Set expiry_minutes to 60
3. Upload any file
4. Click Execute
5. Note the `file_id` from response

**Using curl:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/ingest?expiry_minutes=60" \
  -H "Authorization: Bearer dev-token" \
  -F "file=@yourfile.txt"
```

### 2. List Your Files

**Using Swagger:**
1. Click GET /api/v1/files
2. Click Execute

**Using curl:**
```bash
curl "http://127.0.0.1:8000/api/v1/files" \
  -H "Authorization: Bearer dev-token"
```

### 3. Retrieve a File

**Using Swagger:**
1. Click POST /api/v1/files/retrieve
2. Paste the file_id from upload
3. Keep default values for AI context
4. Click Execute
5. Download the decrypted file

**Using curl:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/retrieve" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "YOUR-FILE-ID",
    "login_hour": 12,
    "trusted_device": 1,
    "country": "Unknown",
    "ip_reputation": 0.8,
    "vpn_detected": 0,
    "failed_login_attempts": 0,
    "browser": "Chrome",
    "access_frequency": 1,
    "file_sensitivity": "High",
    "refresh_frequency": 0
  }' \
  -o downloaded_file.txt
```

### 4. View Audit Log

**Using Swagger:**
1. Click GET /api/v1/audit
2. Click Execute
3. See all access events

**Using curl:**
```bash
curl "http://127.0.0.1:8000/api/v1/audit?limit=20" \
  -H "Authorization: Bearer dev-token"
```

## Running Tests

### Basic Test Run

```bash
make test
```

### Detailed Test Output

```bash
make test-verbose
```

### With Coverage Report

```bash
make coverage
```

## Development Workflow

### Code Quality Checks

```bash
make lint       # Check for style issues
make format     # Auto-format code
make check      # Lint + test + coverage
```

### Clean Up

```bash
make clean      # Remove generated files and caches
```

## Check Audit Logs

View recent events:
```bash
make logs
```

Events stored in: `data/metadata/audit/audit_YYYY-MM-DD.jsonl`

## Troubleshooting

### "Module not found" errors

```bash
# Verify virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port 8000 already in use

Change port in .env:
```env
PORT=8001
```

Then run:
```bash
python3 -m uvicorn app.main:app --reload --port 8001
```

### Data directory permissions

```bash
mkdir -p data/storage data/metadata
chmod 755 data/
```

### Want to reset everything

```bash
make clean
rm -rf data/
make setup
make run
```

## Common Tasks

### Generate a large test file

```bash
dd if=/dev/urandom of=testfile.bin bs=1M count=10  # 10MB file
```

### Monitor audit events in real-time

```bash
tail -f data/metadata/audit/audit_*.jsonl
```

### Test with different settings

Edit `.env`:
```env
LOG_LEVEL=DEBUG  # More detailed logging
CRYPTO_TIME_WINDOW=10  # Longer validity window
```

## Next Steps

1. **Explore the API**: http://127.0.0.1:8000/docs
2. **Read the documentation**: See README.md
3. **Run the tests**: `make test`
4. **Check the logs**: `make logs`
5. **Build the frontend**: React/Vite (coming next)

## Architecture Overview

```
┌─────────────────────────────────────────┐
│     API Layer (FastAPI Routes)          │
│  (/health, /api/v1/files/*, /audit)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Service Layer (Business Logic)        │
│  (FileService, AuditService)            │
└────────────────┬────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
┌────────▼──────┐  ┌─────▼──────────┐
│ Adapters      │  │ Integrations   │
│ (Wrappers)    │  │ (AI, Storage)  │
├───────────────┤  ├────────────────┤
│ CryptoAdapter │  │ AIAdapter      │
│ AIAdapter     │  │ ObjectStore    │
└───────────────┘  └────────────────┘
         │                │
    ┌────▼────────────────▼──┐
    │ Implementations        │
    ├───────────────────────┤
    │ crypto_engine/        │ ← Actual crypto
    │ major_project/        │ ← AI risk engine
    │ LocalObjectStore      │ ← File storage
    │ LocalMetadataStore    │ ← Metadata DB
    └───────────────────────┘
```

## Support Files

- **API Docs**: Visit http://127.0.0.1:8000/docs
- **Configuration**: See `.env.example`
- **Logs**: `data/metadata/audit/`
- **Tests**: Run `make test`
- **Full Docs**: See `README.md`

---

**Ready to go!** 🚀

Start with `make setup && make run` and then visit http://127.0.0.1:8000/docs
