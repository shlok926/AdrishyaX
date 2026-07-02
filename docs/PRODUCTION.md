# StegoForge v4.0 Enterprise Edition - Production Deployment Guide

## Overview
StegoForge is a production-ready steganography platform using enterprise-grade cryptography (AES-256 + Argon2id + ECDH) and LSB-based image embedding.

## System Requirements

### Minimum Specifications
- **CPU**: 2 cores, 2GHz+
- **RAM**: 4GB
- **Disk**: 10GB (logs + temp files)
- **Python**: 3.9+
- **Network**: 10 Mbps+

### Recommended Production Setup
- **CPU**: 4+ cores
- **RAM**: 8-16GB
- **Disk**: SSD with 20GB+
- **OS**: Ubuntu 20.04 LTS or CentOS 8+
- **Container**: Docker + Kubernetes (optional)

## Installation

### 1. Clone Repository
```bash
git clone <repository-url> stegoforge
cd stegoforge
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "from src.crypto import derive_key; print('Crypto module OK')"
python -c "from src.stego import embed_bytes_into_image; print('Stego module OK')"
```

## Configuration

### Environment Variables
```bash
# Application
export FLASK_ENV=production
export FLASK_APP=app.py
export SECRET_KEY=$(openssl rand -hex 32)

# Security
export CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
export SESSION_COOKIE_SECURE=true
export SESSION_COOKIE_HTTPONLY=true

# Performance
export WORKERS=4
export THREADS_PER_WORKER=2
export MAX_REQUESTS_PER_WORKER=1000
```

### Security Configuration
1. **TLS/SSL Certificate**
   ```bash
   # Using Let's Encrypt
   sudo certbot certonly --standalone -d yourdomain.com
   ```

2. **CORS Policy** - Configure allowed origins in `config.py`

3. **Rate Limiting** - Set `RATE_LIMIT_PER_MINUTE` in `config.py`

4. **Input Validation** - All inputs sanitized (password, message, image)

## Running the Application

### Development Mode
```bash
flask run --host 127.0.0.1 --port 5000
```

### Production Mode with Gunicorn
```bash
pip install gunicorn
gunicorn --workers 4 --threads 2 --worker-class gthread \
  --bind 0.0.0.0:8000 --timeout 60 app:app
```

### Docker Deployment
```bash
# Build image
docker build -t stegoforge:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  --restart always \
  stegoforge:latest
```

### Docker Compose (with Nginx)
```bash
docker-compose up -d
```

## Monitoring and Logging

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "timestamp": "2024-04-19T12:00:00"
}
```

### Log Files
- **Application Logs**: `stegoforge.log`
- **Log Level**: Set via `FLASK_ENV` (DEBUG in dev, INFO in prod)
- **Log Retention**: 5 files, 10MB each

### Performance Monitoring
```bash
# Monitor resource usage
watch -n 1 'ps aux | grep gunicorn'

# Check logs in real-time
tail -f stegoforge.log
```

## API Endpoints

### Health Check
```
GET /health
Response: 200 OK
{
  "status": "healthy",
  "version": "4.0.0",
  "timestamp": "ISO8601"
}
```

### Embed Content
```
POST /api/v1/encode
Content-Type: multipart/form-data

Parameters:
- image: Binary (PNG/JPEG/BMP)
- password: String (8-256 chars)
- message: String (up to 10000 bytes)
- aes_bits: Integer (128, 192, or 256)
- decoy_password: String (optional)
- decoy_message: String (optional)

Response: 200 OK
- Binary PNG file download
```

### Extract Content
```
POST /api/v1/decode
Content-Type: multipart/form-data

Parameters:
- image: Binary (PNG/BMP)
- password: String

Response: 200 OK
{
  "message": "Decrypted content",
  "timestamp": "ISO8601"
}

Error Response: 403 Forbidden
{
  "error": "Authentication failed. Invalid password."
}
```

### Analyze Robustness
```
POST /api/v1/analyze
Content-Type: multipart/form-data

Parameters:
- image: Binary (PNG/BMP)
- password: String

Response: 200 OK
{
  "jpeg_compression_attack": "Survived" | "Failed",
  "cropping_attack": "Survived" | "Failed",
  "robustness_score": 0-100,
  "timestamp": "ISO8601"
}
```

### Generate Preview
```
POST /api/v1/preview
Content-Type: multipart/form-data

Parameters:
- original: Binary (PNG/BMP)
- encoded: Binary (PNG/BMP)

Response: 200 OK
{
  "visibility_percent": 0-100,
  "invisibility_score": 0-100,
  "changed_pixels": Integer,
  "total_pixels": Integer,
  "heatmap_b64": Base64-encoded PNG,
  "timestamp": "ISO8601"
}
```

## Security Considerations

### Cryptographic Details
- **KDF**: Argon2id (65536 KB, 3 iterations, 4 parallelism)
- **Symmetric**: AES-GCM (256-bit)
- **Asymmetric**: ECDH (P-256/P-384/P-521)
- **Hashing**: SHA-256

### Network Security
- Always use HTTPS/TLS in production
- Implement CORS properly
- Use strong `SECRET_KEY`
- Enable secure cookies

### Input Validation
- Password: 8-256 characters, UTF-8 encoded
- Message: up to 10,000 bytes
- Image: max 50MB, PNG/JPEG/BMP only
- AES bits: 128, 192, or 256

### Rate Limiting
- Default: 30 requests/minute per IP
- Production: 20 requests/minute per IP
- Enforced via decorator on API endpoints

## Troubleshooting

### Issue: "Address already in use"
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Issue: "Out of memory"
```bash
# Reduce worker count
gunicorn --workers 2 app:app
# Increase swap space
sudo dd if=/dev/zero of=/swapfile bs=1G count=2
```

### Issue: "SSL certificate error"
```bash
# Verify certificate
openssl x509 -in /etc/letsencrypt/live/domain/fullchain.pem -text -noout
# Renew certificate
sudo certbot renew
```

### Issue: "Image not found during extraction"
- Ensure image is PNG or BMP format
- Verify image contains valid steganographic payload
- Check file integrity (not corrupted)
- Try re-encoding

## Performance Tuning

### For High Throughput
```bash
gunicorn --workers $(nproc) --threads 4 \
  --worker-class gthread --max-requests 1000 \
  --max-requests-jitter 100 app:app
```

### For Low Latency
```bash
gunicorn --workers 4 --threads 2 \
  --preload-app --worker-class gthread app:app
```

### Database Caching (if extended)
- Implement Redis for session storage
- Cache decoded images temporarily
- Use CDN for static assets

## Backup and Recovery

### Daily Backup
```bash
# Backup logs
tar -czf stegoforge_logs_$(date +%Y%m%d).tar.gz stegoforge.log

# Backup config
tar -czf stegoforge_config_$(date +%Y%m%d).tar.gz config.py requirements.txt
```

### Disaster Recovery
```bash
# Fresh deployment
git clone <repo> stegoforge_backup
cd stegoforge_backup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run  # Test
```

## Compliance and Auditing

### Logging Audit Trail
All operations logged with:
- Timestamp (UTC)
- Operation type (encode/decode/analyze)
- Source IP
- Success/failure status
- Error messages

### Data Retention
- Logs retained: 50MB (5 files × 10MB)
- Temporary files cleaned automatically
- No payload data stored on server

## Support and Maintenance

### Regular Maintenance
- Monthly security updates
- Quarterly dependency upgrades
- Annual security audit
- Log rotation and cleanup

### Contact and Escalation
For production issues:
1. Check logs: `tail -f stegoforge.log`
2. Health check: `curl /health`
3. Review security logs
4. Contact platform administrator

## Version History

### v4.0.0 (Current)
- Enterprise security hardening
- API versioning (v1)
- Rate limiting and CORS
- Comprehensive logging
- Production-ready Docker setup

### v3.x
- Initial advanced features
- Heatmap visualization
- Attack simulation

### v2.x
- Decoy password protocol
- Multi-AES selection

### v1.x
- Basic LSB embedding
- AES-256 encryption
