# TDEM - Temporal Data Encryption Management

A secure, vault-based data encryption and management system with temporal access control and AI-driven risk assessment.

## Project Status

✅ **Crypto Engine**: Integrated and working
✅ **AI Risk Engine**: Integrated and working  
✅ **Backend (FastAPI)**: Implemented with complete workflows
✅ **Local Storage**: Full persistence without AWS
⏳ **Frontend**: React/TypeScript application (next phase)
⏳ **AWS Integration**: Placeholder adapters ready (not yet connected)

## Features

### Core Capabilities

- **Temporal Encryption**: Time-window-based encryption with automatic expiry
- **Chunk-Based Processing**: File-level encryption with per-chunk key derivation
- **Identity Fragments**: PBKDF2-based user identity verification
- **Temporal Fragments**: HMAC-based time window validation
- **XOR Fragmentation**: Key reconstruction through XOR operations
- **AES-256-GCM**: Strong authenticated encryption
- **Integrity Verification**: SHA-256 based integrity checks
- **Key Refresh**: Cryptographic key lifecycle management

### Security Features

- **Ownership Enforcement**: Users can only access their own files
- **AI-Driven Risk Assessment**: ML-based anomaly detection for access decisions
- **Audit Logging**: Complete event trail for security incidents
- **Expiry Validation**: Server-side authoritative expiry checks
- **No Secret Exposure**: Crypto material never exposed in API responses

### Backend APIs

```
GET    /health                      # Health check
POST   /api/v1/files/ingest         # Upload & encrypt file
POST   /api/v1/files/retrieve       # Retrieve & decrypt file
POST   /api/v1/files/{id}/refresh   # Refresh encryption
GET    /api/v1/files                # List user's files
GET    /api/v1/files/{id}           # Get file details
DELETE /api/v1/files/{id}           # Delete file
GET    /api/v1/audit                # Get audit log
GET    /api/v1/metrics              # Get performance metrics
```

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. **Clone repository**
   ```bash
   cd Cloud-TDEM
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   ```

5. **Run backend**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

Backend will be available at: `http://127.0.0.1:8000`
Swagger docs: `http://127.0.0.1:8000/docs`

## Usage

### Development Authentication

In development mode, authentication is automatically provided:
- User ID: `dev_user_001`
- Authorization: Pass any value in `Authorization` header

Example:
```bash
curl -H "Authorization: Bearer dev-token" http://127.0.0.1:8000/health
```

### Upload a File

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/ingest?expiry_minutes=60" \
  -H "Authorization: Bearer dev-token" \
  -F "file=@myfile.txt"
```

### Retrieve a File

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/files/retrieve" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "your-file-id",
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
  }'
```

### List Files

```bash
curl "http://127.0.0.1:8000/api/v1/files" \
  -H "Authorization: Bearer dev-token"
```

### Get Audit Log

```bash
curl "http://127.0.0.1:8000/api/v1/audit?limit=50" \
  -H "Authorization: Bearer dev-token"
```

## Testing

### Run Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

- Storage layer (object and metadata)
- Service layer workflows
- API endpoints
- Audit logging
- Error handling

## Project Structure

```
Cloud-TDEM/
├── app/
│   ├── core/                 # Configuration, logging, security
│   ├── api/                  # FastAPI routes and schemas
│   │   ├── routes/
│   │   └── schemas/
│   ├── services/             # Business logic layer
│   ├── integrations/         # Adapters for crypto, AI, storage
│   │   └── aws/              # AWS placeholders (not connected)
│   └── main.py               # FastAPI application
│
├── crypto_engine/            # TDEM cryptographic implementation
│   ├── service.py            # Main encrypt/decrypt/refresh
│   ├── file_service.py       # File-level operations
│   ├── integrity.py          # Hash verification
│   ├── expiry.py             # Temporal validation
│   └── ...
│
├── major_project/            # AI Risk Engine
│   ├── risk_engine.py        # ML-based risk scoring
│   ├── feature_extractor.py  # Request feature extraction
│   ├── service.py            # AI evaluation service
│   └── model.pkl             # Pre-trained model
│
├── tests/                    # Test suite
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Data Flow

### Upload (Ingest)

```
File Upload
    ↓
Validate User (Auth)
    ↓
Validate Expiry Duration
    ↓
Call Crypto Engine (encrypt_data)
    ↓
Generate Fid (Identity Fragment)
Generate Ftime (Temporal Fragment)
Generate Km (Master Key)
Generate Fdb (Km XOR Fid XOR Ftime)
    ↓
AES-256-GCM Encryption
    ↓
Store Encrypted Object (Local Filesystem)
    ↓
Store Metadata (Local JSON)
    ↓
Create Audit Event
    ↓
Return Safe File Metadata
```

### Retrieve

```
User Request with Risk Context
    ↓
Authenticate User
    ↓
Check File Ownership
    ↓
Load Metadata
    ↓
Check Expiry (Server Authoritative)
    ↓
Call AI Risk Engine (evaluate_request)
    ↓
AI Decision: ALLOW / REQUIRE_MFA / DENY
    ↓
If DENY → Stop
    ↓
Retrieve Encrypted Object
    ↓
Call Crypto Engine (retrieve_data)
    ↓
Verify Temporal Window
Regenerate Fid
Regenerate Ftime
Reconstruct Km
    ↓
AES-256-GCM Decryption
    ↓
Verify Integrity (SHA-256)
    ↓
Update Access Time
    ↓
Create Audit Event
    ↓
Return File Content
```

## Local Storage Structure

```
data/
├── storage/          # Encrypted objects
│   └── {file_id}.enc
└── metadata/         # File metadata
    ├── {file_id}.json
    ├── index_{user_id}.json
    └── audit/        # Audit logs
        └── audit_YYYY-MM-DD.jsonl
```

## Security Considerations

### What's Protected

✅ File content encrypted with AES-256-GCM
✅ User identity verified via Fid
✅ Temporal validity enforced via Ftime
✅ Key material never exposed in API
✅ Audit trail of all access
✅ AI-based anomaly detection
✅ Ownership enforced at backend

### What's NOT Protected (Local Dev)

- Development mode uses default credentials
- No TLS/HTTPS in development
- Environment variables in .env file
- Local filesystem not encrypted

### For Production

1. Enable JWT-based authentication
2. Configure AWS Cognito integration
3. Enable TLS/HTTPS
4. Use AWS Secrets Manager for keys
5. Enable CloudWatch logging
6. Deploy to AWS with proper IAM roles
7. Use S3 for encrypted object storage
8. Use DynamoDB for metadata
9. Configure VPC and security groups
10. Enable audit logging to CloudTrail

## AWS Integration (Future)

Current implementation uses local storage placeholders:

- `LocalObjectStore` → Future: S3
- `LocalMetadataStore` → Future: DynamoDB
- Environment-based Auth → Future: Cognito
- Local JSON Audit → Future: CloudWatch
- Request Metrics → Future: CloudWatch Metrics
- Events → Future: EventBridge

To enable AWS integration in the future:

1. Update `app/integrations/aws/` implementations
2. Configure AWS credentials
3. Create S3 bucket and DynamoDB table
4. Update `app/integrations/storage_adapter.py` factory functions
5. Deploy backend to AWS Lambda or ECS
6. Configure API Gateway
7. Enable VPC endpoints for S3/DynamoDB

## Configuration

### Environment Variables

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# Storage
STORAGE_PATH=./data/storage
METADATA_PATH=./data/metadata

# Crypto
CRYPTO_TIME_WINDOW=5
CRYPTO_KSEED=your-32-byte-seed-key

# Auth (Development)
DEVELOPMENT_USER_ID=dev_user_001
DEVELOPMENT_USER_NAME=Developer

# Auth (Production - JWT)
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Development Workflow

1. **Run backend**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Test with Swagger**
   Visit: `http://127.0.0.1:8000/docs`

3. **Run tests**
   ```bash
   python -m pytest tests/ -v
   ```

4. **Check audit logs**
   Files in: `data/metadata/audit/`

## Troubleshooting

### Crypto Engine Import Error

Ensure crypto_engine files are in repository:
```bash
ls crypto_engine/*.py
```

If missing, restore from git:
```bash
git show COMMIT_SHA:crypto_engine/service.py > crypto_engine/service.py
```

### AI Engine Not Available

Ensure major_project files exist:
```bash
ls major_project/*.py
```

### Permission Denied on Storage

Ensure data directory is writable:
```bash
mkdir -p data/storage data/metadata
chmod 755 data/
```

## Logging

Logs are output to stdout with the following format:
```
2026-09-01 10:30:45,123 - tdem.module_name - INFO - Log message
```

Change log level in `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Performance Notes

- **Crypto Time Window**: Set to 5 seconds for testing (set higher in production)
- **File Size**: Tested with files up to 10MB
- **Concurrent Users**: No specific optimization for concurrent access yet
- **Audit Log**: Keep-all strategy (archive old logs manually)

## Known Limitations

1. **No Real AWS Integration**: AWS adapters are placeholders only
2. **Single Time Window**: Crypto uses fixed window (can be made configurable)
3. **No Database Optimization**: Metadata stored as JSON files
4. **No Caching**: Every request does full crypto operations
5. **Development Auth Only**: Production JWT auth not yet tested

## Next Steps (Frontend)

1. Create React/Vite application
2. Implement vault dashboard with concentric rings
3. Build file upload/retrieve UI
4. Add risk assessment visualization
5. Implement audit log viewer
6. Create security dashboard

## Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Test locally before committing
5. Use feature branches

## License

[To be defined]

## Support

For issues or questions:
1. Check logs in data/metadata/audit/
2. Review Swagger documentation: /docs
3. Check test files for usage examples

---

**Version**: 0.1.0  
**Last Updated**: 2026-09-01  
**Status**: Functional (Local Development)
