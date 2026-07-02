# StegoForge v4 - Complete API Reference

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Request/Response Format](#requestresponse-format)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [Endpoints](#endpoints)
7. [Code Examples](#code-examples)

---

## Overview

StegoForge v4 is a comprehensive steganography platform providing secure message embedding, extraction, and advanced cryptographic features. The API is RESTful and returns JSON responses.

**Base URL:** `http://127.0.0.1:5000/api/v1/`

**Version:** 4.0.0  
**Protocol:** HTTP/HTTPS  
**Response Format:** JSON

---

## Authentication

StegoForge uses **password-based authentication** integrated into each operation:

- **No API tokens required** - Authentication happens per-operation
- **Password length:** 8-256 characters
- **Encryption:** AES-128/192/256 (configurable)
- **Default:** AES-256

All sensitive operations require a password parameter.

---

## Request/Response Format

### Request Headers
```
Content-Type: multipart/form-data (for file uploads)
Content-Type: application/json (for JSON payloads)
X-Client-ID: Optional client identifier (for session tracking)
```

### Response Format
```json
{
  "success": true,
  "data": { },
  "timestamp": "2024-04-28T10:30:00Z",
  "error": null,
  "error_code": null
}
```

### Error Response
```json
{
  "success": false,
  "error": "Detailed error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-04-28T10:30:00Z",
  "details": {
    "field": "relevant details"
  }
}
```

---

## Rate Limiting

### Limits by Endpoint

| Endpoint | Limit | Period | Description |
|----------|-------|--------|-------------|
| `/api/v1/encode` | 10 | 60s | Heavy operation |
| `/api/v1/decode` | 20 | 60s | Medium operation |
| `/api/v1/analyze` | 10 | 60s | Analysis |
| `/api/v1/optimize` | 30 | 60s | Image analysis (new feature) |
| `/api/v1/capacity-check` | 30 | 60s | Light check |
| `/api/v1/video/*` | 3-5 | 60s | Video operations |
| **Global** | 60 | 60s | All endpoints |

### Headers on Rate-Limited Response
```
HTTP/1.1 429 Too Many Requests

{
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "remaining_requests": 0,
  "reset_time": "2024-04-28T10:31:00Z"
}
```

---

## Error Handling

### Common Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `AUTHENTICATION_ERROR` | 403 | Wrong password |
| `INSUFFICIENT_CAPACITY` | 400 | Payload too large |
| `IMAGE_PROCESSING_ERROR` | 400 | Image invalid |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `MESSAGE_EXPIRED` | 403 | TTL expired |
| `SELF_DESTRUCT_ACTIVATED` | 403 | Max attempts exceeded |
| `SERVICE_DEGRADED` | 503 | Service unavailable |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

## Endpoints

### 1. Health Check

#### GET `/api/v1/health`
Check service health and get performance metrics.

**Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "timestamp": "2024-04-28T10:30:00Z",
  "metrics": {
    "performance": { },
    "memory": {
      "cpu_percent": 5.2,
      "memory_mb": 150.5,
      "memory_percent": 2.1
    },
    "circuit_breakers": { }
  }
}
```

---

### 2. Image Encoding

#### POST `/api/v1/encode`
Embed secret message into carrier image.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Carrier image (PNG, JPEG, BMP) |
| `message` | String | Yes | Secret message (max 10,000 chars) |
| `password` | String | Yes | Encryption password (8-256 chars) |
| `aes_bits` | Integer | No | AES key size: 128, 192, 256 (default: 256) |
| `double_encrypt` | Boolean | No | Enable double encryption (default: false) |
| `remove_exif` | Boolean | No | Remove EXIF data (default: false) |
| `self_destruct` | Boolean | No | Enable message expiry (default: false) |
| `ttl_seconds` | Integer | No | Time to live in seconds (default: 3600) |
| `max_attempts` | Integer | No | Max failed decode attempts (default: 0=unlimited) |
| `decoy_password` | String | No | Decoy password for security |
| `decoy_message` | String | No | Decoy message if wrong password used |

**Response:**
```json
{
  "success": true,
  "status": "encoded",
  "payload_bytes": 2048,
  "timestamp": "2024-04-28T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Secret message" \
  -F "password=MyPassword123" \
  -F "aes_bits=256" \
  -F "double_encrypt=true" \
  --output stego_image.png
```

---

### 3. Image Decoding

#### POST `/api/v1/decode`
Extract and decrypt message from stego image.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Stego image with embedded message |
| `password` | String | Yes | Decryption password |

**Response:**
```json
{
  "success": true,
  "message": "Extracted secret message",
  "timestamp": "2024-04-28T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/decode \
  -F "image=@stego_image.png" \
  -F "password=MyPassword123"
```

---

### 4. Batch Encoding

#### POST `/api/v1/encode-batch`
Embed multiple files into single image with compression.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Carrier image |
| `files` | Files | Yes | Multiple files to embed |
| `password` | String | Yes | Encryption password |
| `aes_bits` | Integer | No | AES key size (default: 256) |
| `compression_method` | String | No | 'zip' or '7z' (default: 'zip') |
| `double_encrypt` | Boolean | No | Enable double encryption |
| `remove_exif` | Boolean | No | Remove EXIF data |
| `self_destruct` | Boolean | No | Enable expiry |
| `ttl_seconds` | Integer | No | Expiry time (default: 3600) |
| `max_attempts` | Integer | No | Max decode attempts |

**Response:**
```json
{
  "success": true,
  "status": "batch_encoded",
  "files_embedded": 3,
  "compressed_size": 1024000,
  "original_size": 5000000,
  "compression_ratio": 81.5
}
```

---

### 5. Batch Decoding

#### POST `/api/v1/decode-batch`
Extract multiple files from stego image.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Batch-encoded stego image |
| `password` | String | Yes | Decryption password |

**Response:**
```json
{
  "success": true,
  "files_extracted": 3,
  "manifest": {
    "total_size": 5000000,
    "compressed_size": 1024000,
    "files": [
      {"name": "file1.txt", "size": 1000},
      {"name": "file2.pdf", "size": 2000}
    ]
  }
}
```

Returns ZIP file with extracted files and manifest.

---

### 6. Split Encoding

#### POST `/api/v1/encode-split`
Distribute payload across multiple carrier images.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `images` | Files | Yes | 1-20 carrier images |
| `message` | String | No | Secret message OR files |
| `files` | Files | No | Files to embed (if no message) |
| `password` | String | Yes | Encryption password |
| `aes_bits` | Integer | No | AES key size (default: 256) |
| `compression_method` | String | No | 'zip' or '7z' (default: 'zip') |

**Response:**
```json
{
  "success": true,
  "segments": 4,
  "total_images": 4,
  "payload_bytes": 50000
}
```

Returns ZIP file with all encoded images.

---

### 7. Split Decoding

#### POST `/api/v1/decode-split`
Decode payload split across multiple images.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `images` | Files | Yes | All segment images |
| `password` | String | Yes | Decryption password |

**Response:**
```json
{
  "success": true,
  "segments_recovered": 4,
  "payload_bytes": 50000
}
```

Returns ZIP file with extracted content.

---

### 8. Capacity Check

#### POST `/api/v1/capacity-check`
Check carrier image capacity for payload.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Carrier image |
| `payload_size` | Integer | No | Expected payload size |

**Response:**
```json
{
  "success": true,
  "capacity_bytes": 102400,
  "payload_size": 2048,
  "utilization_percent": 2.0,
  "can_fit": true
}
```

---

### 9. Capacity Multiple Images

#### POST `/api/v1/capacity-check`
Check capacity across multiple images.

**JSON Body:**
```json
{
  "carriers": [[800, 600], [1024, 768]],
  "payload_size": 50000
}
```

**Response:**
```json
{
  "status": "success",
  "available_bytes": 500000,
  "required_bytes": 50000,
  "percentage": 10.0,
  "fit": true,
  "recommendations": []
}
```

---

### 10. Attack Simulation

#### POST `/api/v1/analyze`
Test payload robustness against attacks.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Stego image |
| `password` | String | Yes | For verification |

**Tests:**
- JPEG compression (quality: 85)
- Image cropping (10% borders removed)

**Response:**
```json
{
  "success": true,
  "jpeg_compression_attack": "Survived",
  "cropping_attack": "Survived",
  "robustness_score": 100,
  "timestamp": "2024-04-28T10:30:00Z"
}
```

---

### 11. Steganalysis Detection

#### POST `/api/v1/steganalysis`
Detect if image contains hidden content using ML.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Image to analyze |

**Response:**
```json
{
  "success": true,
  "stego_probability": 0.92,
  "confidence": "High",
  "analysis": {
    "lsb_bias": -0.05,
    "chi_square": 125.4,
    "entropy": 7.98
  }
}
```

---

### 12. Image Optimization (NEW)

#### POST `/api/v1/optimize`
Analyze and score carrier image for steganography suitability.

**Description:**
Get AI-powered recommendations for image quality, embedding capacity, and optimal configuration. This endpoint analyzes multiple aspects of the carrier image to provide a suitability score (0-100) and actionable recommendations.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Carrier image to analyze (PNG, JPEG, BMP, GIF, WEBP) |

**Response:**
```json
{
  "success": true,
  "filename": "carrier.png",
  "overall_score": 92,
  "score_breakdown": {
    "capacity_score": 95,
    "quality_score": 89,
    "suitability_score": 92
  },
  "metrics": {
    "dimensions": "1920x1080",
    "width": 1920,
    "height": 1080,
    "aspect_ratio": 1.78,
    "entropy": 7.45,
    "format": "PNG",
    "file_size": 2048000,
    "file_size_mb": 1.95,
    "color_depth": 24,
    "is_compressed": false
  },
  "capacity_analysis": {
    "max_payload_bytes": 622080,
    "max_payload_mb": 0.593,
    "optimal": true
  },
  "recommendations": [
    "Excellent capacity - can hide 600KB of encrypted data",
    "High-entropy image provides good camouflage",
    "PNG format preserves all embedded data (lossless)",
    "Optimal for text messages and files"
  ],
  "suggestions": [
    "Use this image for secure file embedding",
    "Consider double encryption for sensitive data",
    "Enable self-destruct for time-limited messages"
  ],
  "risk_assessment": {
    "compression_risk": "Low",
    "entropy_risk": "Low",
    "visibility_risk": "Low"
  },
  "timestamp": "2024-04-28T10:30:00Z"
}
```

**Score Interpretation:**
- **90-100:** Excellent - Highly recommended carrier
- **75-89:** Good - Suitable for most use cases  
- **60-74:** Fair - Acceptable but with limitations
- **Below 60:** Poor - Not recommended

**Use Cases:**
- Pre-validation before encoding to save processing time
- Selecting best image from multiple candidates
- Optimizing encoding settings per image characteristics
- Educational analysis of image properties for steganography

**Example:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/optimize \
  -F "image=@carrier.png" \
  | python -m json.tool
```

---

### 13. Visualization Heatmap

#### POST `/api/v1/visualization/heatmap`
Generate payload distribution heatmap.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Carrier image |
| `message` | String | Yes | Message to visualize |

**Response:**
```json
{
  "success": true,
  "image": {"width": 800, "height": 600},
  "utilization_percent": 15.5,
  "heatmap": [
    {"x": 0, "y": 0, "intensity": 100},
    {"x": 0, "y": 1, "intensity": 85}
  ],
  "grid_size": 10
}
```

---

### 14. ECDH Key Exchange

#### GET `/api/v1/ecdh/curves`
List available ECDH curves.

**Response:**
```json
{
  "success": true,
  "available_curves": ["p256", "p384", "p521"],
  "default_curve": "p256",
  "timestamp": "2024-04-28T10:30:00Z"
}
```

#### POST `/api/v1/ecdh/generate`
Generate ECDH keypair.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curve` | String | No | Elliptic curve (default: p256) |

**Response:**
```json
{
  "success": true,
  "curve": "p256",
  "private_key": "base64_encoded_private_key",
  "public_key": "base64_encoded_public_key",
  "curve_info": {
    "bits": 256,
    "name": "secp256r1"
  }
}
```

#### POST `/api/v1/ecdh/exchange`
Compute shared secret.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `curve` | String | Yes | Elliptic curve |
| `private_key` | String | Yes | Base64 encoded private key |
| `peer_public_key` | String | Yes | Base64 encoded peer public key |

**Response:**
```json
{
  "success": true,
  "curve": "p256",
  "shared_secret": "base64_encoded_secret",
  "secret_length": 32,
  "timestamp": "2024-04-28T10:30:00Z"
}
```

---

### 15. Video Embedding

#### POST `/api/v1/video/embed`
Embed message into video frames.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video` | File | Yes | Video file (MP4, AVI, MOV) |
| `message` | String | No | Message to embed OR |
| `payload` | File | No | File to embed |
| `password` | String | Yes | Encryption password |
| `frames` | Integer | No | Number of frames (default: 10) |

**Response:**
```json
{
  "success": true,
  "frames_used": 10,
  "payload_bytes": 2048,
  "video_duration": 120,
  "timestamp": "2024-04-28T10:30:00Z"
}
```

---

### 15. Session History

#### GET `/api/v1/session/history`
Retrieve client session history.

**Headers:**
```
X-Client-ID: client-uuid-here
```

**Response:**
```json
{
  "success": true,
  "client_id": "uuid",
  "history": [
    {
      "timestamp": "2024-04-28T10:00:00Z",
      "type": "encode",
      "status": "success",
      "payload_size": 2048
    }
  ],
  "total_operations": 5
}
```

#### POST `/api/v1/session/history`
Record operation in session.

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | String | Yes | 'encode', 'decode', 'analyze' |
| `status` | String | Yes | 'pending', 'success', 'failed' |
| `carrier_size` | Integer | No | Carrier size in bytes |
| `payload_size` | Integer | No | Payload size in bytes |

---

## Code Examples

### Python Example - Basic Encoding
```python
import requests

url = "http://127.0.0.1:5000/api/v1/encode"

files = {
    'image': open('carrier.png', 'rb'),
}

data = {
    'message': 'Secret message',
    'password': 'MyPassword123',
    'aes_bits': 256,
    'double_encrypt': 'true'
}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    with open('stego_image.png', 'wb') as f:
        f.write(response.content)
    print("Encoding successful!")
else:
    print(f"Error: {response.json()}")
```

### Python Example - Batch Decoding
```python
import requests
import zipfile

url = "http://127.0.0.1:5000/api/v1/decode-batch"

files = {
    'image': open('stego_image.png', 'rb'),
}

data = {
    'password': 'MyPassword123'
}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    with open('extracted.zip', 'wb') as f:
        f.write(response.content)
    
    # Extract files
    with zipfile.ZipFile('extracted.zip') as z:
        z.extractall('extracted_files/')
    print("Decoding successful!")
else:
    print(f"Error: {response.json()}")
```

### JavaScript/Fetch Example
```javascript
async function encodeMessage() {
    const formData = new FormData();
    formData.append('image', document.getElementById('imageInput').files[0]);
    formData.append('message', 'Secret message');
    formData.append('password', 'MyPassword123');
    formData.append('aes_bits', '256');
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/encode', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('Error:', error.error);
            return;
        }
        
        // Download stego image
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'stego_image.png';
        a.click();
    } catch (error) {
        console.error('Request failed:', error);
    }
}
```

### cURL Examples

**Encode:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Secret message" \
  -F "password=MyPassword123" \
  -F "aes_bits=256" \
  --output stego_image.png
```

**Decode:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/decode \
  -F "image=@stego_image.png" \
  -F "password=MyPassword123"
```

**Capacity Check:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/capacity-check \
  -F "image=@carrier.png"
```

**Image Optimization:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/optimize \
  -F "image=@carrier.png" | python -m json.tool
```

**Health Check:**
```bash
curl http://127.0.0.1:5000/api/v1/health | python -m json.tool
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 403 | Forbidden (authentication failed, expired, etc.) |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Service unavailable |

---

## Best Practices

1. **Always validate image format** - Use capacity-check before encoding
2. **Use strong passwords** - Minimum 8 characters, mix of characters
3. **Enable double encryption** - For sensitive data
4. **Use rate limiting** - Respect per-endpoint limits
5. **Handle errors gracefully** - Check error_code for specific issues
6. **Cache health checks** - Don't check health on every request
7. **Implement retry logic** - For failed requests (exponential backoff)
8. **Monitor usage** - Track session history for performance

---

**API Documentation Version:** 4.0.0  
**Last Updated:** 2024  
**Status:** Production Ready
