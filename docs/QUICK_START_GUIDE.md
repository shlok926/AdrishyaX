# StegoForge v4 - Quick Start Guide

## 5-Minute Quick Start

Get up and running with StegoForge in 5 minutes!

---

## Scenario 1: Hide a Text Message (2 minutes)

### Goal
Hide the text "Meet at the cafe at 5pm" in a photo

### Steps

1. **Open StegoForge**
   - Go to: http://127.0.0.1:5000/
   - Click the main interface

2. **Upload an Image**
   - Click "📤 UPLOAD CARRIER"
   - Choose a photo (PNG or JPEG works best)
   - The image is displayed

3. **Enter Your Message**
   - Click the Message text box
   - Type: `Meet at the cafe at 5pm`

4. **Set a Password**
   - Click the Password field
   - Type: `CafeSecret123` (or any password you choose)

5. **Encode**
   - Click "🚀 Start Encoding"
   - Wait for processing (usually < 5 seconds)
   - File automatically downloads as `stego_XXXXXX.png`

✅ **Done!** You now have an image with a hidden message.

---

## Scenario 2: Read a Hidden Message (2 minutes)

### Goal
Extract and read a message from a stego image

### Steps

1. **Open StegoForge**
   - Go to: http://127.0.0.1:5000/

2. **Click "🔓 DECODE"**
   - A decode window appears

3. **Select the Stego Image**
   - Click "📁 SELECT IMAGE"
   - Choose the image from Scenario 1

4. **Enter the Password**
   - Type the password: `CafeSecret123`

5. **Extract Message**
   - Click "🔓 Extract Message"
   - The hidden message appears
   - You can copy it or save it

✅ **Done!** You extracted the hidden message.

---

## Scenario 3: Hide Multiple Files (3 minutes)

### Goal
Hide 3 files (document, photo, spreadsheet) in one image

### Steps

1. **Open StegoForge**
   - Go to: http://127.0.0.1:5000/

2. **Switch to Batch Mode**
   - Click the "📦 BATCH" tab/button
   - Or select "Batch Encoding" from menu

3. **Upload Files**
   - Click "📁 ADD FILES"
   - Select multiple files:
     - `document.pdf`
     - `photo.jpg`
     - `spreadsheet.xlsx`
   - Files are shown in a list

4. **Select Carrier Image**
   - Click "📤 UPLOAD CARRIER"
   - Choose a large image (1600×1200 or larger)

5. **Set Encryption**
   - Password: `FileSecret456`
   - Compression: `ZIP` (default)
   - AES Bits: `256` (default)

6. **Encode**
   - Click "🚀 Start Batch Encoding"
   - System compresses and embeds all files
   - File downloads as `stego_batch_XXXXXX.png`

✅ **Done!** All files are hidden in one image.

---

## Scenario 4: Decode Batch Files (2 minutes)

### Goal
Extract the 3 files from the batch-encoded image

### Steps

1. **Open StegoForge**
2. **Click "🔓 DECODE"**
3. **Select Image Type: BATCH**
   - Click on "Batch Decoding" if available
   - Or let it auto-detect

4. **Upload the Stego Image**
   - Click "📁 SELECT IMAGE"
   - Choose `stego_batch_XXXXXX.png`

5. **Enter Password**
   - Type: `FileSecret456`

6. **Extract Files**
   - Click "🔓 Extract Files"
   - A ZIP file automatically downloads
   - Extract the ZIP to get all 3 files

✅ **Done!** All files recovered!

---

## Scenario 5: Advanced Security (3 minutes)

### Goal
Encode a message with extra security (double encryption + expiry)

### Steps

1. **Open StegoForge**
2. **Upload image and enter message** (normal steps)
3. **Click "⚡ Advanced Options"**

4. **Enable Security Features**
   - ☑️ "Double Encryption" → ON
   - ☑️ "Message Expiry" → ON
   - Set "TTL Seconds" to: `3600` (1 hour)
   - ☑️ "Self-Destruct" → ON
   - Set "Max Attempts" to: `3`

5. **Optionally: Add Decoy Message**
   - If advanced options expanded, fill:
   - "Decoy Password": `WrongPassword123`
   - "Decoy Message": `You guessed wrong!`

6. **Encode**
   - Click "🚀 Start Encoding"
   - Image downloads

### Result:
- Message encrypted **twice** (AES-256 each)
- Message expires in 1 hour
- After 3 failed password attempts, message self-destructs
- If wrong password entered, shows decoy message

✅ **Maximum SECURITY!**

---

## Scenario 6: Check Image Capacity (1 minute)

### Goal
Check how much data an image can hold

### Steps

1. **Open StegoForge**
2. **Click "📊 ANALYTICS"** or **"⚙️ SETTINGS"**
3. **Find "Capacity Check" or "Image Info"**
4. **Upload an Image**
   - Click "📁 SELECT IMAGE"
   - Choose the image

5. **View Capacity**
   - Shows: **Capacity: 125 KB**
   - Shows: **Can hold X files**
   - Shows: **Recommended compression**

✅ **Now you know max file size!**

---

## Command-Line Examples

### Using cURL (Linux/Mac/Windows)

#### Hide a Message
```bash
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@myimage.png" \
  -F "message=Secret text here" \
  -F "password=MyPassword123" \
  -F "aes_bits=256" \
  --output stego_output.png

echo "Done! Check stego_output.png"
```

#### Extract a Message
```bash
curl -X POST http://127.0.0.1:5000/api/v1/decode \
  -F "image=@stego_output.png" \
  -F "password=MyPassword123"

# Output shows: {"success": true, "message": "Secret text here"}
```

#### Check Capacity
```bash
curl -X POST http://127.0.0.1:5000/api/v1/capacity-check \
  -F "image=@myimage.png"

# Output shows: {"capacity_bytes": 125000, "utilization_percent": 10}
```

---

## Python Examples

### Simple Encoding
```python
import requests

# Define API endpoint
url = "http://127.0.0.1:5000/api/v1/encode"

# Prepare files and data
files = {'image': open('carrier.png', 'rb')}
data = {
    'message': 'Secret message',
    'password': 'MyPassword123',
    'aes_bits': '256'
}

# Send request
response = requests.post(url, files=files, data=data)

# Save result
if response.status_code == 200:
    with open('stego.png', 'wb') as f:
        f.write(response.content)
    print("✅ Encoding successful!")
else:
    print(f"❌ Error: {response.json()['error']}")
```

### Simple Decoding
```python
import requests

url = "http://127.0.0.1:5000/api/v1/decode"

files = {'image': open('stego.png', 'rb')}
data = {'password': 'MyPassword123'}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Message: {result['message']}")
else:
    print(f"❌ Error: {response.json()['error']}")
```

---

## JavaScript Examples

### Encoding in Browser
```javascript
async function hideMessage() {
    const formData = new FormData();
    
    // Get file from input
    const imageFile = document.getElementById('imageInput').files[0];
    formData.append('image', imageFile);
    
    // Get message and password
    formData.append('message', 'Secret message');
    formData.append('password', 'MyPassword123');
    formData.append('aes_bits', '256');
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/encode', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            downloadFile(blob, 'stego.png');
            console.log('✅ Encoding successful!');
        } else {
            const error = await response.json();
            console.error('❌ Error:', error.error);
        }
    } catch (err) {
        console.error('Request failed:', err);
    }
}

function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}
```

### Decoding in Browser
```javascript
async function extractMessage() {
    const formData = new FormData();
    
    // Get stego image
    const imageFile = document.getElementById('stegoInput').files[0];
    formData.append('image', imageFile);
    
    // Get password
    formData.append('password', 'MyPassword123');
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/decode', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('output').textContent = data.message;
            console.log('✅ Decoding successful!');
        } else {
            const error = await response.json();
            console.error('❌ Error:', error.error);
        }
    } catch (err) {
        console.error('Request failed:', err);
    }
}
```

---

## Common Workflows

### Workflow 1: Secure Communication
```
1. Alice creates message
2. Alice encodes into image with password
3. Alice sends image via email/social media
4. Bob downloads image
5. Bob decodes with password
6. Bob reads message
   
✅ No one else can read the message!
```

### Workflow 2: Backup Sensitive Files
```
1. Zip important files
2. Encode ZIP into a seemingly innocent image
3. Store image in cloud or on USB
4. When needed, decode and extract files
   
✅ Files hidden in plain sight!
```

### Workflow 3: Add Watermark to Photos
```
1. Take high-quality photo
2. Encode copyright info into photo
3. Share photo publicly
4. Only you can decode to verify ownership
   
✅ Invisible watermark!
```

---

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| "Image required" | Make sure image is selected |
| "Message too long" | Use BATCH mode for large content |
| "Image too small" | Use a bigger image or split across multiple images |
| "Wrong password" | Check password (case-sensitive) |
| "Rate limit" | Wait 60 seconds and try again |
| "Image won't open" | Make sure download completed, try different viewer |

---

## Tips & Tricks

💡 **Large Messages?** → Use BATCH mode + compression  
💡 **Extra Secure?** → Enable double encryption + expiry  
💡 **Sharing?** → Use decoy password for extra plausible deniability  
💡 **Checking Capacity?** → Use capacity-check before encoding  
💡 **Multiple Files?** → Always use BATCH mode (auto-compresses)  
💡 **Long Term?** → Backup images in secure cloud storage  

---

## What's Next?

- **Read the Beginner's Guide** for concepts and features
- **Check API Reference** for advanced integration
- **Explore Advanced Features** for encryption options
- **See Examples** for code in your language

---

**Quick Start Guide Version:** 4.0.0  
**Last Updated:** 2024  
**Time to First Success:** ~5 minutes
