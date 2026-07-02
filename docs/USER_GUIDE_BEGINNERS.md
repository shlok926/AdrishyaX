# StegoForge v4 - Beginner's Guide

## Welcome to StegoForge! 🔐

StegoForge is a powerful tool for hiding secret messages inside images. This guide will help you get started with the basics.

---

## Table of Contents
1. [What is Steganography?](#what-is-steganography)
2. [Getting Started](#getting-started)
3. [Basic Encoding](#basic-encoding)
4. [Basic Decoding](#basic-decoding)
5. [Security Features](#security-features)
6. [Common Questions](#common-questions)
7. [Troubleshooting](#troubleshooting)

---

## What is Steganography?

**Steganography** is the art of hiding secret messages inside other files (like images) in a way that no one knows the message exists.

### Example:
- **Normal:** You send a message "Meet me at 5pm" - anyone can see it
- **Steganography:** The same message is hidden inside an innocent-looking photo - only you and the recipient know it's there

### Why Use It?
✅ **Privacy** - Keep your messages private  
✅ **Security** - Hide sensitive information in plain sight  
✅ **Plausible deniability** - The image looks completely normal  
✅ **Not suspicious** - Sharing photos is normal, sharing encrypted files might raise questions  

---

## Getting Started

### Accessing StegoForge

1. **Open your browser**
2. **Go to:** `http://127.0.0.1:5000/`
3. **You'll see the main StegoForge interface**

### The Interface Overview

```
┌─────────────────────────────────────────┐
│        StegoForge v4 ULTIMATE           │
├─────────────────────────────────────────┤
│                                         │
│  [📤 UPLOAD CARRIER]                   │
│                                         │
│  Message: [Text Area]                  │
│  Password: [****]                      │
│                                         │
│  [⚡ Advanced Options]                  │
│  [🚀 Start Encoding]                   │
│                                         │
│  [🔓 DECODE]                           │
│  [📊 ANALYTICS]                        │
│  [⚙️ SETTINGS]                          │
│                                         │
└─────────────────────────────────────────┘
```

---

## Basic Encoding

### Step-by-Step: Hide a Message in an Image

#### **Step 1: Choose Your Carrier Image**
- Click **"📤 UPLOAD CARRIER"**
- Select a PNG, JPEG, or BMP image
- Larger images hold more data
- File size: Any reasonable size (most images work)

**💡 Tip:** Images with complex patterns (natural scenes, photos) work better than solid colors.

#### **Step 2: Enter Your Secret Message**
- Click in the **"Message"** text area
- Type whatever you want to hide
- Max 10,000 characters

**Example message:**
```
Meet me at the cafe at 5pm.
Bring the documents we discussed.
```

#### **Step 3: Set a Password**
- Click in the **"Password"** field
- Enter a strong password (8+ characters)
- This password will be needed to read the message later

**🔒 Password Tips:**
- Use mix of upper, lower, numbers, symbols
- Don't use dictionary words
- Don't share your password with anyone you don't trust
- ✅ Good: `Tr0p1cal-Sunset#42`
- ❌ Bad: `password123`

#### **Step 4: Click "🚀 Start Encoding"**
- The system embeds your message into the image
- A new image file is created and downloaded
- This is your "stego image" (image with hidden message)

#### **Step 5: Share the Image Safely**
- Send the stego image to your recipient
- To anyone else, it looks like a normal photo
- Only someone with the password can read the message

### Simple Encoding Example

```
Carrier Image: photo_of_sunset.jpg (2MB)
Message: "Secret meeting at 3pm"
Password: "MySecretPassword123"
     ↓
[ENCODING PROCESS]
     ↓
Stego Image: stego_image.png (2MB)
(Looks identical to original, but contains hidden message)
```

---

## Basic Decoding

### Step-by-Step: Extract a Hidden Message

#### **Step 1: Get the Stego Image**
- You receive a stego image from someone
- Download it or have it ready

#### **Step 2: Click "🔓 DECODE"**
- A decode window appears
- Click **"📁 SELECT IMAGE"**
- Choose the stego image

#### **Step 3: Enter the Password**
- Enter the password you received with the image
- Must be exactly the same password used for encoding

#### **Step 4: Extract the Message**
- Click **"🔓 Extract Message"**
- The hidden message is revealed
- You can copy or download it

### Decoding Example

```
Stego Image: photo_received_from_alice.png
Password: "MySecretPassword123"
     ↓
[DECODING PROCESS]
     ↓
Message: "Secret meeting at 3pm"
(Successfully extracted!)
```

---

## Security Features

### Password Protection
- Your message is encrypted with **AES-256**
- Without the correct password, the message cannot be read
- Even with the image, no one can access the message without the password

### Multiple Layers of Security

#### **1. Double Encryption** (Optional)
- Encrypts your message **twice** with AES-256
- Extra security for highly sensitive data
- Slightly larger file size
- **Enable:** Check "⚡ Advanced Options" → "Double Encryption"

#### **2. Message Expiry** (Optional)
- Message automatically becomes unreadable after a certain time
- Set time limit (default: 1 hour)
- Perfect for time-sensitive messages
- **Enable:** Check "⚡ Advanced Options" → "Message Expiry"

#### **3. Self-Destruct Protection** (Optional)
- Message destroys itself after N failed decode attempts
- Maximum attempts (e.g., 3 tries)
- Prevents brute-force password guessing
- **Enable:** Check "⚡ Advanced Options" → "Max Attempts"

#### **4. Decoy Message** (Optional)
- Set a different message for wrong passwords
- Wrong password shows decoy instead of error
- Can't tell if they guessed wrong
- **Enable:** Check "⚡ Advanced Options" → "Decoy Message"

---

## Common Questions

### Q: Can I hide files (not just text)?
**A:** Yes! Switch to **"BATCH MODE"** to hide multiple files:
1. Click the **"📦 BATCH"** button
2. Upload multiple files
3. They'll be automatically compressed
4. All files hidden in one image

### Q: What image formats work?
**A:** PNG, JPEG, BMP, GIF, WEBP
- **Best:** PNG (no quality loss)
- **Good:** BMP (raw format)
- **Okay:** JPEG (slight loss)
- **Avoid:** GIFs (complex format)

### Q: How much data can I hide?
**A:** Depends on image size:
- **400x300 (small):** ~40KB
- **800x600 (medium):** ~150KB
- **1600x1200 (large):** ~600KB
- **3200x2400 (very large):** ~2.5MB

**Rough formula:** Image pixels × 0.33 ÷ 8 = max data in bytes

### Q: Is it detectable?
**A:** With StegoForge:
- Visual inspection: **No** (image looks identical)
- Statistical analysis: **Difficult** (encryption randomizes data)
- Steganalysis tools: **Maybe** (depends on tool)

### Q: Can I change the message after encoding?
**A:** No. You must:
1. Encode a new image
2. Or create a new message before encoding

### Q: What if I forget the password?
**A:** The message is **permanently lost**.
- Passwords are one-way
- Even we can't recover it
- Always write down or securely store passwords!

### Q: Can I encode multiple messages in one image?
**A:** No. One image = one message.
- Create separate images for different messages
- Or combine messages before encoding

### Q: What if the image gets corrupted?
**A:** The message is likely lost:
- Image files are fragile
- Keep multiple backups
- Use cloud storage for important images

---

## Troubleshooting

### Problem: "Image file required"
**Solution:**
1. Make sure you selected an image
2. Check file format (PNG, JPEG, BMP)
3. File size should be reasonable (< 100MB)

### Problem: "Message too long"
**Solution:**
1. Maximum 10,000 characters for text
2. For larger data, use BATCH MODE
3. Use compression if available

### Problem: "Invalid password"
**Solution:**
1. Password is case-sensitive
2. Check for extra spaces
3. Verify you're using the correct password
4. Note: After 3 failed attempts, message may self-destruct

### Problem: "Image too small for payload"
**Solution:**
1. Use a larger image (more pixels)
2. Use BATCH MODE with compression
3. Compress your data first (ZIP before uploading)
4. Split message across multiple images

### Problem: "Authentication failed" during decode
**Solution:**
1. Wrong password entered
2. Image is corrupted
3. Image is not a StegoForge-encoded image
4. Message has expired (if expiry enabled)

### Problem: "Rate limit exceeded"
**Solution:**
1. Wait 60 seconds
2. You've made too many requests
3. Try again after the wait

### Problem: Downloaded image won't open
**Solution:**
1. Wait for download to complete
2. Try a different image viewer
3. Check if file is actually an image (right-click → properties)
4. Re-download the stego image

---

## Security Best Practices

### ✅ DO:
- ✅ Use strong passwords (8+ characters, mix of types)
- ✅ Keep passwords secure and private
- ✅ Use double encryption for sensitive data
- ✅ Keep backup copies of important images
- ✅ Enable message expiry for time-sensitive info
- ✅ Use decoy messages for extra security
- ✅ Verify image integrity before using
- ✅ Test with a dummy message first

### ❌ DON'T:
- ❌ Use simple passwords like "password123"
- ❌ Send passwords with the image
- ❌ Share your stego images publicly
- ❌ Store passwords in plain text
- ❌ Assume the image is private (metadata can reveal info)
- ❌ Use the same password for multiple images
- ❌ Encode highly illegal content
- ❌ Test security with actual passwords

---

## Next Steps

Ready to level up? Check out:
- **Advanced Features Guide** - Double encryption, video hiding, ECDH
- **API Documentation** - Integrate StegoForge into your apps
- **Troubleshooting Guide** - Advanced troubleshooting

---

## Need Help?

### Quick Answers
- **Can't encode?** → Check image format and size
- **Can't decode?** → Verify password is correct
- **Message too large?** → Use BATCH MODE
- **Worried about security?** → Use double encryption + expiry

### Still Stuck?
Check the Troubleshooting Guide for more detailed solutions.

---

**Beginner's Guide Version:** 4.0.0  
**Last Updated:** 2024  
**Status:** Ready to Use
