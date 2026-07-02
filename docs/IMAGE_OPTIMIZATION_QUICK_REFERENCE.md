# Image Optimization Endpoint - Quick Reference

## Endpoint: POST /api/v1/optimize

### Quick Example

```bash
# Analyze an image
curl -X POST http://127.0.0.1:5000/api/v1/optimize \
  -F "image=@carrier.png" | python -m json.tool
```

### JavaScript Example

```javascript
async function analyzeImage(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await fetch('http://127.0.0.1:5000/api/v1/optimize', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  console.log(`Score: ${result.overall_score}`);
  console.log(`Max Payload: ${result.capacity_analysis.max_payload_mb} MB`);
  console.log(`Recommendations:`, result.recommendations);
  
  return result;
}
```

### Python Example

```python
import requests

def analyze_image(image_path):
    """Analyze image for steganography suitability"""
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(
            'http://127.0.0.1:5000/api/v1/optimize',
            files=files
        )
    
    return response.json()

# Usage
result = analyze_image('carrier.png')
print(f"Suitability Score: {result['overall_score']}/100")
if result['overall_score'] >= 80:
    print("✓ Excellent carrier image!")
else:
    print("⚠ Consider using a different image")

# Show recommendations
for rec in result['recommendations'][:3]:
    print(f"  • {rec}")
```

### Node.js Example (using FormData)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function analyzeImage(imagePath) {
  const form = new FormData();
  form.append('image', fs.createReadStream(imagePath));
  
  try {
    const response = await axios.post(
      'http://127.0.0.1:5000/api/v1/optimize',
      form,
      { headers: form.getHeaders() }
    );
    
    return response.data;
  } catch (error) {
    console.error('Analysis failed:', error.response?.data || error.message);
  }
}

// Usage
analyzeImage('carrier.png').then(result => {
  console.log(`Score: ${result.overall_score}/100`);
  console.log(`Max Capacity: ${result.capacity_analysis.max_payload_mb} MB`);
});
```

## Response Fields

### Top-Level Fields
| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Always true if request succeeds |
| `filename` | string | Uploaded image filename |
| `overall_score` | int | 0-100 suitability score |
| `timestamp` | string | ISO 8601 timestamp |

### score_breakdown
| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| `capacity_score` | int | 0-100 | How much data can fit (LSB availability) |
| `quality_score` | int | 0-100 | Visual quality for hiding (entropy, format) |
| `suitability_score` | int | 0-100 | Weighted combination (overall recommendation) |

### metrics
| Field | Type | Description |
|-------|------|-------------|
| `dimensions` | string | "1920x1080" format |
| `width` | int | Image width in pixels |
| `height` | int | Image height in pixels |
| `aspect_ratio` | float | Width/height ratio |
| `entropy` | float | Shannon entropy (0-8), higher = more random |
| `format` | string | PNG, JPEG, BMP, GIF, WEBP |
| `file_size` | int | File size in bytes |
| `file_size_mb` | float | File size in megabytes |
| `color_depth` | int | Bits per pixel (typically 24 or 32) |
| `is_compressed` | bool | Lossy compression detected |

### capacity_analysis
| Field | Type | Description |
|-------|------|-------------|
| `max_payload_bytes` | int | Maximum hidden data in bytes |
| `max_payload_mb` | float | Maximum hidden data in MB |
| `optimal` | bool | True if score > 80 |

### Risk Assessment
| Risk Type | Values | Meaning |
|-----------|--------|---------|
| `compression_risk` | Low/Medium/High | JPEG compression vulnerability |
| `entropy_risk` | Low/Medium/High | Suspicious distribution detection |
| `visibility_risk` | Low/Medium/High | Potential visual artifacts |

## Score Meanings

### Overall Score: 90-100 ✓ Excellent
- Perfect for all use cases
- High embedding capacity
- Natural entropy distribution
- Minimal visibility risk
- **Recommendation:** Use immediately

### Overall Score: 75-89 ✓ Good
- Suitable for most scenarios
- Adequate capacity
- Natural appearance
- **Recommendation:** Safe to use

### Overall Score: 60-74 ⚠ Fair
- Works but with caveats
- Limited capacity
- Potential visual artifacts
- **Recommendation:** Use if necessary

### Overall Score: < 60 ✗ Poor
- Not recommended
- Very limited capacity
- High visibility risk
- **Recommendation:** Choose different image

## Common Patterns

### Find Best Image from Multiple
```python
images = ['img1.png', 'img2.jpg', 'img3.png']
analyses = [analyze_image(img) for img in images]
best = max(analyses, key=lambda x: x['overall_score'])

print(f"Best image: {best['filename']} (score: {best['overall_score']})")
```

### Auto-Configure Based on Score
```python
result = analyze_image('carrier.png')
score = result['overall_score']

config = {
    'aes_bits': 256,
    'remove_exif': True,
    'double_encrypt': score < 75,  # Extra security if risky
    'compression_method': 'zip' if score < 80 else '7z'
}

print(f"Recommended config: {config}")
```

### Check Capacity Before Encoding
```python
import os

result = analyze_image('carrier.png')
file_size = os.path.getsize('secret.txt')
max_payload = result['capacity_analysis']['max_payload_bytes']

if file_size < max_payload:
    print(f"✓ Can fit {file_size} bytes (capacity: {max_payload})")
else:
    print(f"✗ File too large ({file_size} > {max_payload})")
```

## Error Handling

```python
import requests

try:
    response = requests.post(
        'http://127.0.0.1:5000/api/v1/optimize',
        files={'image': open('carrier.png', 'rb')},
        timeout=5
    )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"Score: {result['overall_score']}")
        else:
            print(f"Error: {response.json()['error']}")
    else:
        print(f"HTTP {response.status_code}: {response.text}")
        
except requests.Timeout:
    print("Request timeout - image too large?")
except requests.ConnectionError:
    print("Cannot connect to API server")
except Exception as e:
    print(f"Error: {e}")
```

## Tips & Best Practices

1. **Cache Results:** Analysis takes ~200-500ms, consider caching
2. **Batch Check:** Analyze multiple images before choosing
3. **Check Entropy:** Aim for entropy between 4.0-7.8
4. **Monitor Risks:** Low risk assessment is more secure
5. **Use Recommendations:** Let the API guide your configuration
6. **Test Format:** PNG preserves all data (lossless)
7. **File Size:** Consider file_size_mb in your workflow

## Integration Workflow

```
User selects image
    ↓
Call /api/v1/optimize
    ↓
Display score and recommendations
    ↓
User decides to proceed
    ↓
Call /api/v1/encode (with optimized settings)
    ↓
Success!
```

## Version
- API: 4.0.0
- Last Updated: April 28, 2026
- Status: Production Ready
