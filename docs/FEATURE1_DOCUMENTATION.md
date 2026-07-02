# Feature #1: Auto Image Optimization - Complete Documentation

## Table of Contents
1. [Quick Start](#quick-start)
2. [User Guide](#user-guide)
3. [Technical Architecture](#technical-architecture)
4. [API Reference](#api-reference)
5. [Performance Benchmarks](#performance-benchmarks)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Quick Start

### For End Users

1. **Open StegoForge** and navigate to the Image Upload section
2. **Select an Image** for analysis (PNG, JPEG, BMP, WEBP)
3. **Click "Analyze Image Quality"** button (appears after image selection)
4. **View Results** including:
   - Overall Optimization Score (0-100)
   - Score Breakdown (Capacity, Quality, Suitability)
   - Capacity Analysis (maximum data you can hide)
   - Risk Assessment (compression, entropy, visibility risks)
   - Personalized Recommendations

### For Developers

```python
from image_optimizer import ImageOptimizer

# Initialize optimizer
optimizer = ImageOptimizer()

# Analyze single image
score = optimizer.score_image('path/to/image.png')

print(f"Score: {score.overall_score}")
print(f"Entropy: {score.entropy:.3f}")
print(f"Capacity: {score.capacity_bytes / 1024 / 1024:.2f} MB")
```

### Using the API

```bash
# POST request to analyze image
curl -X POST http://localhost:5000/api/v1/optimize \
  -F "image=@myimage.png"

# Response (example):
{
  "success": true,
  "overall_score": 77.3,
  "score_breakdown": {
    "capacity_score": 96.3,
    "quality_score": 62.1,
    "suitability_score": 77.3
  },
  "metrics": {
    "width": 800,
    "height": 600,
    "entropy": 6.178,
    "complexity": 62.1,
    "format": "PNG",
    "color_depth": "24-bit RGB"
  },
  "capacity_analysis": {
    "max_payload_mb": 1.4,
    "optimal": true
  },
  "recommendations": [
    "High entropy - excellent for hiding data",
    "Image has excellent texture variation for carrier use",
    "* This image is highly suitable for steganography"
  ],
  "risk_assessment": {
    "compression_risk": "Low",
    "entropy_risk": "Low",
    "visibility_risk": "Low"
  }
}
```

---

## User Guide

### What is Image Optimization?

Image Optimization analyzes images to determine their suitability as "carrier" images for steganography. It evaluates:

1. **Entropy** - How complex and varied the pixel data is
2. **Complexity** - The amount of detail and texture
3. **Compression Ratio** - How well the image compresses

High scores indicate images that are excellent for hiding secret data.

### Interpreting the Score

| Score Range | Suitability | Recommendation |
|-------------|------------|-----------------|
| 75-100 | Excellent | Use this image - highly secure |
| 50-75 | Good | Usable with caution |
| 25-50 | Fair | Consider alternatives |
| 0-25 | Poor | Avoid - use different image |

### Understanding the Metrics

#### Capacity Score (based on Entropy)
- **What it means**: Maximum complexity of pixel data
- **Why it matters**: Complex pixels provide more space to hide data
- **Good range**: 70+ (indicates high entropy)
- **Example**: Random noise = 100, Solid color = 0

#### Quality Score (based on Complexity)
- **What it means**: Amount of texture and detail
- **Why it matters**: Natural images hide data better than flat areas
- **Good range**: 60+ (indicates lots of texture)
- **Example**: Photo of landscape = 80+, Blue sky = 20

#### Suitability Score (combined metric)
- **Formula**: (Entropy * 0.4) + (Complexity * 0.3) + (Compression * 0.3)
- **Interpretation**: Overall rating for steganography suitability
- **Best for**: Making quick decisions about image quality

### Risk Assessment

#### Compression Risk
- **Low**: Good - image resists compression (contains varied data)
- **Medium**: Acceptable - image compresses somewhat
- **High**: Avoid - image compresses heavily (too smooth)
- **Why**: If an image compresses too much, modifications are obvious

#### Entropy Risk
- **Low**: Good - image has good complexity
- **Medium**: Fair - image is fairly complex
- **High**: Poor - image is too uniform
- **Why**: Uniform images can't hide much data safely

#### Visibility Risk
- **Low**: Good - complex image masks changes
- **Medium**: Fair - changes somewhat visible
- **High**: Poor - changes are obvious
- **Why**: Low-complexity images show visual artifacts from hiding data

### Best Practices

1. **Use natural photos** rather than graphics or cartoons
2. **Look for detailed images** with lots of texture (landscapes, portraits)
3. **Avoid solid colors** and simple gradients
4. **Use diverse images** for different payloads (larger images for bigger data)
5. **Check all three scores** - don't just rely on the overall score
6. **Test with your actual payload** before production use

### Common Image Types and Scores

| Image Type | Typical Score | Notes |
|----------|--------------|-------|
| Natural landscape | 70-85 | Excellent choice |
| Portrait photo | 65-80 | Good detail and variety |
| Nature closeup | 75-90 | High entropy from detail |
| Texture/fabric | 60-75 | Good for large payloads |
| Cartoon/graphic | 20-40 | Not recommended |
| Solid color | 0-10 | Worst choice |
| Screenshot | 30-50 | Fair if contains detail |
| Sunset/gradient | 40-60 | Marginal, use caution |

---

## Technical Architecture

### System Overview

```
StegoForge v4.0.1
│
├─ Frontend (HTML/CSS/JavaScript)
│  ├─ Image Upload Handler
│  ├─ "Analyze Image Quality" Button
│  └─ Results Display Panel
│
├─ Backend (Flask REST API)
│  └─ /api/v1/optimize [POST]
│     └─ Rate limiting (30 req/min)
│     └─ File validation
│     └─ Temporary file handling
│
└─ Image Optimizer Module
   ├─ Shannon Entropy Calculator (with adaptive sampling)
   ├─ Complexity Calculator (std deviation)
   ├─ Compression Ratio Calculator (ZIP analysis)
   ├─ Score Aggregator
   └─ Caching System (LRU compression cache)
```

### Algorithm Details

#### Shannon Entropy Calculation

Shannon Entropy measures the average information content:

```
H = -Σ(p_i * log2(p_i))

Where:
  p_i = probability of pixel value i (0-255)
  
Result:
  0 bits    = completely uniform (solid color)
  8 bits    = maximum randomness (pure noise)
  4-7 bits  = typical natural image
```

For large images (>1.5MP), adaptive sampling is used:
- Sample interval = ceil(sqrt(total_pixels / 500,000))
- Maintains accuracy within ~2%
- Achieves 2.6x performance improvement

#### Complexity Calculation

Complexity uses standard deviation of pixel values:

```
complexity = (std_deviation / 127.5) * 100

Where:
  std_deviation = variation of pixel brightness
  127.5 = maximum std_dev for 8-bit images
  
Result:
  0   = flat, smooth areas
  100 = highly textured, varied areas
```

#### Compression Ratio Calculation

Measures how well image compresses with ZIP:

```
ratio = (compressed_size / original_size) * 100

Where:
  compressed_size = size after ZIP deflate compression
  original_size = original file size
  
Result:
  <50%  = excellent (not much redundancy)
  50-80% = good (some compression)
  >80%  = poor (highly compressible, too smooth)
```

Note: Compression cache stores results by MD5 file hash to avoid
recalculation for identical images.

#### Final Score Calculation

```
overall_score = (entropy_norm * 0.4) + (complexity * 0.3) + (compression * 0.3)

Where:
  entropy_norm = entropy / 8 * 100  (normalized to 0-100)
  complexity = 0-100
  compression = 0-100
  
Weights:
  40% entropy      = primary indicator of capacity
  30% complexity   = natural variation for masking
  30% compression  = indicates existing randomness
```

### Performance Optimizations (v4.0.1)

#### Adaptive Sampling for Large Images

Large images (>1.5MP) use intelligent sampling:

| Image Size | Before | After | Improvement |
|-----------|--------|-------|------------|
| 50x50 (0.0025MP) | 17ms | 23ms | No sampling |
| 800x600 (0.48MP) | 95-216ms | 64-147ms | 32-49% |
| 2000x100 (0.2MP) | 136ms | 82ms | 40% |
| 100x2000 (0.2MP) | 135ms | 87ms | 36% |
| 2048x2048 (4.2MP) | 1932ms | 735ms | **62%** |

#### Compression Caching

- **Method**: LRU cache with 10-entry limit
- **Key**: MD5 hash of image file
- **Benefit**: Avoids 100-300ms ZIP operation
- **Scope**: Per-session (resets on app restart)
- **Future**: Global cache across requests (planned)

### Supported Image Formats

| Format | Extension | Color Depth | Support |
|--------|-----------|------------|---------|
| PNG | .png | 8-bit (grayscale) or 24-bit (RGB) | Full |
| JPEG | .jpg, .jpeg | 24-bit (RGB) | Full |
| BMP | .bmp | 24-bit (RGB) | Full |
| WEBP | .webp | 24-bit (RGB) | Full |
| GIF | .gif | 8-bit (indexed) | Full |
| TIFF | .tiff, .tif | Various | Supported (converted to RGB) |

---

## API Reference

### POST /api/v1/optimize

Analyzes an image and returns a suitability score for steganography.

#### Request

```http
POST /api/v1/optimize HTTP/1.1
Host: localhost:5000
Content-Type: multipart/form-data

image=<binary image file>
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| image | File | Yes | Image file to analyze (max 50MB) |

#### Response (Success - 200 OK)

```json
{
  "success": true,
  "filename": "myimage.png",
  "overall_score": 77.3,
  "score_breakdown": {
    "capacity_score": 96.3,
    "quality_score": 62.1,
    "suitability_score": 77.3
  },
  "metrics": {
    "width": 800,
    "height": 600,
    "dimensions": "800x600",
    "entropy": 6.178,
    "complexity": 62.1,
    "format": "PNG",
    "file_size": 1440000,
    "color_depth": "24-bit RGB",
    "is_compressed": false
  },
  "capacity_analysis": {
    "max_payload_bytes": 1440000,
    "max_payload_mb": 1.373,
    "optimal": true
  },
  "recommendations": [
    "High entropy - excellent for hiding data",
    "Image has excellent texture variation for carrier use",
    "* This image is highly suitable for steganography"
  ],
  "suggestions": [
    "Use this image for maximum security in LSB encoding",
    "Combine with password encryption for additional protection",
    "Consider using multi-image steganography for larger payloads"
  ],
  "risk_assessment": {
    "compression_risk": "Low",
    "entropy_risk": "Low",
    "visibility_risk": "Low"
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Response (Error - 400 Bad Request)

```json
{
  "error": "Image file required"
}
```

Possible errors:
- `"Image file required"` - No image in request
- `"Failed to analyze image"` - Processing error
- Invalid file format (corrupted image, not an image file)

#### Response (Error - 413 Payload Too Large)

```json
{
  "error": "File size exceeds maximum (50MB)"
}
```

#### Response (Error - 429 Too Many Requests)

```json
{
  "error": "Rate limit exceeded: 30 requests per minute"
}
```

#### Rate Limiting

- **Limit**: 30 requests per minute per IP address
- **Headers**: 
  - `X-RateLimit-Limit: 30`
  - `X-RateLimit-Remaining: 27`
  - `X-RateLimit-Reset: 1705326645`

#### Performance Characteristics

| Metric | Value |
|--------|-------|
| Average response time | 125 ms |
| 95th percentile | 200 ms |
| 99th percentile | 800 ms |
| Max file size | 50 MB |
| Timeout | 300 seconds |

---

## Performance Benchmarks

### Test Environment

- CPU: Modern multi-core processor
- RAM: 16GB available
- Disk: SSD
- Python: 3.10+
- Libraries: PIL/Pillow, NumPy, SciPy

### Benchmark Results (v4.0.1)

#### Standard Images (800x600)

```
PNG (high entropy)      216.87ms -> 146.78ms (-32%)
PNG (low entropy)        95.15ms ->  55.88ms (-41%)
PNG (complex texture)     98.41ms ->  83.23ms (-15%)
JPEG (90% quality)        90.18ms ->  63.66ms (-29%)
BMP (uncompressed)       210.73ms -> 107.82ms (-49%)
WEBP (lossy)             79.97ms ->  76.30ms (-5%)

Average:                128.55ms ->  88.95ms (-31%)
```

#### Edge Cases

```
Tiny (50x50)              16.93ms ->  22.84ms (variance)
Large (2048x2048)       1931.67ms -> 735.23ms (-62%)
Wide (2000x100)          135.81ms ->  81.82ms (-40%)
Tall (100x2000)          134.99ms ->  87.18ms (-35%)
```

#### Error Cases

```
Corrupted JPEG           ~13ms (HTTP 400)
Fake image file          ~14ms (HTTP 400)
```

### Scalability

| Image Size | Pixels | Time |
|-----------|--------|------|
| 50x50 | 2.5K | 23ms |
| 256x256 | 66K | 30ms |
| 512x512 | 262K | 45ms |
| 800x600 | 480K | 90ms |
| 1024x1024 | 1M | 110ms |
| 2048x2048 | 4.2M | 735ms |
| 2K (2560x1440) | 3.7M | 650ms |
| 4K (3840x2160) | 8.3M | 1200ms* |

*Estimated - not tested, uses adaptive sampling

### Memory Usage

| Image Size | Memory | Sampling |
|-----------|--------|----------|
| 50x50 | 12 KB | None |
| 800x600 | 1.8 MB | None |
| 2048x2048 | 12 MB | 1.3 MB sampled |
| 4096x4096 | 48 MB | 3 MB sampled |

---

## Troubleshooting

### Problem: "Analyze Image Quality" button doesn't appear

**Solution**: 
1. Verify you uploaded an image file
2. Check browser console for JavaScript errors (F12)
3. Ensure image is in supported format (PNG, JPEG, BMP, WEBP)
4. Try different image file

### Problem: "Failed to analyze image" error

**Solution**:
1. Verify image file is not corrupted
2. Try a different image
3. Check server logs: `tail -f logs/app.log`
4. Ensure image is <50MB

### Problem: Image appears to upload but score doesn't display

**Solution**:
1. Wait a moment for analysis (up to 2 seconds for large files)
2. Check if score panel appears below image
3. Open browser console (F12) for error messages
4. Try refreshing page and uploading again

### Problem: API returns 400 error

**Cause**: Invalid or missing image file
**Solution**:
1. Verify image file is valid (try opening in image viewer)
2. Ensure Content-Type is multipart/form-data
3. Check file is not corrupted

### Problem: API returns 429 error

**Cause**: Rate limit exceeded (>30 requests/minute)
**Solution**:
1. Wait 1 minute before trying again
2. Distribute requests across time
3. Contact admin if legitimate high-volume use

### Problem: Slow performance (>2 seconds)

**Solution**:
1. For large images (>2000px), this is expected
2. The feature uses adaptive sampling for large images
3. Ensure server has sufficient RAM
4. Check server CPU usage - may indicate system overload

### Performance Issues - Diagnostic Checklist

```
[ ] Is server running? (check http://localhost:5000)
[ ] Is image file valid? (verify with image viewer)
[ ] Is file size <50MB?
[ ] Server RAM available? (check system resources)
[ ] Flask running in debug mode? (disable for production)
[ ] Is there network latency? (test with curl)
[ ] Have you checked the performance report?
```

---

## FAQ

### Q: What's the difference between entropy, complexity, and compression ratio?

**A**: 
- **Entropy**: Statistical measure of pixel randomness (0-8 bits)
- **Complexity**: Visual texture detail via std deviation (0-100)
- **Compression**: How well ZIP compresses the image (0-100%)

All three measure different aspects of image suitability.

### Q: Why do some images score low when they look detailed?

**A**: Image optimization measures mathematical properties, not visual appeal. A detailed photo of a blue sky might score low because of low entropy in blue areas. Try images with more varied colors and complex patterns.

### Q: Can I hide data in any image?

**A**: Technically yes (LSB always works), but images with high scores hide data much better. Low-score images risk visible artifacts.

### Q: What payload size can I hide in an image?

**A**: The API returns `capacity_analysis.max_payload_mb`. For an 800x600 PNG, this is typically 1.4 MB. Practical payload: 0.5-1.0 MB (leaving buffer for encryption overhead).

### Q: Why is my 2048x2048 image taking so long to analyze?

**A**: Large images require more computation. The optimizer uses adaptive sampling to speed this up (~700ms instead of 1900ms). This is expected behavior.

### Q: Does image optimization affect the original image?

**A**: No. The API only analyzes the image - it doesn't modify it. The original file is unchanged.

### Q: Can I use the same image twice?

**A**: Yes, but for steganography security, it's better to use different images. Using the same image twice makes the hidden data location more predictable.

### Q: What if my image gets corrupted during upload?

**A**: The API will return HTTP 400 "Failed to analyze image". Try re-uploading the file, or use a different image.

### Q: Is the image data stored on the server?

**A**: No. Uploaded images are saved to temporary files, analyzed, then immediately deleted. No data is logged or stored.

### Q: Why do different formats give different scores for the same image?

**A**: JPEG applies lossy compression which affects entropy/complexity calculations. PNG's lossless compression maintains original data. Use PNG for most accurate analysis.

### Q: How accurate are the recommendations?

**A**: Based on cryptographic research into LSB steganography. Recommendations follow best practices for hiding data with minimal detectable artifacts.

### Q: Can I batch analyze multiple images?

**A**: Currently, the UI analyzes one image at a time. For batch analysis, use the Python API directly:

```python
from image_optimizer import ImageOptimizer
import os

optimizer = ImageOptimizer()
for img_file in os.listdir('images/'):
    score = optimizer.score_image(f'images/{img_file}')
    print(f"{img_file}: {score.overall_score}")
```

### Q: What's the roadmap for Feature #1?

**v4.0.1 (Current)**:
- Adaptive sampling for large images
- Compression caching
- Full format support

**v4.0.2 (Planned)**:
- Global optimizer singleton
- NumPy vectorization
- Progress indicator for large files

**v4.1.0 (Future)**:
- Stream processing for 8MP+ images
- GPU acceleration
- Batch analysis UI

---

## Version History

### v4.0.1 (Current)
- Added adaptive pixel sampling for large images (2.6x faster)
- Added compression result caching (LRU)
- Performance optimizations complete
- All formats tested and working
- Error handling robust

### v4.0.0 (Initial Release)
- Base image optimization scoring
- Shannon entropy calculation
- Complexity and compression analysis
- REST API endpoint
- Frontend integration

---

## Support & Contact

For issues, questions, or feature requests:
- Email: support@stegoforge.local
- Documentation: https://stegoforge.local/docs
- GitHub Issues: https://github.com/stegoforge/stegoforge

---

## License

Feature #1 (Image Optimization) is part of StegoForge v4.0.
Licensed under MIT License.

Last Updated: 2024-01-15
Documentation Version: 1.0
