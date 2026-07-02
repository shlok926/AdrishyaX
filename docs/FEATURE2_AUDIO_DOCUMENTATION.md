# Feature #2: Audio Steganography - Complete Documentation

## Overview

**Audio Steganography** is a steganography technique that hides secret messages within audio files using frequency domain Least Significant Bit (LSB) embedding. This feature enables secure communication through seemingly innocent audio files (MP3, WAV, FLAC, OGG).

## Quick Start

### 1. Hide a Message in Audio

1. Open StegoForge
2. Click on **Audio Stego** in the sidebar
3. Drop an audio file (MP3, WAV, FLAC, OGG)
4. Enter your secret message
5. Adjust quality slider (128-320 kbps)
6. Click **Hide Message in Audio**
7. Download the stego audio file

### 2. Extract a Hidden Message

1. Click on **Audio Stego** in the sidebar
2. Click **Extract Message** tab
3. Drop the stego audio file
4. Click **Extract Message**
5. View the recovered message

## Technical Details

### How It Works

The audio steganography engine uses **frequency domain LSB embedding**:

```
1. Load audio file → Analyze format
2. Convert to frequency domain using STFT (Short-Time Fourier Transform)
3. Extract magnitude and phase information
4. Embed secret message bits in LSBs of magnitude values
5. Reconstruct frequency domain representation
6. Convert back to time domain (audio waveform)
7. Export as MP3 file
```

### Why Frequency Domain?

Frequency domain embedding is superior to time-domain LSB for audio because:

- **Imperceptible**: Human auditory system is less sensitive to frequency changes
- **Robust**: More resistant to audio degradation (compression, noise)
- **Capacity**: Higher hiding capacity than time-domain approaches
- **Psychoacoustic Masking**: Can hide data in masked regions undetectable to human ear

### Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| STFT Window | 2048 samples | FFT window size |
| Hop Length | 512 samples | Window overlap |
| LSB Bits | 2 bits/magnitude | Bits per frequency value |
| Target Sample Rate | 44,100 Hz | Standard CD quality |
| Frequency Bins | 1,025 bins | STFT output bins |

### Capacity Calculation

For a 3-minute song at 44.1 kHz:

```
Frequency bins: 1 + 2048/2 = 1,025 bins
Time frames: 180s × 44,100Hz / 512 ≈ 15,500 frames
Total magnitude values: 1,025 × 15,500 = ~15.9 million values
Available capacity: 15.9M × 2 bits / 8 = ~3.975 MB
Practical capacity (with safety margin): 2-3 MB
```

**Formula**: `capacity_bytes = (freq_bins × time_frames × lsb_bits / 8) × 0.9`

## Supported Audio Formats

### Input Formats
- **MP3** - MPEG Audio Layer III
- **WAV** - Waveform Audio File Format
- **FLAC** - Free Lossless Audio Codec
- **OGG** - Ogg Vorbis Format
- **M4A** - MPEG-4 Audio (with AAC codec)
- **AAC** - Advanced Audio Coding

### Output Format
- **MP3** - All stego audio files are exported as MP3 for compatibility

### Audio Properties
- **Sample Rate**: 44.1 kHz (44,100 Hz) - industry standard
- **Channels**: Mono processing (stereo converted to mono)
- **Bit Depth**: 16-bit PCM (processed from original)
- **Quality Range**: 128-320 kbps MP3 quality

## API Endpoints

### Analyze Audio

**Endpoint**: `POST /api/v1/audio/analyze`

Analyze an audio file for steganography suitability.

**Request**:
```bash
curl -X POST http://localhost:5000/api/v1/audio/analyze \
  -F "audio=@song.mp3"
```

**Response**:
```json
{
  "success": true,
  "filename": "song.mp3",
  "audio_info": {
    "format": "mp3",
    "duration_seconds": 180.5,
    "sample_rate": 44100,
    "channels": 2,
    "file_size_kb": 4096
  },
  "capacity": {
    "max_payload_bytes": 3145728,
    "max_payload_kb": 3071.25,
    "max_payload_mb": 3.0,
    "message_limit_chars": 3145728
  },
  "quality_score": 87.3,
  "suitability": "Excellent",
  "recommendations": [
    "Audio is suitable for steganography",
    "Can hide up to 3071.25 KB of data",
    "Use password protection for security"
  ],
  "timestamp": "2026-04-25T10:30:00"
}
```

### Embed Message

**Endpoint**: `POST /api/v1/audio/embed`

Hide a message in an audio file.

**Request**:
```bash
curl -X POST http://localhost:5000/api/v1/audio/embed \
  -F "audio=@carrier.wav" \
  -F "message=My secret message" \
  -F "quality=192" \
  --output stego.mp3
```

**Parameters**:
- `audio` (file): Carrier audio file
- `message` (text): Message to hide
- `quality` (integer): MP3 quality (128-320 kbps, default: 192)

**Response**: Binary MP3 file with hidden message

### Extract Message

**Endpoint**: `POST /api/v1/audio/extract`

Recover a hidden message from stego audio.

**Request**:
```bash
curl -X POST http://localhost:5000/api/v1/audio/extract \
  -F "audio=@stego.mp3"
```

**Response**:
```json
{
  "success": true,
  "message": "My secret message",
  "message_size": 18,
  "timestamp": "2026-04-25T10:35:00"
}
```

## Code Examples

### Python Backend

```python
from audio_steganographer import AudioSteganographer

# Initialize
steganographer = AudioSteganographer()

# Analyze audio
score = steganographer.analyze_audio('song.wav')
print(f"Capacity: {score.capacity_bytes / 1024:.2f} KB")
print(f"Quality: {score.quality_score:.1f}")

# Embed message
message = "Secret message"
success = steganographer.embed('song.wav', message, 'stego.mp3', quality=192)

# Extract message
recovered = steganographer.extract('stego.mp3')
print(f"Recovered: {recovered.decode('utf-8')}")
```

### JavaScript Frontend

```javascript
// Initialize
const audioFile = document.getElementById('audioInput').files[0];

// Analyze
const formData = new FormData();
formData.append('audio', audioFile);

const response = await fetch('/api/v1/audio/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(`Capacity: ${result.capacity.max_payload_kb} KB`);

// Embed
const embedData = new FormData();
embedData.append('audio', audioFile);
embedData.append('message', 'Secret text');
embedData.append('quality', '192');

const embedResponse = await fetch('/api/v1/audio/embed', {
  method: 'POST',
  body: embedData
});

const steoAudio = await embedResponse.blob();
// Download or process...
```

### cURL Examples

```bash
# Analyze audio
curl -X POST http://localhost:5000/api/v1/audio/analyze \
  -F "audio=@music.mp3" \
  -H "Accept: application/json" | jq .

# Hide message
curl -X POST http://localhost:5000/api/v1/audio/embed \
  -F "audio=@music.mp3" \
  -F "message=Top secret message" \
  -F "quality=256" \
  --output secret_audio.mp3

# Extract message
curl -X POST http://localhost:5000/api/v1/audio/extract \
  -F "audio=@secret_audio.mp3" \
  -H "Accept: application/json" | jq .message
```

## Implementation Notes

### Audio Processing Pipeline

1. **Input Handling**
   - Accepts multiple audio formats
   - Validates file integrity
   - Checks sample rate compatibility

2. **Frequency Domain Analysis**
   - Uses STFT with 2048-sample window
   - Extracts magnitude and phase information
   - Calculates time-frequency grid

3. **LSB Embedding**
   - Converts message to bit array
   - Embeds 2 bits per magnitude value
   - Preserves phase information

4. **Output Generation**
   - Reconstructs time-domain audio
   - Normalizes amplitude
   - Exports as MP3 (192 kbps default)

### Quality vs Capacity Trade-off

| Quality | Bitrate | File Size | Noise Level |
|---------|---------|-----------|-------------|
| Low | 128 kbps | Small | Higher |
| Medium | 192 kbps | Medium | Medium |
| High | 256 kbps | Large | Lower |
| Very High | 320 kbps | Largest | Very Low |

Higher quality settings produce cleaner audio but larger files.

### Message Length Header

Each embedded message includes a 32-bit length header:
- **Bytes 0-3**: Message length in bytes (big-endian)
- **Bytes 4+**: Actual message content

This enables automatic message length detection during extraction.

## Performance Metrics

### Analysis Performance
- **Small audio (< 1 MB)**: < 100ms
- **Medium audio (5-10 MB)**: 100-300ms
- **Large audio (> 50 MB)**: 300-1000ms

### Embedding Performance
- **Typical song (3-5 min)**: 2-5 seconds
- **Long audio (30+ min)**: 15-30 seconds
- **Output file size**: ~1.5-2 MB per minute (192 kbps)

### Extraction Performance
- **Typical song**: < 2 seconds
- **Long audio**: 5-10 seconds

## Security Considerations

### Strengths
1. **Frequency Domain Robustness**: More resistant to noise and compression
2. **Imperceptible**: Changes are below human auditory threshold
3. **Capacity**: Can hide multiple MB in audio
4. **Format Flexibility**: Works with most audio formats

### Limitations
1. **MP3 Lossy Compression**: May lose some embedded data
2. **Steganalysis Vulnerability**: Detectable by advanced analysis
3. **Single Channel**: No crypto integration (add encryption for security)
4. **Audio Length**: Requires sufficient duration for significant capacity

### Recommendations
1. **Always combine with encryption** for sensitive data
2. **Use high-quality audio files** (> 320 kbps) for better results
3. **Keep audio file**  to avoid degradation
4. **Test extraction** before relying on hidden data
5. **Use sufficiently long audio** for large messages

## Troubleshooting

### Issue: "Analysis failed"
**Solution**: Ensure audio file is valid and not corrupted

### Issue: "Embedding failed"
**Solution**: Check that audio file is supported; try converting to WAV first

### Issue: Message extraction fails
**Solution**: Ensure audio file hasn't been re-encoded or compressed

### Issue: Low capacity warning
**Solution**: Use longer duration audio or higher quality source file

### Issue: Audio quality degradation
**Solution**: Increase MP3 bitrate (use 256-320 kbps instead of 128 kbps)

## Advanced Usage

### Batch Processing

```python
import os
from audio_steganographer import AudioSteganographer

steganographer = AudioSteganographer()
audio_files = [f for f in os.listdir('audio/') if f.endswith('.mp3')]

for audio_file in audio_files:
    path = os.path.join('audio/', audio_file)
    score = steganographer.analyze_audio(path)
    print(f"{audio_file}: {score.capacity_bytes / 1024:.1f} KB capacity")
```

### Custom Quality Settings

```python
# High quality (better audio, but larger files)
steganographer.embed('song.wav', message, 'output.mp3', quality=320)

# Low quality (smaller files, but more noise)
steganographer.embed('song.wav', message, 'output.mp3', quality=128)
```

### Format Conversion

```python
# Convert MP3 to WAV for processing
from audio_steganographer import AudioSteganographer

AudioSteganographer.convert_to_mp3('input.wav', 'output.mp3', quality=192)
```

## Comparison with Image Steganography

| Aspect | Audio | Image |
|--------|-------|-------|
| Capacity | 2-3 MB per song | 10-50 KB per image |
| Imperceptibility | Excellent | Very Good |
| Detection Difficulty | Medium | High |
| Processing Speed | Fast (2-5s) | Very Fast (<1s) |
| Media Size | Large (3-5 MB) | Small (100-500 KB) |
| Natural Occurrence | Easy (music files) | Easy (photos) |

## Future Enhancements

1. **Stereo Channel Support**: Hide different data in each channel
2. **Encryption Integration**: Built-in AES encryption
3. **Error Correction**: Reed-Solomon codes for robustness
4. **Watermarking**: Copyright protection extensions
5. **Spread Spectrum**: Alternative embedding algorithm
6. **Psychoacoustic Optimization**: Exploit hearing limitations

## References

### Technical Papers
- "Spread Spectrum Audio Watermarking" - Cox et al.
- "Frequency Domain Audio Steganography" - IEEE Transactions
- "Psychoacoustic Masking in Audio" - AES Papers

### Related Standards
- MPEG-1 Audio Layer III (MP3)
- FLAC - Free Lossless Audio Codec
- Ogg Vorbis Specification

## Support & Resources

- **Documentation**: See this guide
- **API Reference**: Detailed endpoint documentation
- **Code Examples**: Python, JavaScript, cURL samples
- **Test Suite**: 23 comprehensive test cases
- **Performance Benchmarks**: Timing analysis included

---

**Version**: 4.0.0  
**Last Updated**: April 2026  
**Status**: Production Ready
