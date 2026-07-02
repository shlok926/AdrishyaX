# Feature #1 Image Optimization - Developer Quick Reference

## Installation & Setup

### Prerequisites
```bash
python 3.10+
pip install pillow numpy scipy scikit-learn
```

### Import the Module

```python
from image_optimizer import ImageOptimizer
```

## Basic Usage

### Single Image Analysis

```python
from image_optimizer import ImageOptimizer

# Create optimizer instance
optimizer = ImageOptimizer()

# Analyze image
score = optimizer.score_image('path/to/image.png')

# Access results
print(f"Overall Score: {score.overall_score}")
print(f"Entropy: {score.entropy}")
print(f"Complexity: {score.complexity}")
print(f"Compression: {score.compression_ratio}%")
print(f"Capacity: {score.capacity_bytes / 1024 / 1024:.2f} MB")
```

### Batch Analysis

```python
from image_optimizer import ImageOptimizer
import os

optimizer = ImageOptimizer()
results = []

for filename in os.listdir('images/'):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
        score = optimizer.score_image(f'images/{filename}')
        if score:
            results.append(score)

# Sort by score (best first)
results.sort(key=lambda x: x.overall_score, reverse=True)

# Display top 5
for i, score in enumerate(results[:5], 1):
    print(f"{i}. {score.filename}: {score.overall_score:.1f}/100")
```

### Get Recommendations

```python
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()

# Get best images for specific payload size
payload_size = 1_000_000  # 1 MB
recommendations = optimizer.recommend_carriers(
    payload_size=payload_size,
    image_paths=['img1.png', 'img2.jpg', 'img3.bmp'],
    top_n=5  # Get top 5 recommendations
)

print(f"Found {recommendations['suitable_count']} suitable images")
for i, img in enumerate(recommendations['recommendations'], 1):
    print(f"{i}. {img.filename}: {img.overall_score:.1f} (capacity: {img.capacity_bytes / 1024 / 1024:.2f}MB)")
```

## API Integration

### Using the Optimize Endpoint

#### Python Requests

```python
import requests

files = {'image': open('myimage.png', 'rb')}
response = requests.post('http://localhost:5000/api/v1/optimize', files=files)

if response.status_code == 200:
    data = response.json()
    print(f"Score: {data['overall_score']}")
    print(f"Capacity: {data['capacity_analysis']['max_payload_mb']} MB")
    print("Recommendations:")
    for rec in data['recommendations']:
        print(f"  - {rec}")
else:
    print(f"Error: {response.json()['error']}")
```

#### JavaScript/Fetch

```javascript
async function analyzeImage(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/v1/optimize', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Score: ${data.overall_score}/100`);
            console.log(`Capacity: ${data.capacity_analysis.max_payload_mb} MB`);
            return data;
        } else {
            const error = await response.json();
            console.error(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error(`Request failed: ${error.message}`);
    }
}

// Usage
const fileInput = document.getElementById('imageInput');
fileInput.addEventListener('change', (e) => {
    analyzeImage(e.target.files[0]);
});
```

#### cURL

```bash
# Analyze a single image
curl -X POST http://localhost:5000/api/v1/optimize \
  -F "image=@myimage.png"

# Save results to file
curl -X POST http://localhost:5000/api/v1/optimize \
  -F "image=@myimage.png" \
  -o result.json

# Pretty print JSON response
curl -X POST http://localhost:5000/api/v1/optimize \
  -F "image=@myimage.png" | python -m json.tool
```

#### Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const http = require('http');

function analyzeImage(imagePath) {
    return new Promise((resolve, reject) => {
        const form = new FormData();
        form.append('image', fs.createReadStream(imagePath));
        
        const options = {
            hostname: 'localhost',
            port: 5000,
            path: '/api/v1/optimize',
            method: 'POST',
            headers: form.getHeaders()
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    resolve(JSON.parse(data));
                } else {
                    reject(new Error(`HTTP ${res.statusCode}`));
                }
            });
        });
        
        form.pipe(req);
    });
}

// Usage
analyzeImage('myimage.png')
    .then(data => {
        console.log(`Score: ${data.overall_score}/100`);
        console.log(`Capacity: ${data.capacity_analysis.max_payload_mb} MB`);
    })
    .catch(err => console.error(err));
```

## Data Structures

### ImageScore Class

```python
@dataclass
class ImageScore:
    path: str                    # Full path to image
    filename: str              # Filename only
    width: int                 # Image width in pixels
    height: int                # Image height in pixels
    pixels: int                # Total pixels (width * height)
    capacity_bytes: int        # Max payload in bytes
    entropy: float             # Shannon entropy (0-8)
    complexity: float          # Texture complexity (0-100)
    compression_ratio: float   # ZIP compression % (0-100)
    overall_score: float       # Final score (0-100)
    
    # Methods
    def to_dict(self) -> dict  # Convert to JSON-ready dict
```

### Response JSON Structure

```json
{
    "success": boolean,
    "filename": "string",
    "overall_score": number,
    "score_breakdown": {
        "capacity_score": number,
        "quality_score": number,
        "suitability_score": number
    },
    "metrics": {
        "width": number,
        "height": number,
        "dimensions": "WIDTHxHEIGHT",
        "entropy": number,
        "complexity": number,
        "format": "PNG|JPEG|BMP|WEBP|...",
        "file_size": number,
        "color_depth": "24-bit RGB",
        "is_compressed": boolean
    },
    "capacity_analysis": {
        "max_payload_bytes": number,
        "max_payload_mb": number,
        "optimal": boolean
    },
    "recommendations": [string],
    "suggestions": [string],
    "risk_assessment": {
        "compression_risk": "Low|Medium|High",
        "entropy_risk": "Low|Medium|High",
        "visibility_risk": "Low|Medium|High"
    },
    "timestamp": "ISO8601"
}
```

## Advanced Usage

### Custom Scoring Weights

```python
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()
score = optimizer.score_image('image.png')

# Custom weighted scoring (different from default 0.4/0.3/0.3)
entropy_norm = (score.entropy / 8.0) * 100
custom_score = (entropy_norm * 0.5) + (score.complexity * 0.3) + (score.compression_ratio * 0.2)

print(f"Standard score: {score.overall_score:.1f}")
print(f"Custom score: {custom_score:.1f}")
```

### Filter by Criteria

```python
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()
images = ['img1.png', 'img2.jpg', 'img3.bmp']

# Get images with high entropy
high_entropy = [
    optimizer.score_image(img) for img in images
    if optimizer.score_image(img) and optimizer.score_image(img).entropy > 6.5
]

# Get images that can fit large payloads
large_capacity = [
    optimizer.score_image(img) for img in images
    if optimizer.score_image(img) and optimizer.score_image(img).capacity_bytes > 1_000_000
]

# Get images with good overall score
suitable = [
    optimizer.score_image(img) for img in images
    if optimizer.score_image(img) and optimizer.score_image(img).overall_score > 70
]
```

### Parallel Analysis

```python
from image_optimizer import ImageOptimizer
from concurrent.futures import ThreadPoolExecutor
import os

def analyze_folder(folder_path, num_workers=4):
    images = [f for f in os.listdir(folder_path) 
              if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))]
    
    optimizer = ImageOptimizer(max_workers=num_workers)
    
    # Use parallel ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(optimizer.score_image, f"{folder_path}/{img}"): img
            for img in images
        }
        
        results = []
        for future in futures:
            score = future.result()
            if score:
                results.append(score)
    
    return results

# Usage
results = analyze_folder('images/', num_workers=4)
results.sort(key=lambda x: x.overall_score, reverse=True)
```

## Performance Tips

### 1. Cache Results

```python
# Store scores to avoid re-analysis
from image_optimizer import ImageOptimizer
import json

optimizer = ImageOptimizer()
cache = {}

def get_score(image_path):
    if image_path not in cache:
        cache[image_path] = optimizer.score_image(image_path)
    return cache[image_path]

# Save cache between sessions
with open('image_scores.json', 'w') as f:
    json.dump({
        path: {
            'score': score.overall_score,
            'entropy': score.entropy,
            'capacity_bytes': score.capacity_bytes
        }
        for path, score in cache.items()
    }, f)
```

### 2. Batch Processing

```python
# Process multiple images efficiently
optimizer = ImageOptimizer()
recommendations = optimizer.recommend_carriers(
    payload_size=5_000_000,  # 5 MB
    image_paths=['img1.png', 'img2.jpg', ...],
    top_n=10  # Get top 10 at once
)
```

### 3. Monitor Performance

```python
import time
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()
images = ['small.png', 'large.png']

for img_path in images:
    start = time.time()
    score = optimizer.score_image(img_path)
    elapsed = time.time() - start
    
    if score:
        mb = score.capacity_bytes / 1024 / 1024
        print(f"{score.filename}: {elapsed*1000:.0f}ms, "
              f"capacity={mb:.1f}MB, score={score.overall_score:.1f}")
```

## Error Handling

```python
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()

try:
    score = optimizer.score_image('nonexistent.png')
    if score is None:
        print("Failed to score image")
    else:
        print(f"Score: {score.overall_score}")
except FileNotFoundError:
    print("Image file not found")
except Exception as e:
    print(f"Error: {e}")
```

## Common Patterns

### Score Images Based on Payload Size

```python
from image_optimizer import ImageOptimizer

def find_best_carrier(payload_size, image_folder):
    """Find best carrier image for given payload size"""
    optimizer = ImageOptimizer()
    recommendations = optimizer.recommend_carriers(
        payload_size=payload_size,
        image_paths=[f"{image_folder}/{f}" for f in os.listdir(image_folder)
                    if f.endswith(('.png', '.jpg', '.bmp', '.webp'))],
        top_n=1
    )
    
    if recommendations['recommendations']:
        return recommendations['recommendations'][0]
    return None

# Usage
best = find_best_carrier(1_000_000, 'images/')  # Find best for 1MB payload
if best:
    print(f"Best carrier: {best.filename} (score: {best.overall_score:.1f})")
```

### Create Score Report

```python
from image_optimizer import ImageOptimizer
import csv

def create_report(image_folder, output_file='score_report.csv'):
    """Generate CSV report of image scores"""
    optimizer = ImageOptimizer()
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Filename', 'Score', 'Entropy', 'Complexity',
            'Compression', 'Capacity (MB)', 'Suitable'
        ])
        
        for filename in os.listdir(image_folder):
            if filename.endswith(('.png', '.jpg', '.bmp', '.webp')):
                score = optimizer.score_image(f"{image_folder}/{filename}")
                if score:
                    writer.writerow([
                        score.filename,
                        f"{score.overall_score:.1f}",
                        f"{score.entropy:.3f}",
                        f"{score.complexity:.1f}",
                        f"{score.compression_ratio:.1f}",
                        f"{score.capacity_bytes / 1024 / 1024:.2f}",
                        "Yes" if score.overall_score >= 70 else "No"
                    ])

create_report('images/')
```

## Debugging

### Enable Logging

```python
import logging
from image_optimizer import ImageOptimizer

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

optimizer = ImageOptimizer()
score = optimizer.score_image('image.png')
# Will print debug info to console
```

### Check Calculation Details

```python
from image_optimizer import ImageOptimizer
from PIL import Image
import numpy as np

optimizer = ImageOptimizer()
image = Image.open('image.png')
image_array = np.array(image)

# Check individual metrics
entropy = optimizer.calculate_shannon_entropy(image_array)
complexity = optimizer.calculate_complexity(image_array)
compression = optimizer.calculate_compression_ratio('image.png')

print(f"Entropy (0-8): {entropy:.3f}")
print(f"Complexity (0-100): {complexity:.1f}")
print(f"Compression ratio: {compression:.1f}%")

entropy_norm = (entropy / 8.0) * 100
overall = (entropy_norm * 0.4) + (complexity * 0.3) + (compression * 0.3)
print(f"Overall score: {overall:.1f}")
```

## Version & Compatibility

| Version | Python | NumPy | Pillow | Status |
|---------|--------|-------|--------|--------|
| 4.0.0 | 3.8+ | 1.19+ | 8.0+ | Deprecated |
| 4.0.1 | 3.10+ | 1.20+ | 9.0+ | Current |
| 4.1.0 (planned) | 3.10+ | 1.23+ | 10.0+ | Future |

---

**Last Updated**: 2024-01-15  
**Documentation Version**: 1.0
