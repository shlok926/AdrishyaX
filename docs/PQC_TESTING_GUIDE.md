# Post-Quantum Cryptography Testing Guide
## StegoForge v4.0 - Feature #4 Verification

---

## 📋 **PRE-TESTING CHECKLIST**

### Environment Setup
- [ ] Windows PowerShell or Command Prompt open
- [ ] Navigate to: `d:\Desktop\StegoForge`
- [ ] Virtual environment activated (if exists)
- [ ] Port 5000 available (or Flask configured differently)
- [ ] All dependencies installed

### File Verification
- [ ] `server.py` exists (2700+ lines)
- [ ] `post_quantum_crypto.py` exists (500+ lines)
- [ ] `public/index.html` exists (7500+ lines)
- [ ] `.venv` folder present (or Python 3.11+ installed)

---

## 🚀 **STARTUP PROCEDURE**

### Step 1: Verify Python Installation
```powershell
# Check Python version
python --version

# Should show: Python 3.11.x or higher
```

### Step 2: Create/Activate Virtual Environment (If Needed)
```powershell
# Create venv
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# OR Activate (Command Prompt)
.venv\Scripts\activate.bat
```

### Step 3: Install Dependencies
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install Flask
pip install flask

# Install liboqs-python (Required for PQC)
pip install liboqs-python

# Install other dependencies
pip install flask-cors flask-limiter requests cryptography
```

### Step 4: Start Flask Server
```powershell
# From d:\Desktop\StegoForge directory
python server.py

# Expected output:
# WARNING in app.run(): This is a development server...
# WARNING in werkzeug...: Running on http://127.0.0.1:5000
```

### Step 5: Open Web Browser
- **URL:** http://localhost:5000
- **Expected:** StegoForge homepage loads
- **Look for:** Sidebar with ⚛️ Quantum-Safe option

---

## 🧪 **UNIT TESTS**

### Test 1: Backend Module Import
```powershell
# In Python interpreter
python -c "from post_quantum_crypto import PostQuantumCrypto; print('✅ Module imported successfully')"

# Expected output:
# ✅ Module imported successfully
# (May take 5-10 seconds on first run for liboqs compilation)
```

### Test 2: Create PQC Instance
```powershell
# Create test script: test_pqc.py
$code = @'
from post_quantum_crypto import PostQuantumCrypto
pqc = PostQuantumCrypto()
print("✅ PostQuantumCrypto instance created")
print("Available methods:", dir(pqc))
'@
Set-Content -Path test_pqc.py -Value $code
python test_pqc.py
```

---

## 🌐 **WEB INTERFACE TESTS**

### Test Suite: ML-KEM Operations

#### Test 1A: Navigate to PQC Panel
**Steps:**
1. Load http://localhost:5000
2. Look for sidebar on left side
3. Locate "⚛️ Quantum-Safe" item (should be at bottom)
4. Click on it

**Expected Result:**
- Panel switches to PQC section
- Three algorithm boxes visible: ML-KEM, ML-DSA, Hybrid
- ML-KEM tab shows by default

**Validation:**
- [ ] Sidebar item highlights on click
- [ ] Panel transitions smoothly
- [ ] ML-KEM box has icon and description

---

#### Test 1B: Generate ML-KEM Keys
**Steps:**
1. Ensure on ML-KEM tab
2. Click "🔑 Generate Key Pair" button
3. Wait 10-15 seconds for completion
4. Observe console for progress messages

**Expected Result:**
- Loading spinner appears
- Toast notification: "✅ ML-KEM key pair generated successfully"
- Public key displays in green box
- Private key shows as "[⚠️ PRIVATE - Keep Secret]"

**Validation:**
- [ ] Loading state appears/disappears correctly
- [ ] Toast notification displays
- [ ] Keys display in proper format
- [ ] No error messages in console

**Log Verification (Browser Console - F12):**
```
ML-KEM keys generated (256-bit security)
[success] in PQC panel state
```

---

#### Test 1C: Encapsulate (Create Shared Secret)
**Steps:**
1. Copy public key from Test 1B
2. Paste into "Recipient's ML-KEM Public Key" field
3. Click "📤 Encapsulate" button
4. Wait for completion

**Expected Result:**
- Loading spinner appears
- Toast: "✅ Encapsulation successful!"
- Shared Secret displays (partial: "...256 characters")
- Ciphertext displays below
- "📋 Copy Result" button appears

**Validation:**
- [ ] Public key accepted without error
- [ ] Shared secret generates (~64 hex characters)
- [ ] Ciphertext generates (different format)
- [ ] Copy button works

---

#### Test 1D: Decapsulate (Extract Shared Secret)
**Steps:**
1. Copy Ciphertext from Test 1C
2. Paste into "Ciphertext" field
3. Retrieve private key from Test 1B (or use stored: window.mlkemPrivateKey)
4. Paste into "Private Key" field
5. Click "📥 Decapsulate" button

**Expected Result:**
- Loading spinner
- Toast: "✅ Decapsulation successful!"
- Recovered Shared Secret displays
- Should match shared secret from Test 1C

**Validation:**
- [ ] Ciphertext accepted
- [ ] Private key accepted
- [ ] Recovered secret matches original
- [ ] No errors in console

---

### Test Suite: ML-DSA Operations

#### Test 2A: Generate ML-DSA Keys
**Steps:**
1. Click "ML-DSA" tab
2. Click "🔑 Generate Signing Keys" button
3. Wait 10-15 seconds

**Expected Result:**
- Toast: "✅ ML-DSA key pair generated successfully"
- Signing key shows as "[⚠️ KEEP SECRET]"
- Verification key displays in green
- "📋 Copy Public Key" button available

**Validation:**
- [ ] Key generation completes
- [ ] Both keys stored in window variables
- [ ] Public key can be copied
- [ ] No errors

---

#### Test 2B: Sign File
**Steps:**
1. Create test file: `test_document.txt` with content "Hello, Quantum World!"
2. Click file upload zone in "Sign File" section
3. Select `test_document.txt`
4. Paste ML-DSA private key (from Test 2A)
5. Click "Sign File" button

**Expected Result:**
- Toast: "✅ File signed successfully!"
- File name displays: "test_document.txt"
- Digital signature appears (long base64 string)
- "📋 Copy Signature" button available

**Validation:**
- [ ] File selection works
- [ ] File size displays correctly
- [ ] Signature generates
- [ ] Signature is ~4000 characters (base64 encoded)

---

#### Test 2C: Verify Signature
**Steps:**
1. Copy signature from Test 2B
2. Use same test file from Test 2B
3. Copy verification key (public key) from Test 2A
4. Paste signature into "Signature" field
5. Paste public key into "Public Key" field
6. Upload file in "Verify Signature" zone
7. Click "Verify Signature" button

**Expected Result:**
- Toast: "✅ Signature is valid!"
- Green box with: "✅ SIGNATURE VALID"
- File name displays

**Validation:**
- [ ] Signature validates successfully
- [ ] Result displays with green highlight
- [ ] Console shows: "✅ SIGNATURE VALID [success]"

#### Test 2D: Invalid Signature (Negative Test)
**Steps:**
1. Modify the signature (change first character)
2. Try to verify same file
3. Click "Verify Signature" button

**Expected Result:**
- Toast: "❌ Signature is invalid!"
- Red box with: "❌ SIGNATURE INVALID"

**Validation:**
- [ ] Invalid signature rejected
- [ ] Error handling works
- [ ] No crashes or console errors

---

### Test Suite: Hybrid Mode Operations

#### Test 3A: Generate Hybrid Keys
**Steps:**
1. Click "Hybrid Mode" tab
2. Click "🔑 Generate Hybrid Keys" button
3. Wait 15-20 seconds (longer than individual keys)

**Expected Result:**
- Toast: "✅ Hybrid key pair generated successfully"
- RSA Public Key displays (partial)
- ML-KEM Public Key displays (partial)
- "⚠️ Private Keys" section shows secure storage message
- "📥 Download Keys (ZIP)" button available

**Validation:**
- [ ] Both keys generate
- [ ] Loading time ~15-20 seconds
- [ ] Keys stored in window variables
- [ ] Download button functional

---

#### Test 3B: Hybrid Encryption
**Steps:**
1. Create test file: `secret_message.pdf` (or any file)
2. Click upload zone in "Hybrid Encrypt" section
3. Select file
4. Paste RSA Public Key (first public key from Test 3A)
5. Paste ML-KEM Public Key (second public key from Test 3A)
6. Click "Encrypt with Hybrid Mode" button
7. Wait for completion

**Expected Result:**
- Toast: "✅ Hybrid encryption successful!"
- Three ciphertexts display:
  - RSA Ciphertext (very long base64)
  - ML-KEM Ciphertext (long base64)
  - Encrypted Data (long base64)
- "📋 Copy All Results" button appears

**Validation:**
- [ ] File selection works
- [ ] Both public keys accepted
- [ ] Three different ciphertexts generate
- [ ] No errors

---

#### Test 3C: Hybrid Decryption
**Steps:**
1. Copy all three ciphertexts from Test 3B
2. Click "Hybrid Mode" tab (if not already there)
3. Scroll to "Hybrid Decrypt" section
4. Paste RSA Ciphertext into first field
5. Paste ML-KEM Ciphertext into second field
6. Paste Encrypted Data into third field
7. Paste RSA Private Key
8. Paste ML-KEM Private Key
9. Click "Decrypt with Hybrid Mode" button

**Expected Result:**
- Toast: "✅ Hybrid decryption successful!"
- Green box with: "✅ DECRYPTION SUCCESSFUL"
- Plaintext displays in textarea

**Validation:**
- [ ] All three ciphertexts accepted
- [ ] Both private keys accepted
- [ ] Plaintext recovers successfully
- [ ] Plaintext matches original file content

---

## 📊 **API ENDPOINT TESTS** (Using cURL or Postman)

### Test API 1: ML-KEM Key Generation
```bash
curl -X POST http://localhost:5000/api/v1/pqc/mlkem/generate-keys \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: 200 OK
# Response: {
#   "status": "success",
#   "keys": {
#     "public_key": "base64_string_...",
#     "private_key": "base64_string_..."
#   }
# }
```

### Test API 2: ML-KEM Encapsulation
```bash
# First get public key from Test API 1, then:
curl -X POST http://localhost:5000/api/v1/pqc/mlkem/encapsulate \
  -H "Content-Type: application/json" \
  -d '{"public_key": "paste_key_here"}'

# Expected: 200 OK
# Response: {
#   "status": "success",
#   "shared_secret": "hex_string_...",
#   "ciphertext": "base64_string_..."
# }
```

### Test API 3: ML-DSA Signing
```bash
# Create test file first
curl -X POST http://localhost:5000/api/v1/pqc/mldsa/sign \
  -F "file=@test_document.txt" \
  -F "private_key=paste_key_here"

# Expected: 200 OK
# Response: {
#   "status": "success",
#   "signature": "base64_string_..."
# }
```

---

## ⚠️ **TROUBLESHOOTING**

### Issue 1: "ModuleNotFoundError: No module named 'oqs'"
**Cause:** liboqs-python not installed or compiled

**Solution:**
```powershell
# Option 1: Install with pip
pip install liboqs-python

# Option 2: If compilation fails on Windows
# Use Windows Subsystem for Linux (WSL):
wsl
pip install liboqs-python

# Option 3: Use Docker
docker run -it python:3.11 bash
pip install liboqs-python
```

### Issue 2: "404 Not Found" on API Endpoints
**Cause:** Flask server not running or wrong routes

**Solution:**
1. Verify server running: http://localhost:5000 should show homepage
2. Check server console for error messages
3. Verify `server.py` has `/api/v1/pqc/` routes (grep_search confirm)
4. Check network tab in browser (F12) for actual request URL

### Issue 3: "Timeout" on Key Generation
**Cause:** First run compilation or slow machine

**Solution:**
1. Wait longer (liboqs compiles native library on first use)
2. Check `server.py` logs for compilation messages
3. May take 30+ seconds on first run

### Issue 4: JavaScript Functions Not Defined
**Cause:** Functions not loaded in index.html

**Solution:**
1. Refresh browser (F5)
2. Clear browser cache (Ctrl+Shift+Delete)
3. Check browser console (F12) for syntax errors
4. Verify function names in HTML match JavaScript

### Issue 5: File Upload Not Working
**Cause:** File size limit or FormData issue

**Solution:**
1. Try smaller test file (<1MB)
2. Check browser console for errors
3. Verify file input element has correct ID
4. Test with simple .txt file first

---

## ✅ **VERIFICATION CHECKLIST**

### Backend Verification
- [ ] `post_quantum_crypto.py` imports without errors
- [ ] All 9 PQC endpoints exist in `server.py`
- [ ] `pqc` instance created globally
- [ ] No Python syntax errors (try `python -m py_compile server.py`)

### Frontend Verification
- [ ] Sidebar has "⚛️ Quantum-Safe" item
- [ ] PQC panel loads when clicked
- [ ] ML-KEM, ML-DSA, Hybrid tabs visible
- [ ] All input fields present with correct IDs

### API Verification
- [ ] `/api/v1/pqc/mlkem/generate-keys` returns 200 OK
- [ ] `/api/v1/pqc/mldsa/generate-keys` returns 200 OK
- [ ] `/api/v1/pqc/hybrid/generate-keys` returns 200 OK
- [ ] Error responses are formatted consistently

### Integration Verification
- [ ] Full ML-KEM: Generate → Encapsulate → Decapsulate
- [ ] Full ML-DSA: Generate → Sign → Verify
- [ ] Full Hybrid: Generate → Encrypt → Decrypt
- [ ] All three complete successfully

---

## 🎯 **SUCCESS CRITERIA**

### Test Complete When:
1. ✅ All unit tests pass
2. ✅ All web interface tests pass
3. ✅ All API endpoint tests pass
4. ✅ No console errors (F12 Developer Tools)
5. ✅ No server errors (Terminal output)
6. ✅ All 3 algorithms functional
7. ✅ File upload/download working
8. ✅ Error messages display correctly

### Performance Targets:
- Key generation: 10-20 seconds
- Encapsulation: <1 second
- Signing/Verification: <1 second
- File operations: <5 seconds for <1MB files

---

## 📝 **TEST REPORT TEMPLATE**

Use this format to document test results:

```markdown
# PQC Testing Report - [DATE]

## Environment
- OS: Windows 11
- Python: 3.11.x
- Browser: Chrome/Firefox
- Server: Flask Development

## Test Results

### Backend Tests
- [ ] Import test: PASS/FAIL
- [ ] Instance creation: PASS/FAIL
- [ ] API endpoints: PASS/FAIL

### ML-KEM Tests
- [ ] Key generation: PASS/FAIL (time: __s)
- [ ] Encapsulation: PASS/FAIL
- [ ] Decapsulation: PASS/FAIL

### ML-DSA Tests
- [ ] Key generation: PASS/FAIL (time: __s)
- [ ] File signing: PASS/FAIL
- [ ] Signature verification: PASS/FAIL

### Hybrid Tests
- [ ] Key generation: PASS/FAIL (time: __s)
- [ ] Encryption: PASS/FAIL
- [ ] Decryption: PASS/FAIL

## Issues Found
(List any issues discovered)

## Overall Status: PASS/FAIL

## Sign-off
Date: ________
Tester: ________
Notes: ________
```

---

## 🚀 **NEXT STEPS AFTER SUCCESSFUL TESTING**

1. **Deploy to Production**
   - Use WSL or Docker for liboqs compatibility
   - Configure HTTPS/SSL certificates
   - Set up database for key storage

2. **Integration Testing**
   - Test alongside Features #1-3
   - Verify cross-feature compatibility
   - Load testing with multiple users

3. **Security Audit**
   - Code review by security team
   - Penetration testing
   - Compliance verification (FIPS 203/204)

4. **Performance Optimization**
   - Benchmark against classical encryption
   - Optimize key generation time
   - Cache frequently used keys

5. **Documentation**
   - User guide for PQC operations
   - Admin guide for key management
   - API documentation for integrations

---

**Last Updated:** April 29, 2026  
**Version:** 1.0  
**Status:** Ready for Testing
