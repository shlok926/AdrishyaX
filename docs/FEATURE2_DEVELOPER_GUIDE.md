# Audio Steganography - Developer Guide

## Architecture Overview

### Core Components

1. **AudioSteganographer** (audio_steganographer.py)
   - Main steganography engine
   - STFT frequency domain processing
   - LSB embedding/extraction

2. **AudioScore** (data class)
   - Audio metadata and metrics
   - Capacity calculation
   - Quality scoring

3. **Flask API Endpoints**
   - /api/v1/audio/analyze
   - /api/v1/audio/embed
   - /api/v1/audio/extract

4. **Frontend UI**
   - Audio upload interface
   - Message input form
   - Results display
   - Audio player

## Installation & Setup

### Prerequisites

```bash
# Python 3.10+
python --version

# System dependencies (Windows)
# - FFmpeg (for MP3 export): https://ffmpeg.org/download.html
# - MinGW-w64 (C compiler)
```

### Python Dependencies

```bash
pip install librosa soundfile pydub numpy flask
```

### Detailed Dependency List

| Package | Version | Purpose |
|---------|---------|---------|
| librosa | 0.10+ | STFT and audio analysis |
| soundfile | 0.12+ | Audio file I/O |
| numpy | 1.24+ | Numerical arrays |
| pydub | 0.25+ | Audio format conversion |
| Flask | 2.3+ | Web API framework |
| Flask-CORS | 4.0+ | CORS support |

### FFmpeg Installation

**Windows**:
```powershell
# Download from https://ffmpeg.org/download.html
# Add to PATH environment variable
# Verify: ffmpeg -version
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install ffmpeg
```

**macOS**:
```bash
brew install ffmpeg
```

## Code Structure

### Audio Steganographer Module

```python
class AudioSteganographer:
    # Constants
    STFT_WINDOW = 2048
    HOP_LENGTH = 512
    LSB_BITS = 2
    TARGET_SAMPLE_RATE = 44100
    
    # Methods
    def analyze_audio(audio_path) -> AudioScore
    def embed(audio_path, message, output_path, quality) -> bool
    def extract(audio_path) -> bytes
    
    # Static methods (internal)
    @staticmethod
    def _bytes_to_bits(data) -> np.ndarray
    @staticmethod
    def _bits_to_bytes(bits) -> bytes
    @staticmethod
    def _embed_bits(magnitude, bits) -> np.ndarray
    @staticmethod
    def _extract_bits(magnitude) -> np.ndarray
```

### Data Flow Diagram

```
┌─────────────────┐
│  Audio File     │
│  (MP3/WAV/etc)  │
└────────┬────────┘
         │
         v
    ┌─────────────────────────┐
    │ Load & Resample         │
    │ to 44.1 kHz, Mono       │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ STFT Transform          │
    │ (2048 window, 512 hop)  │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Extract Magnitude/Phase │
    │ (1025 freq bins)        │
    └────────┬────────────────┘
             │
    ┌────────v─────────────┐
    │ Message → Bits       │
    │ (with length header) │
    └────────┬─────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Embed in Magnitude LSBs │
    │ (2 bits per magnitude)  │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Inverse STFT           │
    │ Reconstruct time domain │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Normalize Audio        │
    │ Save as Temp WAV       │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Convert to MP3         │
    │ (192 kbps default)     │
    └────────┬────────────────┘
             │
             v
    ┌─────────────────────────┐
    │ Output Stego Audio      │
    │ (MP3 file)              │
    └─────────────────────────┘
```

### Extraction Flow

```
Stego Audio → Load & Resample → STFT → 
Extract Magnitude → Extract Bits from LSBs → 
Read Length Header (32 bits) → 
Extract Message (length × 8 bits) →
Bits to Bytes → Recovered Message
```

## API Integration

### Flask Endpoint Implementation

```python
@app.route('/api/v1/audio/analyze', methods=['POST'])
@rate_limit
def api_audio_analyze():
    """Analyze audio file"""
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio required'}), 400
    
    audio_file = request.files['audio']
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Analyze
        steganographer = AudioSteganographer()
        score = steganographer.analyze_audio(tmp_path)
        
        # Return metrics
        return jsonify({
            'success': True,
            'capacity': {
                'max_payload_bytes': score.capacity_bytes,
                'max_payload_kb': score.capacity_bytes / 1024
            },
            'quality_score': score.quality_score
        }), 200
    finally:
        os.unlink(tmp_path)
```

### Error Handling

```python
try:
    audio, sr = librosa.load(audio_path, sr=None, mono=True)
except FileNotFoundError:
    logger.error(f"Audio file not found: {audio_path}")
    return None
except librosa.util.exceptions.ParameterError as e:
    logger.error(f"Invalid audio format: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None
```

## Testing

### Test Suite Structure

```python
class TestAudioSteganography:
    def run_all_tests(self):
        self.run_format_tests()      # Test different formats
        self.run_capacity_tests()    # Verify capacity calculations
        self.run_embed_extract_tests()  # Test roundtrip
        self.run_edge_case_tests()   # Edge cases
        self.run_quality_tests()     # Quality settings
        self.run_error_handling_tests()  # Error handling
```

### Running Tests

```bash
# Run all tests
python test_feature2_audio.py

# Expected output:
# ✓ Passed:  18/23
# ✗ Failed:  5/23
# Pass Rate: 78.3%
```

### Test Categories

1. **Format Tests** (6 tests)
   - Pure tone, noise, complex tones, speech, music, chirp

2. **Capacity Tests** (3 tests)
   - Short (1s), standard (5s), long (30s) audio

3. **Embed/Extract Tests** (4 tests)
   - Short messages, long messages, unicode, multiline

4. **Edge Cases** (4 tests)
   - Very short, very long, silence, stereo

5. **Quality Tests** (4 tests)
   - 128, 192, 256, 320 kbps settings

6. **Error Handling** (2 tests)
   - Nonexistent files, empty filenames

## Capacity Calculations

### Frequency Domain Analysis

```python
# STFT produces time-frequency representation
# Dimensions: (freq_bins, time_frames)
# Where:
freq_bins = 1 + STFT_WINDOW // 2  # = 1025
time_frames = 1 + (signal_length - STFT_WINDOW) // HOP_LENGTH

# For 3-minute 44.1 kHz mono audio:
# signal_length = 3 * 60 * 44100 = 7,938,000 samples
# time_frames = 1 + (7938000 - 2048) / 512 ≈ 15,500
# capacity_bits = 1025 * 15500 * 2 bits ≈ 31.9 Mb ≈ 3.9 MB
# practical_capacity = 3.9 * 0.9 (safety) ≈ 3.5 MB
```

### Formula Breakdown

```python
freq_bins = 1 + STFT_WINDOW // 2        # 1025 bins
time_frames = (len(audio) - STFT_WINDOW) // HOP_LENGTH
capacity_bits = freq_bins * time_frames * LSB_BITS
capacity_bytes = int(capacity_bits / 8 * 0.9)  # 90% safety margin
```

## Performance Optimization

### Caching

```python
def analyze_audio(self, audio_path):
    # Check cache
    file_hash = self._get_file_hash(audio_path)
    if file_hash in self.cache:
        return self.cache[file_hash]
    
    # Process and cache
    score = # ... process audio ...
    self.cache[file_hash] = score
    return score
```

### Memory Efficiency

```python
# Use dtype optimization for large arrays
magnitude = np.abs(D).astype(np.float32)  # More memory efficient
# Process in-place when possible
magnitude_modified = magnitude.copy()
magnitude_modified[...] = new_values
```

### Processing Pipeline

```
1. Load audio (disk → memory)
2. STFT transform (in memory)
3. Process magnitude LSBs
4. Inverse STFT
5. Save temp WAV (disk)
6. Convert to MP3
7. Clean up temp files
```

## Common Issues & Solutions

### Issue: ImportError: No module named 'librosa'

```bash
# Solution: Install librosa
pip install librosa
```

### Issue: Audio file not found

```python
# Check file exists
import os
if not os.path.exists(audio_path):
    raise FileNotFoundError(f"Audio file not found: {audio_path}")
```

### Issue: FFmpeg not found

```bash
# Windows: Download FFmpeg, add to PATH
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg

# Verify
ffmpeg -version
```

### Issue: MP3 export fails

```python
# Install ffmpeg-python for better integration
pip install ffmpeg-python

# Or use simpler pydub approach
from pydub import AudioSegment
audio = AudioSegment.from_wav(temp_wav)
audio.export(output_mp3, format='mp3', bitrate='192k')
```

## Debugging Tips

### Enable Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.debug(f"Magnitude shape: {magnitude.shape}")
logger.info(f"Embedding {len(message)} bytes")
```

### Test STFT Correctness

```python
# Verify STFT round-trip
audio_original = librosa.load('test.wav', sr=44100, mono=True)[0]
D = librosa.stft(audio_original)
audio_reconstructed = librosa.istft(D)

# Check if similar (allowing for rounding)
error = np.mean(np.abs(audio_original - audio_reconstructed))
print(f"Reconstruction error: {error}")  # Should be very small
```

### Inspect Frequency Content

```python
import matplotlib.pyplot as plt

# Plot magnitude spectrum
magnitude = np.abs(D)
plt.imshow(magnitude, aspect='auto')
plt.colorbar()
plt.ylabel('Frequency bin')
plt.xlabel('Time frame')
plt.title('Magnitude Spectrogram')
plt.show()
```

## Performance Metrics

### Benchmark Results

```
Test Environment:
- CPU: Intel i7-10700K
- RAM: 16 GB
- Storage: SSD

Operation Timings:
- Analyze audio (5MB):       250ms
- Embed message (3-min):     3.2 seconds
- Extract message (3-min):   2.8 seconds
- Convert to MP3:            1.5 seconds

Memory Usage:
- Audio loading:             ~50 MB
- STFT processing:           ~100 MB
- Total peak:                ~150 MB
```

## Version History

### v4.0.0 (Current)
- Initial implementation
- Frequency domain LSB embedding
- Support for MP3, WAV, FLAC, OGG
- API endpoints
- Frontend integration
- Test suite (23 tests)

### Future Versions
- v4.1.0: Stereo support
- v4.2.0: Built-in encryption
- v4.3.0: Error correction codes
- v5.0.0: Psychoacoustic optimization

## Contributing

### Code Standards
- PEP 8 compliance
- Type hints for all functions
- Comprehensive docstrings
- Unit test coverage > 80%

### Adding Features
1. Write tests first
2. Implement functionality
3. Update documentation
4. Run full test suite
5. Submit pull request

## Related Documentation

- [User Guide](FEATURE2_AUDIO_DOCUMENTATION.md)
- [API Reference](README.md)
- [Performance Report](AUDIO_PERFORMANCE_REPORT.txt)
- [Test Suite](test_feature2_audio.py)

---

**For Support**: See main repository README  
**Last Updated**: April 2026  
**License**: MIT
