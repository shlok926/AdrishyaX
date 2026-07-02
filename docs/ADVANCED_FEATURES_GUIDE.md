# StegoForge v4 - Advanced Features Guide

## Advanced Features for Power Users

This guide covers advanced StegoForge features for experienced users and developers.

---

## Table of Contents
1. [Double Encryption](#double-encryption)
2. [Message Expiry & Self-Destruct](#message-expiry--self-destruct)
3. [Decoy Messages](#decoy-messages)
4. [Split Encoding](#split-encoding)
5. [ECDH Key Exchange](#ecdh-key-exchange)
6. [Video Steganography](#video-steganography)
7. [Steganalysis & Detection](#steganalysis--detection)
8. [Advanced Compression](#advanced-compression)
9. [Multi-Carrier Distribution](#multi-carrier-distribution)

---

## Double Encryption

### What is Double Encryption?

Double encryption applies **two layers of AES encryption** to your message:

```
Plaintext
    ↓
[AES-256 Encrypt with Salt1] → Intermediate Ciphertext
    ↓
[AES-256 Encrypt with Salt2] → Final Ciphertext
    ↓
Embedded in Image
```

### Why Use It?

- **Maximum Security:** Would need to break 2 independent AES-256 encryptions
- **Defense in Depth:** Different salts prevent pattern analysis
- **Quantum Safe:** Even hypothetical quantum computers would struggle
- **Peace of Mind:** Know your data is secured with highest standard

### How to Enable

**Web Interface:**
1. Click "⚡ Advanced Options"
2. Check "☑️ Double Encryption"
3. Password is used for both layers with different salts

**API:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Top secret" \
  -F "password=MyPassword123" \
  -F "double_encrypt=true"
```

**Python:**
```python
data = {
    'message': 'Top secret',
    'password': 'MyPassword123',
    'double_encrypt': 'true',
    'aes_bits': '256'
}
response = requests.post(url, files=files, data=data)
```

### Technical Details

```
Salt1 = random 16 bytes
Salt2 = random 16 bytes
Key1 = derive_key(password, salt1, 256) = 32 bytes
Key2 = derive_key(password, salt2, 256) = 32 bytes

Ciphertext1 = AES-256-GCM(Key1, message)
Ciphertext2 = AES-256-GCM(Key2, Ciphertext1)

Payload = Version | Salt1 | Salt2 | Ciphertext2
```

### Decryption

Decryption happens in **reverse order**:

```
Ciphertext2
    ↓
[AES-256 Decrypt with Salt2] → Ciphertext1
    ↓
[AES-256 Decrypt with Salt1] → Plaintext
```

**Note:** Both salts are stored in the payload, so the system automatically detects and handles double encryption.

---

## Message Expiry & Self-Destruct

### Message Expiry (TTL)

Make messages automatically unreadable after a time period.

#### Use Cases:
- **Time-sensitive operations:** "Meeting at 3pm"
- **Temporary credentials:** Passwords valid for 24 hours
- **Confidential proposals:** Auto-delete after negotiation
- **Sensitive documents:** Delete after review period

#### How It Works:

```
Encode at: 2024-04-28 10:00:00
TTL: 3600 seconds (1 hour)
Expires at: 2024-04-28 11:00:00

After 11:00:00 → Message cannot be decoded (Error: "Message has expired")
```

#### Enable in Web UI:
1. Click "⚡ Advanced Options"
2. Check "☑️ Message Expiry"
3. Set "TTL Seconds": `3600` (1 hour, default)

#### API Example:
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Valid for 1 hour only" \
  -F "password=MyPassword123" \
  -F "self_destruct=true" \
  -F "ttl_seconds=3600"
```

---

### Self-Destruct on Failed Attempts

Protect against brute-force password guessing.

#### How It Works:

```
Max Attempts: 3

Attempt 1 - Wrong Password → Fail (2 remaining)
Attempt 2 - Wrong Password → Fail (1 remaining)
Attempt 3 - Wrong Password → Fail (0 remaining)
Attempt 4 - LOCKED → "Message self-destructed"

(Image is locked permanently)
```

#### Enable in Web UI:
1. Click "⚡ Advanced Options"
2. Check "☑️ Self-Destruct"
3. Set "Max Attempts": `3`

#### API Example:
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Important" \
  -F "password=MyPassword123" \
  -F "max_attempts=3"
```

#### Response on Lock:
```json
{
  "success": false,
  "error": "Authentication failed. Message self-destructed.",
  "error_code": "SELF_DESTRUCT_ACTIVATED"
}
```

---

## Decoy Messages

### Purpose

If someone guesses wrong password, show a decoy message instead of error. They won't know they're wrong!

### Example Scenario:

```
Alice encodes with:
  Real Password: "SecretPassword123"
  Real Message: "Attack plan: March 15"
  Decoy Password: "TryMe123"
  Decoy Message: "Just a cat photo!"

Bob tries password "TryMe123":
  → Decoy message appears: "Just a cat photo!"
  → Bob thinks he's succeeded
  → Bob never suspects there's a real message
```

### Enable in Web UI:
1. Click "⚡ Advanced Options"
2. Check "☑️ Decoy Message"
3. Fill "Decoy Password": Password for wrong attempt
4. Fill "Decoy Message": Message to show on wrong password

### API Example:
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=REAL: Secret attack plan" \
  -F "password=RealPassword123" \
  -F "decoy_password=TryMe123" \
  -F "decoy_message=Just a harmless photo"
```

### Security Considerations:

✅ **Advantage:** No error message reveals anything  
✅ **Advantage:** Plausible deniability (can claim only decoy exists)  
⚠️ **Risk:** Decoy must be believable (matching real file content)  
⚠️ **Risk:** Wrong password still proves wrong attempt  

---

## Split Encoding

### Purpose

Distribute payload across multiple images for:
- **Higher Capacity:** Hide more data
- **Redundancy:** Lose one image, recover from others
- **Distribution:** Spread across multiple carriers

### How It Works:

```
Payload (100KB)
    ↓
Split into 4 segments (25KB each)
    ↓
Segment 1 → Image 1 (25KB hidden)
Segment 2 → Image 2 (25KB hidden)
Segment 3 → Image 3 (25KB hidden)
Segment 4 → Image 4 (25KB hidden)
    ↓
User receives 4 images (total: 100KB payload)
```

### Encoding Example:

**Web UI:**
1. Click "📦 SPLIT MODE"
2. Upload 4 carrier images
3. Upload files to hide (or enter message)
4. Set password
5. Click "🚀 Encode"

**API:**
```python
files = {
    'images': [
        open('image1.png', 'rb'),
        open('image2.png', 'rb'),
        open('image3.png', 'rb'),
        open('image4.png', 'rb')
    ]
}

data = {
    'message': 'Large message or file data',
    'password': 'SplitPassword123'
}

response = requests.post(
    'http://127.0.0.1:5000/api/v1/encode-split',
    files=files,
    data=data
)

# Download returns ZIP with all 4 encoded images
```

### Decoding Example:

**Web UI:**
1. Click "🔓 DECODE" → "SPLIT MODE"
2. Upload all 4 images
3. Enter password
4. Click "Extract"

**API:**
```python
files = {
    'images': [
        open('stego_1.png', 'rb'),
        open('stego_2.png', 'rb'),
        open('stego_3.png', 'rb'),
        open('stego_4.png', 'rb')
    ]
}

data = {'password': 'SplitPassword123'}

response = requests.post(
    'http://127.0.0.1:5000/api/v1/decode-split',
    files=files,
    data=data
)

# Response contains extracted payload
```

### Advantages:
- ✅ Hide more data than single image
- ✅ Distribute risk across carriers
- ✅ Could be suspicious if found (why 4 identical images?)

---

## ECDH Key Exchange

### What is ECDH?

Elliptic Curve Diffie-Hellman: Agreement protocol to establish shared secret over insecure channel.

### Use Case:

Two people want to agree on encryption key without secure channel:

```
Alice                              Bob
  ↓                                ↓
Generate keypair                Generate keypair
(Private: A, Public: PA)        (Private: B, Public: PB)
  ↓                                ↓
Exchange public keys      ←→    Exchange public keys
  ↓                                ↓
Compute: ECDH(A, PB)            Compute: ECDH(B, PA)
  ↓                                ↓
Shared Secret S                 Shared Secret S
  ↓                                ↓
Same secret! ════════════════════ Same secret!
```

### Supported Curves:

| Curve | Bits | Strength | Use Case |
|-------|------|----------|----------|
| P-256 | 256 | High | Default, balance |
| P-384 | 384 | Very High | Maximum security |
| P-521 | 521 | Extreme | Future-proof |

### Usage Example:

**Step 1: Generate Keypairs**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/ecdh/generate \
  -F "curve=p256"

# Response:
# {
#   "curve": "p256",
#   "private_key": "base64_private",
#   "public_key": "base64_public"
# }
```

**Step 2: Exchange Public Keys**
```
Alice sends her public_key to Bob (via public channel)
Bob sends his public_key to Alice (via public channel)
```

**Step 3: Compute Shared Secret**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/ecdh/exchange \
  -F "curve=p256" \
  -F "private_key=<your_private_key>" \
  -F "peer_public_key=<other_person_public_key>"

# Response:
# {
#   "shared_secret": "base64_shared_secret",
#   "secret_length": 32
# }
```

**Step 4: Use Shared Secret as Password**
```bash
# Use shared_secret as password for encoding
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Secret" \
  -F "password=<shared_secret>"
```

### Python Example:

```python
import requests
import base64

# Alice generates keypair
response = requests.post(
    'http://127.0.0.1:5000/api/v1/ecdh/generate',
    data={'curve': 'p256'}
)
alice_private = response.json()['private_key']
alice_public = response.json()['public_key']

# Bob generates keypair (same process)
bob_private = "..."  # Bob's private key
bob_public = "..."   # Bob's public key

# Alice computes shared secret
response = requests.post(
    'http://127.0.0.1:5000/api/v1/ecdh/exchange',
    data={
        'curve': 'p256',
        'private_key': alice_private,
        'peer_public_key': bob_public
    }
)
shared_secret = response.json()['shared_secret']

# Now use shared_secret as password for StegoForge
```

---

## Video Steganography

### Embedding Messages in Videos

Hide messages in video frames (requires FFmpeg).

### How It Works:

```
Video: movie.mp4
  ↓
Extract frames: frame_0.png, frame_1.png, ..., frame_N.png
  ↓
Embed message in random frames
  ↓
Reassemble frames → Output video
```

### API Usage:

```bash
curl -X POST http://127.0.0.1:5000/api/v1/video/embed \
  -F "video=@movie.mp4" \
  -F "message=Hidden in video" \
  -F "password=VideoPassword123" \
  -F "frames=10"
```

### Extraction:

```bash
curl -X POST http://127.0.0.1:5000/api/v1/video/extract \
  -F "video=@stego_movie.mp4" \
  -F "password=VideoPassword123"
```

### Requirements:
- FFmpeg installed and in PATH
- Video file size matters (larger videos = more space)
- Extracting requires exact frame extraction

---

## Steganalysis & Detection

### Analyze if Image Contains Hidden Content

Machine learning-based detection.

### API:
```bash
curl -X POST http://127.0.0.1:5000/api/v1/steganalysis \
  -F "image=@suspicious_image.png"

# Response:
# {
#   "stego_probability": 0.85,
#   "confidence": "High",
#   "analysis": {
#     "lsb_bias": -0.02,
#     "chi_square": 145.3,
#     "entropy": 7.98
#   }
# }
```

### Metrics:

| Metric | Meaning |
|--------|---------|
| `stego_probability` | 0-1 (0=natural, 1=likely stego) |
| `lsb_bias` | Least Significant Bit distribution |
| `chi_square` | Statistical deviation |
| `entropy` | Information randomness |

**Important:** Not 100% accurate. False positives common!

---

## Advanced Compression

### Compression Methods

#### ZIP Compression
- **Ratio:** 50-70%
- **Speed:** Fast
- **Compatibility:** Universal
- **Use:** Default, most compatible

#### 7-Zip Compression
- **Ratio:** 60-80% (better)
- **Speed:** Slower
- **Compatibility:** Less common
- **Use:** Maximum compression

### Choosing Compression:

**API Example with 7-Zip:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode-batch \
  -F "image=@carrier.png" \
  -F "files=@large_file.bin" \
  -F "password=MyPassword123" \
  -F "compression_method=7z"
```

### Compression Algorithm:

```
Original Files: 10 MB
  ↓
ZIP Compression: 3.5 MB (65% ratio)
  ↓
Encryption: 3.5 MB + 32 bytes overhead
  ↓
Image Capacity Check: Needs 3.5MB
```

---

## Multi-Carrier Distribution

### Distribute Payload Across Multiple Images

Different from Split Encoding:

```
Split Encoding: 100KB payload split to 4 images (25KB each)
Multi-Carrier: Same payload encoded in each carrier separately

Benefits:
- Redundancy: Any one carrier = full payload recovery
- Backup: Automatic backups
- Distribution: Can send carriers separately
```

### API:
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode-multi-carrier \
  -F "carrier_0=@image1.png" \
  -F "carrier_1=@image2.png" \
  -F "carrier_2=@image3.png" \
  -F "files=@important.zip" \
  -F "password=MultiPassword123"
```

---

## Advanced Security Combinations

### Scenario: Maximum Security

Combine features for ultimate protection:

```python
data = {
    'message': 'Top secret',
    'password': 'SuperSecurePassword123!@#',
    'double_encrypt': 'true',      # 2x AES-256
    'self_destruct': 'true',        # Expiry + max attempts
    'ttl_seconds': '600',           # 10 minutes
    'max_attempts': '3',            # 3 tries then locked
    'decoy_password': 'DecoyPwd123', # Show decoy on wrong attempt
    'decoy_message': 'This is just a cat photo',
    'aes_bits': '256',              # Maximum strength
    'remove_exif': 'true'           # Remove metadata
}
```

**Result:**
- ✅ Double encrypted
- ✅ Expires in 10 minutes
- ✅ Self-destructs after 3 wrong attempts
- ✅ Wrong password shows decoy
- ✅ No metadata
- ✅ Maximum security

---

## Performance Optimization

### Best Practices for Large Files:

1. **Use Batch Mode** - Automatic compression
2. **Choose Right Compression** - 7z for max compression, ZIP for speed
3. **Use Split Mode** - Distribute across multiple images
4. **Enable Streaming** - For very large files
5. **Check Capacity First** - Verify image can hold data

### Capacity Estimation:

```
Image Size (pixels): W × H × 3 channels
Usable Capacity: (W × H × 3) / 8 bytes

Example:
1600 × 1200 × 3 = 5,760,000 bits
5,760,000 / 8 = 720,000 bytes = 720 KB raw capacity
With compression (70% ratio): 720 × 3 = 2.1 MB with 7z
```

---

## Error Codes & Handling

### Advanced Errors:

| Code | Cause | Solution |
|------|-------|----------|
| `INSUFFICIENT_CAPACITY` | Payload too large | Use compression or larger image |
| `MESSAGE_EXPIRED` | TTL exceeded | Request fresh copy |
| `SELF_DESTRUCT_ACTIVATED` | Too many attempts | Image is locked forever |
| `SERVICE_DEGRADED` | Service overloaded | Wait and retry |
| `ENCRYPTION_ERROR` | Crypto operation failed | Report to support |

---

**Advanced Features Guide Version:** 4.0.0  
**Last Updated:** 2024  
**Target Audience:** Power Users & Developers
