# StegoForge Platform v4.0 Enterprise Edition

**Advanced Enterprise Steganography Suite with Military-Grade Cryptography**

## Overview

StegoForge is a production-ready platform for secure data hiding using LSB steganography combined with enterprise-grade cryptography. Hide sensitive information within digital media with plausible deniability through decoy passwords.

## Core Features

### Cryptographic Security
- **AES-GCM** encryption (128/192/256-bit configurable)
- **Argon2id** key derivation (RFC 9106 compliant)
- **ECDH** key exchange (P-256/P-384/P-521)
- **SHA-256** fingerprinting and hashing

### Steganography
- **LSB Embedding** in RGB channels
- **Capacity Calculation** for optimal payload sizing
- **EXIF Scrubbing** to remove metadata
- **Multiple Carrier Formats** (PNG, JPEG, BMP)

### Advanced Features
- **Decoy Password Protocol** for plausible deniability
- **Stealth Heatmap Visualization** showing pixel-level modifications
- **Attack Simulation** testing JPEG compression and cropping resilience
- **Bit-Level Inspector** for forensic analysis
- **Operation History** with timestamps and status tracking

### Enterprise Features
- **API v1 Versioning** for backward compatibility
- **Rate Limiting** (30 req/min per client)
- **Security Headers** (CORS, X-Frame-Options, HSTS)
- **Comprehensive Logging** with audit trails
- **Health Check Endpoint** for monitoring
- **Input Validation & Sanitization** on all parameters

## Installation

### Quick Start (Development)
```bash
# Clone and setup
git clone <repository> stegoforge
cd stegoforge
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
# Open http://127.0.0.1:5000
```

### Production Deployment

See [PRODUCTION.md](PRODUCTION.md) for comprehensive deployment guide.

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --workers 4 --threads 2 --worker-class gthread \
  --bind 0.0.0.0:8000 --timeout 60 app:app
```

### Docker
```bash
docker build -t stegoforge .
docker run -p 8000:8000 stegoforge
```

## Usage

### Basic Encoding (Hide Content)
1. Open http://localhost:5000
2. **Embed Content** panel:
   - Upload carrier image (PNG/JPEG/BMP)
   - Enter secret message
   - Set encryption password (8+ characters)
   - Click **Embed** → Downloads stego image

### Basic Decoding (Recover Content)
1. **Extract Content** panel:
   - Upload stego image
   - Enter decryption password
   - Click **Extract** → Reveals message

### Advanced Operations

**Decoy Protocol**
- Set alternate password and message
- Encrypted independently with random salt
- Wrong password reveals decoy message instead
- Provides plausible deniability

**Preview Heatmap**
- Visualize pixel changes before encoding
- Shows invisibility score percentage
- Red pixels = modified, Green = unchanged

**Analyze Robustness**
- Test payload survival against attacks
- JPEG compression (85% quality)
- Image cropping (10% from edges)
- Robustness score (0-100%)

**Bit Inspector**
- Click pixels to view exact RGB values
- Inspect LSB bits where data hidden
- Forensic-level pixel analysis

## API Reference

All endpoints return JSON and are rate-limited to 30 req/min.

### Health Check
```bash
curl http://localhost:5000/health
```
Returns: `{"status":"healthy","version":"4.0.0","timestamp":"..."}`

### Encode (Embed)
```bash
curl -X POST http://localhost:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "password=MySecurePass123" \
  -F "message=Secret data" \
  -F "aes_bits=256" > stego.png
```

### Decode (Extract)
```bash
curl -X POST http://localhost:5000/api/v1/decode \
  -F "image=@stego.png" \
  -F "password=MySecurePass123"
```
Returns: `{"message":"Secret data","timestamp":"..."}`

### Analyze (Robustness)
```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "image=@stego.png" \
  -F "password=MySecurePass123"
```
Returns: Attack test results and robustness score

### Preview (Heatmap)
```bash
curl -X POST http://localhost:5000/api/v1/preview \
  -F "original=@carrier.png" \
  -F "encoded=@stego.png" > heatmap_response.json
```

## Security

### Cryptographic Specifications
- **KDF**: Argon2id with 65536 KB memory, 3 iterations, 4 parallelism
- **Symmetric**: AES-256-GCM with 96-bit IV, 128-bit auth tag
- **Key Exchange**: ECDH with SHA-256 fingerprinting
- **Randomization**: Cryptographically secure OS-level RNG

### Threat Mitigation
| Threat | Mitigation |
|--------|-----------|
| Brute Force | Argon2id KDF with high memory/time cost |
| Timing Attacks | Constant-time AEAD verification |
| Rainbow Tables | Random 128-bit salt per encryption |
| Visual Analysis | LSB embedding below human perception |
| Metadata Leaks | EXIF scrubbing option |
| Deniability | Decoy password protocol |

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | Flask | 2.3.2 |
| Cryptography | cryptography | 41.0.3 |
| KDF | argon2-cffi | 23.1.0 |
| Image Processing | Pillow | 10.0.0 |
| CORS | flask-cors | 4.0.0 |

## Documentation

- [PRODUCTION.md](PRODUCTION.md) - Complete production deployment guide
- [config.py](config.py) - Configuration and environment settings

## System Requirements

- Python 3.9+
- 4GB RAM (8GB recommended)
- 10GB disk space
- HTTPS/TLS in production

---

**StegoForge v4.0** | Enterprise Steganography Platform | Production Ready
