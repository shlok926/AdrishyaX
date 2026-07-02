# StegoForge v4 - Extended Code Examples

## Comprehensive Code Examples for Integration

This file contains detailed, production-ready code examples for integrating StegoForge into applications.

---

## Table of Contents
1. [Python Examples](#python-examples)
2. [JavaScript/Node.js Examples](#javascriptnode-examples)
3. [cURL/Shell Examples](#curlshell-examples)
4. [Complete Workflows](#complete-workflows)
5. [Error Handling Patterns](#error-handling-patterns)

---

## Python Examples

### Basic Encoding with Requests

```python
import requests
import os

def encode_message(image_path, message, password, output_path='stego.png'):
    """
    Basic message encoding into image.
    
    Args:
        image_path: Path to carrier image
        message: Secret message to hide
        password: Encryption password
        output_path: Where to save stego image
    
    Returns:
        dict: Response with status information
    """
    url = "http://127.0.0.1:5000/api/v1/encode"
    
    with open(image_path, 'rb') as img_file:
        files = {'image': img_file}
        data = {
            'message': message,
            'password': password,
            'aes_bits': '256'
        }
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return {
            'success': True,
            'output_file': output_path,
            'file_size': os.path.getsize(output_path)
        }
    else:
        error = response.json()
        return {
            'success': False,
            'error': error.get('error'),
            'error_code': error.get('error_code')
        }


# Usage
result = encode_message(
    'carrier.png',
    'Meet me at the cafe at 5pm',
    'SecurePassword123'
)

if result['success']:
    print(f"✅ Encoded successfully: {result['output_file']}")
    print(f"   File size: {result['file_size']} bytes")
else:
    print(f"❌ Error: {result['error']}")
```

### Advanced Encoding with Double Encryption

```python
import requests
from typing import Optional

def encode_secure_message(
    image_path: str,
    message: str,
    password: str,
    double_encrypt: bool = True,
    self_destruct: bool = False,
    ttl_seconds: int = 3600,
    max_attempts: Optional[int] = None,
    decoy_password: Optional[str] = None,
    decoy_message: Optional[str] = None,
    output_path: str = 'stego_secure.png'
) -> dict:
    """
    Encode with advanced security options.
    
    Args:
        image_path: Carrier image
        message: Secret message
        password: Encryption password
        double_encrypt: Apply double AES-256 encryption
        self_destruct: Enable message expiry and max attempts
        ttl_seconds: Time to live in seconds
        max_attempts: Max failed decode attempts (None = unlimited)
        decoy_password: Decoy password for wrong attempts
        decoy_message: Message shown for wrong password
        output_path: Output file path
    
    Returns:
        dict: Status and result information
    """
    url = "http://127.0.0.1:5000/api/v1/encode"
    
    with open(image_path, 'rb') as img_file:
        files = {'image': img_file}
        data = {
            'message': message,
            'password': password,
            'aes_bits': '256',
            'double_encrypt': str(double_encrypt).lower(),
        }
        
        if self_destruct:
            data['self_destruct'] = 'true'
            data['ttl_seconds'] = str(ttl_seconds)
            if max_attempts:
                data['max_attempts'] = str(max_attempts)
        
        if decoy_password:
            data['decoy_password'] = decoy_password
        
        if decoy_message:
            data['decoy_message'] = decoy_message
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return {
            'success': True,
            'output_file': output_path,
            'security': {
                'double_encrypted': double_encrypt,
                'expires_in_seconds': ttl_seconds if self_destruct else None,
                'max_attempts': max_attempts if self_destruct else None,
                'has_decoy': bool(decoy_password)
            }
        }
    else:
        return {'success': False, 'error': response.json()}


# Usage: Maximum security
result = encode_secure_message(
    'carrier.png',
    'CLASSIFIED: Project Alpha Launch Date: May 15',
    'UltraSecurePass123!@#$',
    double_encrypt=True,
    self_destruct=True,
    ttl_seconds=3600,  # 1 hour
    max_attempts=3,
    decoy_password='TryThisPassword',
    decoy_message='Just a cat photo!'
)

print(f"Encoded with security: {result['security']}")
```

### Batch File Encoding

```python
import requests
import os
from pathlib import Path

def encode_batch_files(
    image_path: str,
    files_to_embed: list,
    password: str,
    compression: str = 'zip',
    output_path: str = 'stego_batch.png'
) -> dict:
    """
    Encode multiple files into single image.
    
    Args:
        image_path: Carrier image path
        files_to_embed: List of file paths to embed
        password: Encryption password
        compression: 'zip' or '7z'
        output_path: Output stego image path
    
    Returns:
        dict: Encoding result
    """
    url = "http://127.0.0.1:5000/api/v1/encode-batch"
    
    # Prepare files
    files = {}
    
    # Add carrier image
    files['image'] = open(image_path, 'rb')
    
    # Add payload files
    for file_path in files_to_embed:
        files[f'files'] = open(file_path, 'rb')
    
    # Add data
    data = {
        'password': password,
        'compression_method': compression,
        'aes_bits': '256'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return {
                'success': True,
                'output_file': output_path,
                'files_embedded': len(files_to_embed),
                'compression': compression
            }
        else:
            return {'success': False, 'error': response.json()}
    
    finally:
        # Close all file handles
        for file_obj in files.values():
            if hasattr(file_obj, 'close'):
                file_obj.close()


# Usage
files_to_hide = ['document.pdf', 'spreadsheet.xlsx', 'photo.jpg']
result = encode_batch_files(
    'large_carrier.png',
    files_to_hide,
    'BatchPassword123',
    compression='7z'
)

print(f"Embedded {result['files_embedded']} files with {result['compression']} compression")
```

### Decoding with Error Handling

```python
import requests
from typing import Tuple

def decode_message(
    stego_image_path: str,
    password: str,
    timeout: int = 30
) -> Tuple[bool, str]:
    """
    Extract and decrypt message from stego image.
    
    Args:
        stego_image_path: Path to stego image
        password: Decryption password
        timeout: Request timeout in seconds
    
    Returns:
        (success: bool, message_or_error: str)
    """
    url = "http://127.0.0.1:5000/api/v1/decode"
    
    with open(stego_image_path, 'rb') as img_file:
        files = {'image': img_file}
        data = {'password': password}
        
        try:
            response = requests.post(url, files=files, data=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                return True, message
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                error_code = error_data.get('error_code', 'UNKNOWN')
                return False, f"{error_code}: {error_msg}"
        
        except requests.Timeout:
            return False, "Request timeout - try again"
        except requests.ConnectionError:
            return False, "Connection error - Flask not running?"
        except Exception as e:
            return False, f"Error: {str(e)}"


# Usage with error handling
success, result = decode_message('stego.png', 'MyPassword123')

if success:
    print(f"✅ Message extracted: {result}")
else:
    print(f"❌ {result}")
```

### Batch Decoding

```python
import requests
import zipfile
import os

def decode_batch_files(
    stego_image_path: str,
    password: str,
    extract_to: str = 'extracted_files'
) -> dict:
    """
    Extract multiple files from batch-encoded image.
    
    Args:
        stego_image_path: Path to batch stego image
        password: Decryption password
        extract_to: Directory to extract files
    
    Returns:
        dict: Extraction result
    """
    url = "http://127.0.0.1:5000/api/v1/decode-batch"
    
    with open(stego_image_path, 'rb') as img_file:
        files = {'image': img_file}
        data = {'password': password}
        
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        # Save ZIP to temp file
        zip_path = 'temp_extract.zip'
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract ZIP
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_to)
        
        # Get file listing
        extracted_files = []
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file != 'manifest.json':
                    extracted_files.append(os.path.join(root, file))
        
        # Clean up temp file
        os.remove(zip_path)
        
        return {
            'success': True,
            'extract_directory': extract_to,
            'files_extracted': extracted_files,
            'count': len(extracted_files)
        }
    else:
        return {'success': False, 'error': response.json()}


# Usage
result = decode_batch_files('stego_batch.png', 'BatchPassword123')

if result['success']:
    print(f"✅ Extracted {result['count']} files to {result['extract_directory']}")
    for file in result['files_extracted']:
        print(f"   - {file}")
```

---

## JavaScript/Node.js Examples

### Browser-Based Encoding

```javascript
/**
 * Hide message in image using browser Fetch API
 */
async function hideMessageInImage() {
    // Get form inputs
    const imageInput = document.getElementById('imageInput');
    const messageInput = document.getElementById('messageInput');
    const passwordInput = document.getElementById('passwordInput');
    
    const image = imageInput.files[0];
    const message = messageInput.value;
    const password = passwordInput.value;
    
    // Validate
    if (!image) {
        alert('Please select an image');
        return;
    }
    
    if (!message || !password) {
        alert('Please enter message and password');
        return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('image', image);
    formData.append('message', message);
    formData.append('password', password);
    formData.append('aes_bits', '256');
    
    // Show loading
    document.getElementById('status').textContent = 'Encoding...';
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/encode', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Encoding failed');
        }
        
        // Download stego image
        const blob = await response.blob();
        downloadFile(blob, 'stego_image.png');
        
        document.getElementById('status').textContent = '✅ Encoded successfully!';
    } catch (error) {
        document.getElementById('status').textContent = `❌ Error: ${error.message}`;
        console.error('Encoding error:', error);
    }
}

/**
 * Download blob as file
 */
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}
```

### Browser-Based Decoding

```javascript
/**
 * Extract message from stego image
 */
async function extractMessageFromImage() {
    const stegoInput = document.getElementById('stegoInput');
    const passwordInput = document.getElementById('passwordInput');
    
    const stego = stegoInput.files[0];
    const password = passwordInput.value;
    
    if (!stego || !password) {
        alert('Please select image and enter password');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', stego);
    formData.append('password', password);
    
    document.getElementById('output').textContent = 'Extracting...';
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/decode', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('output').textContent = data.message;
            document.getElementById('output').style.color = '#44ff44';
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        document.getElementById('output').textContent = `Error: ${error.message}`;
        document.getElementById('output').style.color = '#ff6464';
    }
}
```

### Node.js Server Example

```javascript
// server.js - Express.js integration

const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

const app = express();
const STEGO_API = 'http://127.0.0.1:5000/api/v1';

/**
 * API Route: POST /api/hide
 * Hide message in image
 */
app.post('/api/hide', async (req, res) => {
    try {
        const { message, password, imageFile } = req.body;
        
        // Validate
        if (!message || !password || !imageFile) {
            return res.status(400).json({
                error: 'Missing required fields'
            });
        }
        
        // Read image file
        const imageBuffer = fs.readFileSync(imageFile);
        
        // Prepare form data
        const form = new FormData();
        form.append('image', imageBuffer, 'image.png');
        form.append('message', message);
        form.append('password', password);
        form.append('aes_bits', '256');
        
        // Call StegoForge API
        const response = await axios.post(`${STEGO_API}/encode`, form, {
            headers: form.getHeaders(),
            responseType: 'arraybuffer',
            timeout: 30000
        });
        
        // Save stego image
        const outputPath = path.join(__dirname, 'stego_output.png');
        fs.writeFileSync(outputPath, response.data);
        
        res.json({
            success: true,
            stego_image: outputPath,
            size: response.data.length
        });
    } catch (error) {
        res.status(500).json({
            error: error.message
        });
    }
});

/**
 * API Route: POST /api/extract
 * Extract message from image
 */
app.post('/api/extract', async (req, res) => {
    try {
        const { password, imageFile } = req.body;
        
        if (!password || !imageFile) {
            return res.status(400).json({
                error: 'Missing required fields'
            });
        }
        
        // Read image
        const imageBuffer = fs.readFileSync(imageFile);
        
        // Prepare form data
        const form = new FormData();
        form.append('image', imageBuffer, 'image.png');
        form.append('password', password);
        
        // Call API
        const response = await axios.post(`${STEGO_API}/decode`, form, {
            headers: form.getHeaders(),
            timeout: 30000
        });
        
        res.json({
            success: true,
            message: response.data.message
        });
    } catch (error) {
        const errorCode = error.response?.data?.error_code || 'UNKNOWN';
        const errorMsg = error.response?.data?.error || error.message;
        
        res.status(error.response?.status || 500).json({
            error: errorMsg,
            error_code: errorCode
        });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

---

## cURL/Shell Examples

### Basic Encoding

```bash
#!/bin/bash

# Hide message in image
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=Secret message here" \
  -F "password=MySecurePassword123" \
  -F "aes_bits=256" \
  --output stego_image.png

echo "✅ Stego image saved: stego_image.png"
```

### Advanced Encoding

```bash
#!/bin/bash

# Encode with maximum security
curl -X POST http://127.0.0.1:5000/api/v1/encode \
  -F "image=@carrier.png" \
  -F "message=TOP SECRET INFORMATION" \
  -F "password=SuperSecurePassword123!@#" \
  -F "double_encrypt=true" \
  -F "self_destruct=true" \
  -F "ttl_seconds=3600" \
  -F "max_attempts=3" \
  -F "decoy_password=FakePassword123" \
  -F "decoy_message=Just a nice photo" \
  -F "aes_bits=256" \
  -F "remove_exif=true" \
  --output stego_secure.png

echo "✅ Securely encoded image: stego_secure.png"
```

### Batch Encoding

```bash
#!/bin/bash

# Hide multiple files in image
curl -X POST http://127.0.0.1:5000/api/v1/encode-batch \
  -F "image=@large_carrier.png" \
  -F "files=@document.pdf" \
  -F "files=@spreadsheet.xlsx" \
  -F "files=@photo.jpg" \
  -F "password=BatchPassword123" \
  -F "compression_method=7z" \
  -F "aes_bits=256" \
  --output stego_batch.png

echo "✅ Batch encoded image: stego_batch.png"
```

### Decoding

```bash
#!/bin/bash

# Extract message
curl -X POST http://127.0.0.1:5000/api/v1/decode \
  -F "image=@stego_image.png" \
  -F "password=MySecurePassword123"

# Output:
# {"success": true, "message": "Secret message here"}
```

### Capacity Check

```bash
#!/bin/bash

# Check image capacity
curl -X POST http://127.0.0.1:5000/api/v1/capacity-check \
  -F "image=@carrier.png" \
  | python -m json.tool

# Output shows capacity details
```

### Health Check

```bash
#!/bin/bash

# Check service health
curl http://127.0.0.1:5000/api/v1/health | python -m json.tool
```

---

## Complete Workflows

### Workflow 1: Secure Communication Pipeline

```python
"""
Alice → Bob Secure Communication Workflow
"""

from typing import Tuple
import requests

class SecureCommunication:
    def __init__(self, api_url: str = "http://127.0.0.1:5000/api/v1"):
        self.api_url = api_url
    
    def alice_sends_message(
        self,
        carrier_image: str,
        secret_message: str,
        shared_password: str
    ) -> Tuple[bool, str]:
        """
        Alice encodes and sends message to Bob
        """
        url = f"{self.api_url}/encode"
        
        with open(carrier_image, 'rb') as f:
            files = {'image': f}
            data = {
                'message': secret_message,
                'password': shared_password,
                'aes_bits': '256',
                'double_encrypt': 'true',
                'self_destruct': 'true',
                'ttl_seconds': '86400'  # 24 hours
            }
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            output_file = 'alice_to_bob.png'
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True, output_file
        else:
            error = response.json()
            return False, error['error']
    
    def bob_receives_message(
        self,
        stego_image: str,
        shared_password: str
    ) -> Tuple[bool, str]:
        """
        Bob extracts message from Alice's image
        """
        url = f"{self.api_url}/decode"
        
        with open(stego_image, 'rb') as f:
            files = {'image': f}
            data = {'password': shared_password}
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            return True, result['message']
        else:
            error = response.json()
            return False, error['error']


# Usage
comm = SecureCommunication()

# Alice's side
success, stego_file = comm.alice_sends_message(
    'vacation_photo.png',
    'Meeting location: The Coffee House, 5pm',
    'shared_secure_password_123'
)

if success:
    print(f"Alice: Message hidden in {stego_file}")
    # Alice sends stego_file to Bob via email/upload

# Bob's side (later)
success, message = comm.bob_receives_message(
    'alice_to_bob.png',
    'shared_secure_password_123'
)

if success:
    print(f"Bob: Received message: {message}")
```

### Workflow 2: Automated Backup Pipeline

```python
"""
Automated backup of sensitive files into images
"""

import os
import glob
from datetime import datetime

class BackupPipeline:
    def __init__(self, backup_password: str, api_url: str = "http://127.0.0.1:5000/api/v1"):
        self.backup_password = backup_password
        self.api_url = api_url
    
    def backup_files(
        self,
        files_to_backup: list,
        carrier_image: str,
        backup_name: str = None
    ) -> dict:
        """
        Backup files by embedding into carrier image
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        url = f"{self.api_url}/encode-batch"
        
        files = {'image': open(carrier_image, 'rb')}
        data = {
            'password': self.backup_password,
            'compression_method': '7z',
            'aes_bits': '256',
            'double_encrypt': 'true'
        }
        
        # Add files to backup
        for file_path in files_to_backup:
            files['files'] = open(file_path, 'rb')
        
        try:
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                with open(backup_name, 'wb') as f:
                    f.write(response.content)
                
                return {
                    'success': True,
                    'backup_file': backup_name,
                    'files_backed_up': len(files_to_backup)
                }
            else:
                return {
                    'success': False,
                    'error': response.json()
                }
        finally:
            for f in files.values():
                if hasattr(f, 'close'):
                    f.close()
    
    def restore_files(
        self,
        backup_image: str,
        restore_dir: str = 'restored_files'
    ) -> dict:
        """
        Restore files from backup image
        """
        url = f"{self.api_url}/decode-batch"
        
        with open(backup_image, 'rb') as f:
            files = {'image': f}
            data = {'password': self.backup_password}
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            os.makedirs(restore_dir, exist_ok=True)
            
            import zipfile
            zip_path = 'temp_restore.zip'
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(restore_dir)
            
            os.remove(zip_path)
            
            return {
                'success': True,
                'restore_directory': restore_dir
            }
        else:
            return {
                'success': False,
                'error': response.json()
            }


# Usage
backup = BackupPipeline("secure_backup_password_123")

# Backup important files
files = ['confidential.docx', 'financial_records.xlsx', 'encryption_keys.txt']
result = backup.backup_files(files, 'large_scenic_photo.png')

if result['success']:
    print(f"✅ Backed up {result['files_backed_up']} files to {result['backup_file']}")
    # Store backup_file safely

# Later: Restore files
restore_result = backup.restore_files('backup_20240428_120000.png')

if restore_result['success']:
    print(f"✅ Files restored to {restore_result['restore_directory']}")
```

---

## Error Handling Patterns

### Retry with Exponential Backoff

```python
import requests
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    """
    Decorator for retrying requests with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.ConnectionError, requests.Timeout) as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"Retry in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
        
        return wrapper
    return decorator


@retry_with_backoff(max_retries=3)
def encode_with_retry(image_path, message, password):
    """Encode with automatic retry"""
    url = "http://127.0.0.1:5000/api/v1/encode"
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'message': message, 'password': password}
        response = requests.post(url, files=files, data=data, timeout=30)
    return response
```

### Comprehensive Error Handler

```python
class StegoForgeClient:
    def __init__(self, api_url="http://127.0.0.1:5000"):
        self.api_url = api_url
    
    def _handle_response(self, response):
        """
        Centralized error handling
        """
        if response.status_code == 200:
            return True, response
        
        # Handle different error codes
        error_data = response.json()
        error_code = error_data.get('error_code', 'UNKNOWN')
        error_msg = error_data.get('error', 'Unknown error')
        
        # Map error codes to user-friendly messages
        error_map = {
            'VALIDATION_ERROR': 'Input validation failed. Check message/image.',
            'AUTHENTICATION_ERROR': 'Wrong password.',
            'INSUFFICIENT_CAPACITY': 'Image is too small for this data.',
            'RATE_LIMIT_EXCEEDED': 'Too many requests. Wait a minute.',
            'MESSAGE_EXPIRED': 'Message has expired.',
            'SELF_DESTRUCT_ACTIVATED': 'Message self-destructed after max attempts.'
        }
        
        user_message = error_map.get(error_code, error_msg)
        return False, f"{error_code}: {user_message}"
    
    def encode(self, image_path, message, password):
        """Encode with error handling"""
        try:
            url = f"{self.api_url}/api/v1/encode"
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'message': message, 'password': password}
                response = requests.post(url, files=files, data=data, timeout=30)
            
            success, result = self._handle_response(response)
            return success, result
        
        except requests.Timeout:
            return False, "Request timeout"
        except requests.ConnectionError:
            return False, "Cannot connect to StegoForge service"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
```

---

**Extended Code Examples Version:** 4.0.0  
**Last Updated:** 2024  
**Languages:** Python, JavaScript, Node.js, Shell/cURL
