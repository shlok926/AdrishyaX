# StegoForge v4 - Troubleshooting Guide

## Comprehensive Troubleshooting for StegoForge

---

## Table of Contents
1. [Common Errors & Solutions](#common-errors--solutions)
2. [Image-Related Issues](#image-related-issues)
3. [Encoding Problems](#encoding-problems)
4. [Decoding Problems](#decoding-problems)
5. [Performance Issues](#performance-issues)
6. [Security Features Troubleshooting](#security-features-troubleshooting)
7. [Advanced Troubleshooting](#advanced-troubleshooting)
8. [Getting Help](#getting-help)

---

## Common Errors & Solutions

### Error: "Image file required"

**Meaning:** No image was selected or upload failed.

**Causes:**
- No file selected in upload dialog
- File is not an image format
- File is corrupted
- Upload didn't complete

**Solutions:**

1. **Verify file is selected:**
   ```
   - Click "📤 UPLOAD CARRIER"
   - Select file
   - Confirm filename appears
   ```

2. **Check file format:**
   ```
   ✅ Supported: PNG, JPEG, BMP, GIF, WEBP
   ❌ Not supported: TIFF, ICO, SVG, RAW
   ```

3. **Try a different image:**
   ```
   - Use a simple test image first
   - Avoid corrupted files
   - Download fresh image from trusted source
   ```

4. **Check file size:**
   ```
   ✅ Optimal: 1MB - 50MB
   ❌ Too small: < 100KB
   ❌ Too large: > 200MB (may timeout)
   ```

5. **Verify upload:**
   ```
   - Check browser console (F12)
   - Look for network errors
   - Try different browser
   ```

---

### Error: "Validation error: Invalid image"

**Meaning:** File is technically an image but invalid.

**Causes:**
- Corrupted image file
- Incomplete download
- Wrong file extension
- Image is too small

**Solutions:**

1. **Test image integrity:**
   ```bash
   # Windows: Open with Windows Photo Viewer
   # Mac: Open with Preview
   # Linux: open with feh or imagemagick
   
   # If it opens fine, file is probably valid
   ```

2. **Check image dimensions:**
   - Right-click image → Properties
   - View width × height
   - ✅ Minimum: 100 × 100 pixels
   - ✅ Recommended: 400 × 300 pixels

3. **Re-download image:**
   - Delete current copy
   - Download again from source
   - Verify checksum if available

4. **Convert format:**
   ```bash
   # Windows: Use Paint to re-save as PNG
   # Mac: Use Preview to export as PNG
   # Linux: convert input.jpg output.png
   ```

---

### Error: "Message too long for payload"

**Meaning:** Message is larger than image capacity.

**Causes:**
- Message exceeds 10,000 characters
- Image is too small
- No compression enabled
- Message includes large file

**Solutions:**

1. **Shorten message:**
   ```
   Current length: 15,000 characters
   Max allowed: 10,000 characters
   Solution: Delete 5,000 characters
   ```

2. **Use larger image:**
   ```
   Small image: 400×300 = ~15KB capacity
   Medium image: 800×600 = ~60KB capacity
   Large image: 1600×1200 = ~250KB capacity
   ```

3. **Enable compression (batch mode):**
   ```
   1. Switch to BATCH MODE
   2. Upload files instead of raw text
   3. Enable compression (ZIP or 7z)
   4. Gets 50-80% size reduction
   ```

4. **Split across images:**
   ```
   1. Split long message into parts
   2. Encode part 1 in image 1
   3. Encode part 2 in image 2
   4. Decode both separately
   ```

5. **Use split mode:**
   ```
   1. Click "📦 SPLIT MODE"
   2. Upload multiple carrier images
   3. Message automatically distributed
   ```

---

### Error: "Authentication failed" or "Wrong password"

**Meaning:** Password used for decoding doesn't match encoding password.

**Causes:**
- Typo in password
- Password case mismatch
- Using different password
- Image is corrupted

**Solutions:**

1. **Verify password exactly:**
   ```
   Encoded with: "MyPassword123"
   Trying: "mypassword123" → WRONG (lowercase)
   Trying: "MyPassword123" → CORRECT
   
   ⚠️ Passwords are CASE-SENSITIVE
   ```

2. **Check for spaces:**
   ```
   Encoded with: "Password 123" (has space)
   Trying: "Password123" → WRONG (no space)
   
   ⚠️ Spaces count!
   ```

3. **Try original password:**
   ```
   - Check written notes
   - Check password manager
   - Check email where password was sent
   - Check shared secret with other person
   ```

4. **Check image integrity:**
   ```
   - Image might be corrupted
   - File might be wrong
   - Image might be edited
   - Try a backup copy
   ```

5. **After 3 failed attempts:**
   ```
   If self-destruct enabled:
   - Message may be permanently locked
   - No recovery possible
   - Encoding new message needed
   ```

---

### Error: "Rate limit exceeded"

**Meaning:** Too many requests in short time.

**Causes:**
- Made 10+ encode requests in 60 seconds
- Made 20+ decode requests in 60 seconds
- Automated scripts making requests
- Testing too quickly

**Solutions:**

1. **Wait 60 seconds:**
   ```
   Just wait. Rate limit resets automatically.
   ```

2. **Reduce request frequency:**
   ```
   Before: 10 requests/10 seconds
   After: 1 request/5 seconds
   ```

3. **Batch operations:**
   ```
   Instead of encoding 10 files separately,
   use BATCH MODE to encode all at once.
   ```

4. **Check endpoint limits:**
   ```
   /encode: 10 requests per minute
   /decode: 20 requests per minute
   /capacity-check: 30 requests per minute
   /video: 3-5 requests per minute
   ```

5. **Use API key (if available):**
   ```
   Some deployments offer higher limits with API key
   Contact administrator for details
   ```

---

## Image-Related Issues

### Problem: "Image too small for payload"

**Situation:** Selected image can't hold your message.

**Example:**
```
Image: 200×150 pixels
Capacity: ~5 KB
Message: "Hello world" = 11 bytes
Status: OK (fits)

But if message was 10 KB:
Status: ERROR (doesn't fit)
```

**Solution Checklist:**

| Solution | Steps |
|----------|-------|
| **Use larger image** | Find image with more pixels |
| **Reduce message** | Shorten text or remove files |
| **Use split mode** | Spread across multiple images |
| **Use compression** | BATCH mode compresses automatically |

**Quick Size Check:**
```
Image pixels ÷ 24 = approximate capacity in bytes

Example:
800×600 = 480,000 pixels
480,000 ÷ 24 = 20 KB capacity
```

---

### Problem: "Image quality degraded after download"

**Meaning:** Downloaded stego image looks different.

**Causes:**
- JPEG compression (lossy format)
- Browser auto-compression
- Color profile change
- Image scaling

**Solutions:**

1. **For encoding, use PNG:**
   - PNG is lossless (no quality loss)
   - JPEG uses compression (loses data)
   - ✅ Encode: Use PNG
   - ⚠️ Encoding: JPEG works but quality degrades

2. **For input, prefer PNG:**
   ```
   ✅ Best: Original PNG
   ⚠️ Good: High-quality JPEG (95%+)
   ❌ Avoid: Low-quality JPEG (< 75%)
   ```

3. **Check download settings:**
   - Browser might compress images
   - Check Downloads folder for original
   - Verify file integrity
   - Try different browser

4. **Verify stego image works:**
   - Even if quality degraded, should still decode
   - If decode fails, image is corrupted
   - Try backup copy

---

### Problem: "EXIF data reveals information"

**Meaning:** Image metadata could expose sensitive info.

**Example:**
```
Secret: "Meeting at secret location"
EXIF data: GPS coordinates of location

Risk: If image shared, GPS revealed
```

**Solution:**

1. **Remove EXIF during encoding:**
   ```
   Click ⚡ Advanced Options
   Check ☑️ Remove EXIF
   Encodes without metadata
   ```

2. **Remove EXIF before encoding:**
   ```bash
   # Using ImageMagick
   mogrify -strip image.jpg
   
   # Using ExifTool
   exiftool -all= image.jpg
   ```

3. **Check EXIF before sharing:**
   ```bash
   # View EXIF data
   exiftool image.png
   
   # Check for coordinates, camera info, timestamps
   ```

---

## Encoding Problems

### Problem: "Encoding takes forever"

**Meaning:** Encoding process is slow or hangs.

**Causes:**
- Large image (memory intensive)
- Slow computer
- Disk I/O bottleneck
- Double encryption enabled

**Solutions:**

1. **For large images:**
   ```
   Current: 5000×4000 image = 60MB
   Processing: Might take 30+ seconds
   
   Solution: Use smaller image if possible
   Or increase timeout in browser
   ```

2. **For slow computers:**
   ```
   Disable: Double encryption (processes twice)
   Disable: Remove EXIF (scans metadata)
   Try: Smaller message first
   ```

3. **Monitor progress:**
   ```
   Open browser console (F12)
   Watch network requests
   Look for /api/v1/encode request
   Should show progress or streaming
   ```

4. **Increase timeout:**
   ```javascript
   // In browser console:
   // Default timeout is usually 30 seconds
   // Some large operations need more time
   ```

5. **Try splitting:**
   ```
   Instead of 1 large image:
   Use split mode with multiple smaller images
   Each encodes faster
   ```

---

### Problem: "Encoding fails mid-process"

**Meaning:** Encoding starts but error occurs partway.

**Causes:**
- Out of memory
- Disk space full
- Network interruption
- Server crash

**Solutions:**

1. **Check free disk space:**
   ```bash
   # Windows
   dir C:
   
   # Mac/Linux
   df -h
   
   Need: At least 3× image size free
   ```

2. **Check available memory:**
   ```
   Windows: Ctrl+Shift+Esc → Task Manager
   Mac: Activity Monitor
   Linux: free -h
   
   Need: 2GB minimum free RAM
   ```

3. **Reduce image size:**
   ```
   Current: 4000×3000 image
   Try: 2000×1500 (1/4 size)
   Or: 1600×1200 (smaller)
   ```

4. **Disable double encryption:**
   ```
   Double encryption processes data twice
   Can cause memory issues on old hardware
   ```

5. **Restart service:**
   ```bash
   # Restart Flask server
   # If encoding still fails, server might be broken
   ```

---

## Decoding Problems

### Problem: "No message found in image"

**Meaning:** Decoding succeeds but message is empty.

**Causes:**
- Image doesn't contain hidden message
- Message was deleted/expired
- Image is corrupted
- Wrong decoding method

**Solutions:**

1. **Verify correct image:**
   ```
   Decoding: received_image.png
   Question: Is this the stego image (with hidden message)?
   
   If no → Get correct stego image
   If yes → Image might not contain message
   ```

2. **Check if message expired:**
   ```
   If TTL enabled:
   Encoded: 2024-04-28 10:00 AM
   TTL: 1 hour
   Expires: 2024-04-28 11:00 AM
   
   Current time: 2024-04-28 11:30 AM
   Status: Message expired
   ```

3. **Verify image integrity:**
   ```
   Image might be:
   - Edited/cropped
   - Resized
   - Recompressed
   - Corrupted in transit
   
   Solution: Use backup copy
   ```

4. **Use correct decode mode:**
   ```
   Single message: Use DECODE
   Multiple files: Use DECODE BATCH
   Split across images: Use DECODE SPLIT
   ```

---

### Problem: "Can't extract batch files"

**Meaning:** Batch decode works but ZIP is corrupted.

**Causes:**
- Image is edited
- Multiple images mismatch
- Compression failed
- Network error during download

**Solutions:**

1. **Verify all images:**
   ```
   Batch split across 4 images:
   - Have all 4 images?
   - All original (not edited)?
   - All same resolution?
   - All with same password?
   ```

2. **Try single image:**
   ```
   If one image is corrupted:
   Split mode = encrypted separately
   Try decoding each image alone
   May recover partial data
   ```

3. **Check ZIP integrity:**
   ```bash
   # Test ZIP file
   unzip -t extracted.zip
   
   If error: ZIP is corrupted
   If OK: ZIP is fine but extraction failed
   ```

4. **Use different ZIP tool:**
   ```
   Try: 7-Zip (supports more formats)
   Try: WinRAR (comprehensive)
   Try: Linux command line
   
   Different tools might extract successfully
   ```

---

## Performance Issues

### Problem: "Service degraded" error

**Meaning:** Server is overloaded or unhealthy.

**Causes:**
- Too many simultaneous requests
- Large file processing
- Memory pressure
- CPU at capacity

**Solutions:**

1. **Wait and retry:**
   ```
   Service degrades temporarily
   Wait 30-60 seconds
   Retry operation
   Should recover
   ```

2. **Check server health:**
   ```bash
   curl http://127.0.0.1:5000/api/v1/health
   
   If unhealthy: Server needs restart
   ```

3. **Reduce load:**
   ```
   Stop other encoding operations
   Clear browser cache
   Restart Flask service
   Try smaller files
   ```

4. **Monitor resources:**
   ```bash
   # Check CPU
   top (Linux) or Task Manager (Windows)
   
   # Check memory
   free -h (Linux) or Task Manager (Windows)
   
   # Check disk
   df -h (Linux) or dir (Windows)
   ```

---

### Problem: "Memory usage keeps growing"

**Meaning:** StegoForge uses more memory over time.

**Causes:**
- Cache not cleared
- Session history grows unbounded
- Memory leak in service
- Too many operations

**Solutions:**

1. **Clear browser cache:**
   ```
   Chrome: Ctrl+Shift+Delete
   Firefox: Ctrl+Shift+Delete
   Safari: Cmd+Option+E
   ```

2. **Clear session history:**
   ```
   Click ⚙️ Settings
   Find "Session History"
   Click "Clear History"
   ```

3. **Restart Flask service:**
   ```bash
   # Stop: Ctrl+C in terminal
   # Start: python app.py
   
   This clears all memory
   ```

4. **Monitor memory:**
   ```bash
   # Real-time monitoring
   # Linux: watch free -h
   # Windows: Task Manager → Memory tab
   
   If growing continuously: Memory leak
   ```

---

## Security Features Troubleshooting

### Problem: "Message self-destructed unexpectedly"

**Meaning:** Could decode before but now can't.

**Causes:**
- TTL expired (time passed)
- Max attempts exceeded
- Self-destruct activated
- Image edited

**Solutions:**

1. **Check timing:**
   ```
   TTL enabled: Yes
   TTL seconds: 3600 (1 hour)
   Encoded at: 2024-04-28 10:00
   Expires: 2024-04-28 11:00
   
   If current time > 11:00 → Message expired
   ```

2. **Check attempt counter:**
   ```
   Max attempts: 3
   Failed attempts: 3
   
   After 3 wrong passwords → Image locked forever
   ```

3. **Request fresh copy:**
   ```
   If TTL expired:
   - Ask sender for new encoding
   - Encoding with longer TTL
   
   If attempts exceeded:
   - Ask sender for new encoding
   - No way to recover original
   ```

---

### Problem: "Decoy message showing instead of real"

**Meaning:** Extracting but getting wrong message.

**Causes:**
- Using decoy password instead of real password
- Confusion about which is which

**Solutions:**

1. **Verify which password:**
   ```
   Received password from friend:
   - Real password? (gets real message)
   - Decoy password? (gets decoy message)
   
   Ask sender which is which
   ```

2. **Understand decoy purpose:**
   ```
   Decoy is intentional confusion:
   - Friend might give you decoy password first
   - You use it, get decoy message
   - Friend later gives real password
   - You use it, get real message
   
   OR
   
   - Real password hidden
   - Decoy password obvious
   - Anyone guessing gets decoy
   ```

---

## Advanced Troubleshooting

### Problem: "API returns error code I don't recognize"

**Meaning:** Getting error code not in documentation.

**Solution:**

1. **Check HTTP status code:**
   ```
   200 = Success
   400 = Bad request (validation error)
   403 = Forbidden (authentication/permission)
   429 = Too many requests (rate limit)
   500 = Server error
   503 = Service unavailable
   ```

2. **Look at error message:**
   ```json
   {
     "error": "Detailed description here",
     "error_code": "SPECIFIC_ERROR_CODE"
   }
   ```

3. **Check against API reference:**
   - See API_REFERENCE.md
   - Search for error_code
   - Look at cause and solution

4. **Enable debugging:**
   ```javascript
   // In browser console:
   // Show full response
   fetch('http://127.0.0.1:5000/api/v1/encode', {...})
   .then(r => r.json())
   .then(d => console.log(JSON.stringify(d, null, 2)))
   ```

---

### Problem: "Network errors / Connection refused"

**Meaning:** Can't connect to StegoForge service.

**Causes:**
- Flask not running
- Wrong URL/port
- Firewall blocking
- Network issues

**Solutions:**

1. **Check Flask is running:**
   ```bash
   # If you see:
   # * Running on http://127.0.0.1:5000/
   # → Flask is running
   
   # If terminal closed:
   # Start with: python app.py
   ```

2. **Check correct URL:**
   ```
   ✅ Correct: http://127.0.0.1:5000/
   ✅ Correct: http://localhost:5000/
   ❌ Wrong: http://127.0.0.1:5001/
   ❌ Wrong: https://127.0.0.1:5000/ (HTTPS)
   ```

3. **Check firewall:**
   ```
   Windows Defender Firewall:
   - Inbound rules → Allow Flask/Python
   
   Mac:
   - System Preferences → Security
   - Check firewall settings
   
   Linux:
   - sudo ufw allow 5000/tcp
   ```

4. **Check network:**
   ```bash
   # Test connectivity
   ping 127.0.0.1
   
   # If unreachable: Network issue
   ```

---

### Problem: "Inconsistent results / Different output each time"

**Meaning:** Encoding same data produces different output.

**Causes:**
- Random salts (intentional)
- Encryption uses random initialization vectors
- This is normal security behavior

**Solution:**

1. **Understand why:**
   ```
   StegoForge uses random salts for each encoding
   Same plaintext + password = different ciphertext
   This is GOOD security (prevents pattern analysis)
   
   Message content will always decode identically
   But binary representation will differ
   ```

2. **Verify decoding:**
   ```
   Encode "Hello" with "Password" → File A
   Encode "Hello" with "Password" → File B
   
   File A ≠ File B (different binary)
   
   But:
   Decode File A with "Password" → "Hello" ✅
   Decode File B with "Password" → "Hello" ✅
   
   Content is identical!
   ```

---

## Getting Help

### When to Check Documentation:

1. **Beginner's Guide** - Basic concepts and usage
2. **Quick Start** - Step-by-step examples
3. **API Reference** - Technical specifications
4. **Advanced Guide** - Complex features
5. **This Guide** - Troubleshooting specific issues

### Information to Provide When Seeking Help:

When reporting issues, provide:
```
1. What were you trying to do?
2. What error appeared?
3. What steps led to the error?
4. Image size (dimensions and file size)
5. Message/file size
6. Browser and OS
7. Any error codes or messages
8. When did it last work?
```

### Quick Diagnostic Checklist:

- [ ] Flask is running (`python app.py`)
- [ ] Using correct URL (http://127.0.0.1:5000/)
- [ ] Image is valid (PNG, JPEG, BMP)
- [ ] Message is under 10,000 characters
- [ ] Password is entered exactly same for decode
- [ ] No rate limiting (waited 60 seconds if needed)
- [ ] Try in different browser
- [ ] Try with small test image
- [ ] Check server health (/api/v1/health)

---

**Troubleshooting Guide Version:** 4.0.0  
**Last Updated:** 2024  
**Covers:** 30+ Common Issues
