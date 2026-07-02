# Quick Start Testing Guide
## StegoForge v4.0 - Windows Development

---

## 🚀 **Quick Start (2 minutes)**

### 1. Start Flask Server
```powershell
# In PowerShell/Command Prompt
cd d:\Desktop\StegoForge
python server.py

# Expected output:
# Running on http://127.0.0.1:5000
```

### 2. Open Browser
```
URL: http://localhost:5000
```

### 3. You should see:
- StegoForge v4 ULTIMATE header
- Sidebar with 12 navigation options
- Image Steganography panel active
- Status showing "Ready"

---

## 🧪 **Test Image Steganography (5 minutes)**

### Step-by-Step

**1. Prepare Test Image**
   - Image: `test_image.png` (already created, 800x600)
   - Location: `d:\Desktop\StegoForge\test_image.png`

**2. Upload Image to Stego**
   - Click on "🖼️ Cover Image" upload zone
   - Select `test_image.png` from `d:\Desktop\StegoForge\`
   - You should see:
     - Dimensions: 800 x 600
     - Capacity: ~160 KB

**3. Enter Message**
   - Click message text box: "Enter message to hide..."
   - Copy from `test_message.txt`:
     ```
     StegoForge v4 Test Message - This is a secret message hidden in steganography!
     ```
   - Paste into message field

**4. Set Encryption Key**
   - Click password field: "Encryption Key / Password"
   - Enter: `testkey123`

**5. Encode Image**
   - Click "Start Encoding" button
   - Wait for completion (should be <5 seconds)
   - You should see:
     - Status changes to "Encoding..."
     - Progress bar fills
     - "✅ Encoding successful!" message appears

**6. Save Encoded Image**
   - Download button appears
   - Save as: `test_encoded.png`

**7. Test Decoding**
   - Click "🔍 Decode" in sidebar
   - Upload `test_encoded.png`
   - Enter password: `testkey123`
   - Click "Extract Message"
   - Verify message matches original

### Expected Results
✅ Message encodes without errors  
✅ Encoded image looks similar to original  
✅ Message decodes perfectly  
✅ Wrong password shows error  

---

## 🔐 **Test Encryption (5 minutes)**

### AES Encryption Test

**1. Navigate to Encryption**
   - Click "🔐 Encryption" in sidebar

**2. Select AES Algorithm**
   - Look for algorithm selection dropdown
   - Select "AES-256-CBC"

**3. Encrypt Data**
   - Enter plaintext: `Secret data for encryption testing`
   - Enter password: `SecurePass123`
   - Click "Encrypt"
   - You should see a long ciphertext

**4. Copy Ciphertext**
   - Click "Copy Ciphertext" button

**5. Decrypt Data**
   - Paste ciphertext into decrypt field
   - Enter password: `SecurePass123`
   - Click "Decrypt"
   - Verify plaintext matches original

### Expected Results
✅ Encryption produces different ciphertext each time (due to random IV)  
✅ Decryption recovers original plaintext exactly  
✅ Wrong password shows error or garbage output  

---

## 🎵 **Test Audio Steganography (Optional - 5 minutes)**

### Prerequisites
- Need to create test audio file (optional)
- Or use any .wav file

### Steps

**1. Navigate to Audio Stego**
   - Click "🎵 Audio Stego" in sidebar

**2. Upload Audio**
   - Click upload zone
   - Select audio file (.wav, .mp3, etc.)
   - Wait for analysis

**3. Enter Message**
   - Type message to hide in audio

**4. Set Key**
   - Enter encryption key

**5. Encode**
   - Click "Encode Audio"
   - Wait for completion

**6. Extract**
   - Upload encoded audio
   - Enter key
   - Click "Extract Message"
   - Verify message recovered

### Expected Results
✅ Audio file loads with duration shown  
✅ Message encodes into audio  
✅ Encoded audio still plays  
✅ Message extracts correctly  

---

## 📊 **Monitor Performance**

### Check Encoding Speed
```javascript
// In browser console (F12 → Console tab):
console.time('encode');
// ... click Start Encoding ...
console.timeEnd('encode');

// You'll see: encode: XXXms
```

### Check Network Requests
1. Press F12 to open Developer Tools
2. Click "Network" tab
3. Perform encoding operation
4. Watch requests appear:
   - Check response times
   - Look for any failed requests (red)
   - Check response status (200, 400, 500, etc.)

### View Error Messages
```javascript
// Check console for error logs
// Browser console (F12 → Console tab) shows:
// ✅ Success messages in green
// ❌ Error messages in red
// ⚠️ Warnings in yellow
```

---

## 🐛 **Troubleshooting**

### Issue: "Cannot load image"
**Solution:**
- Check file format (PNG, BMP, WEBP supported)
- Ensure file is not corrupted
- Try smaller image first

### Issue: "Insufficient capacity"
**Solution:**
- Message is too large for image
- Use larger image
- Compress message (remove spaces, use shorthand)

### Issue: "Decoding failed"
**Solution:**
- Check password is correct
- Ensure image hasn't been modified
- Try re-encoding with same image

### Issue: "Server error 503"
**Solution:**
- This is expected for PQC features (liboqs unavailable on Windows)
- Other features should work fine
- Check server terminal for error details

---

## 📋 **Testing Checklist**

### Before Testing
- [ ] Flask server running (`python server.py`)
- [ ] Browser at `http://localhost:5000`
- [ ] Browser console open (F12)
- [ ] Test files created (`test_image.png`, etc.)

### Image Stego
- [ ] Image uploads successfully
- [ ] Capacity calculated correctly
- [ ] Message encodes without errors
- [ ] Encoded image downloads
- [ ] Message decodes perfectly
- [ ] Wrong password fails gracefully

### Encryption
- [ ] AES encryption/decryption works
- [ ] Data perfectly recovers after decrypt
- [ ] Wrong password fails properly
- [ ] Large data handled (test with test_data.bin)

### Audio Stego (if testing)
- [ ] Audio file uploads
- [ ] Message encodes to audio
- [ ] Encoded audio plays
- [ ] Message extracts correctly

### Performance
- [ ] Small image encode: < 5 seconds
- [ ] Large image encode: < 10 seconds
- [ ] Decryption: < 1 second
- [ ] No memory leaks (memory stable)

---

## 🔧 **Development Tips**

### Enable Debug Mode
```python
# In server.py, change:
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'

# To:
DEBUG = True

# Then restart server
```

### View Server Logs
- All API calls logged to terminal
- Look for `INFO:` lines for successful operations
- Look for `ERROR:` lines for failures
- Check response times in logs

### Clear Browser Cache
```
Chrome/Edge: Ctrl+Shift+Delete → Clear browsing data
Firefox: Ctrl+Shift+Delete → Clear Recent History
Safari: Develop menu → Empty Caches
```

### Test with Network Throttling
- F12 → Network tab → Throttling dropdown
- Select "Fast 3G" or "Slow 3G" to test with slow connection
- Helps identify performance issues

---

## 📝 **Testing Notes Template**

Create a file like `TEST_LOG.md`:

```markdown
# Test Log - [DATE]

## Test 1: Image Stego
- **Status:** PASS/FAIL
- **Time:** XXX seconds
- **Notes:** [Observations]
- **Issues:** [Any problems]

## Test 2: Encryption
- **Status:** PASS/FAIL
- **Time:** XXX seconds
- **Notes:** [Observations]
- **Issues:** [Any problems]

## Overall Status
- **All Tests:** PASS/FAIL
- **Blockers:** [Any critical issues]
- **Next Steps:** [What to test next]
```

---

## 🎯 **What's Ready to Test**

### ✅ Fully Operational
- Image Steganography (encode/decode)
- Message Encryption (AES, RSA, ChaCha20)
- Encryption Key Exchange
- Analysis Console (heatmap, pixel inspector)
- Visualization tools
- Session history and analytics

### ⚠️ Gracefully Disabled
- Post-Quantum Cryptography (requires WSL/Docker)
- Returns clear error message when accessed

### 📋 To Be Tested
- Audio Steganography (needs verification)
- Batch processing modes
- Large file handling
- Cross-browser compatibility
- Performance under load

---

## 🚀 **Next Steps**

1. **Complete Manual Testing** (15-20 minutes)
   - Follow test procedures above
   - Document findings
   - Note any issues

2. **Performance Benchmarking** (10 minutes)
   - Measure encode/decode speeds
   - Test with different file sizes
   - Record results in TEST_LOG.md

3. **Bug Fixes** (as needed)
   - Fix any issues discovered
   - Re-test to confirm fixes
   - Update DEVELOPMENT_PLAN.md

4. **Performance Optimization** (when ready)
   - Identify bottlenecks
   - Optimize code
   - Re-benchmark after optimizations

---

## 📞 **Quick Reference**

| Task | Command | Time |
|------|---------|------|
| Start Server | `python server.py` | 1 min |
| Test Image Stego | Manual browser test | 5 min |
| Test Encryption | Manual browser test | 5 min |
| Test Audio Stego | Manual browser test | 5 min |
| Performance Test | Monitor via console | 5 min |

---

## ✅ **Current Status**

🟢 **Server:** Running on http://localhost:5000  
🟢 **Features #1-3:** Ready for testing  
🟡 **Feature #4:** Gracefully disabled (expected)  
🟢 **Test Files:** Created and ready  

**Ready to Begin Testing!**

---

**Created:** May 2, 2026  
**Version:** 1.0  
**Status:** Ready for Development
