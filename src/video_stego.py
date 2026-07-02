"""
Video Steganography Module
Embeds and extracts data from video files using frame-based steganography
"""

import os
import logging
import io
import json
from typing import Tuple, Dict, List
from PIL import Image
import struct

logger = logging.getLogger(__name__)


class VideoSteganography:
    """Handle video steganography operations."""
    
    # Supported codecs
    SUPPORTED_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'flv', 'webm']
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    
    def __init__(self):
        """Initialize video steganography handler."""
        self.has_ffmpeg = self._check_ffmpeg()
        self.use_pillow_only = not self.has_ffmpeg
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def embed_in_video(self, video_file, payload_bytes: bytes, 
                      carrier_frame_count: int = 10) -> bytes:
        """
        Embed payload into video frames.
        
        Uses first N carrier frames for embedding (spreads data across frames).
        """
        if not self.has_ffmpeg:
            raise ValueError('FFmpeg required for video steganography')
        
        try:
            # Extract frames from video
            frames = self._extract_frames(video_file, max_frames=carrier_frame_count)
            
            if not frames:
                raise ValueError('No frames extracted from video')
            
            logger.info(f'Extracted {len(frames)} frames for embedding')
            
            # Split payload across frames
            frame_payload_size = len(payload_bytes) // len(frames)
            remainder = len(payload_bytes) % len(frames)
            
            modified_frames = []
            payload_offset = 0
            
            for i, frame_data in enumerate(frames):
                # Calculate payload size for this frame
                chunk_size = frame_payload_size
                if i < remainder:
                    chunk_size += 1
                
                # Extract chunk of payload
                chunk = payload_bytes[payload_offset:payload_offset + chunk_size]
                payload_offset += chunk_size
                
                # Embed chunk into frame
                modified_frame = self._embed_into_frame(frame_data, chunk)
                modified_frames.append(modified_frame)
            
            # Reconstruct video with modified frames
            output_video = self._reconstruct_video(video_file, modified_frames)
            
            logger.info(f'Embedded {len(payload_bytes)} bytes across {len(modified_frames)} frames')
            return output_video
        
        except Exception as e:
            logger.error(f'Video embedding failed: {e}')
            raise
    
    def extract_from_video(self, video_file) -> bytes:
        """
        Extract embedded payload from video frames.
        """
        if not self.has_ffmpeg:
            raise ValueError('FFmpeg required for video steganography')
        
        try:
            # Extract all frames
            frames = self._extract_frames(video_file, max_frames=None)
            
            if not frames:
                raise ValueError('No frames extracted from video')
            
            logger.info(f'Extracted {len(frames)} frames for analysis')
            
            # Extract payload from each frame
            payloads = []
            for frame_data in frames:
                payload_chunk = self._extract_from_frame(frame_data)
                if payload_chunk:
                    payloads.append(payload_chunk)
            
            # Concatenate all payloads
            extracted_payload = b''.join(payloads)
            
            logger.info(f'Extracted {len(extracted_payload)} bytes from {len(frames)} frames')
            return extracted_payload
        
        except Exception as e:
            logger.error(f'Video extraction failed: {e}')
            raise
    
    def _extract_frames(self, video_file, max_frames: int = None) -> List[bytes]:
        """Extract frames from video using FFmpeg."""
        import subprocess
        import tempfile
        
        frames = []
        temp_dir = None
        
        try:
            # Create temporary directory for frame extraction
            temp_dir = tempfile.mkdtemp()
            frame_pattern = os.path.join(temp_dir, 'frame_%04d.png')
            
            # FFmpeg command to extract frames
            cmd = [
                'ffmpeg',
                '-i', video_file.filename if hasattr(video_file, 'filename') else 'input.mp4',
                '-vf', 'select=not(mod(n\\,1))',  # Extract every frame
                '-vsync', 'vfr',
                frame_pattern
            ]
            
            # Execute FFmpeg
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            if result.returncode != 0:
                logger.warning(f'FFmpeg warning: {result.stderr.decode()[:200]}')
            
            # Load frames
            frame_files = sorted([f for f in os.listdir(temp_dir) if f.endswith('.png')])
            
            if max_frames:
                frame_files = frame_files[:max_frames]
            
            for frame_file in frame_files:
                frame_path = os.path.join(temp_dir, frame_file)
                with open(frame_path, 'rb') as f:
                    frames.append(f.read())
            
            return frames
        
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
    
    def _embed_into_frame(self, frame_bytes: bytes, payload: bytes) -> bytes:
        """
        Embed payload into a video frame using LSB steganography.
        """
        try:
            # Load frame as PIL image
            frame_img = Image.open(io.BytesIO(frame_bytes)).convert('RGB')
            frame_array = list(frame_img.getdata())
            
            # Calculate max payload capacity
            max_capacity = len(frame_array) * 3 // 8  # 3 color channels, 1 bit per channel
            
            if len(payload) > max_capacity:
                logger.warning(f'Payload ({len(payload)}) exceeds frame capacity ({max_capacity})')
                payload = payload[:max_capacity]
            
            # Convert payload to binary string
            payload_bits = ''.join(format(byte, '08b') for byte in payload)
            payload_bits = payload_bits.ljust(max_capacity * 8, '0')  # Pad with zeros
            
            # Add length header (4 bytes = 32 bits)
            length_bits = format(len(payload), '032b')
            all_bits = length_bits + payload_bits
            
            # Embed bits into frame using LSB
            modified_pixels = []
            bit_index = 0
            
            for pixel in frame_array:
                if not isinstance(pixel, tuple):
                    pixel = (pixel, pixel, pixel)
                
                r, g, b = pixel[:3]
                
                # Embed in RGB channels
                if bit_index < len(all_bits):
                    r = (r & 0xFE) | int(all_bits[bit_index])
                    bit_index += 1
                if bit_index < len(all_bits):
                    g = (g & 0xFE) | int(all_bits[bit_index])
                    bit_index += 1
                if bit_index < len(all_bits):
                    b = (b & 0xFE) | int(all_bits[bit_index])
                    bit_index += 1
                
                modified_pixels.append((r, g, b))
            
            # Create modified frame image
            modified_img = Image.new('RGB', frame_img.size)
            modified_img.putdata(modified_pixels)
            
            # Save to bytes
            output = io.BytesIO()
            modified_img.save(output, format='PNG')
            output.seek(0)
            
            return output.getvalue()
        
        except Exception as e:
            logger.error(f'Frame embedding failed: {e}')
            raise
    
    def _extract_from_frame(self, frame_bytes: bytes) -> bytes:
        """
        Extract embedded payload from a video frame.
        """
        try:
            # Load frame as PIL image
            frame_img = Image.open(io.BytesIO(frame_bytes)).convert('RGB')
            frame_array = list(frame_img.getdata())
            
            # Extract bits from LSB
            bits = []
            for pixel in frame_array:
                if not isinstance(pixel, tuple):
                    pixel = (pixel, pixel, pixel)
                
                r, g, b = pixel[:3]
                bits.append(str(r & 1))
                bits.append(str(g & 1))
                bits.append(str(b & 1))
            
            # Extract length (first 32 bits)
            if len(bits) < 32:
                return b''
            
            length_bits = ''.join(bits[:32])
            payload_length = int(length_bits, 2)
            
            if payload_length == 0 or payload_length > len(bits) - 32:
                return b''
            
            # Extract payload bits
            payload_bits = ''.join(bits[32:32 + payload_length * 8])
            
            # Convert bits back to bytes
            payload = bytes(
                int(payload_bits[i:i+8], 2) 
                for i in range(0, len(payload_bits), 8)
            )
            
            return payload
        
        except Exception as e:
            logger.warning(f'Frame extraction failed: {e}')
            return b''
    
    def _reconstruct_video(self, original_video, modified_frames: List[bytes]) -> bytes:
        """Reconstruct video with modified frames."""
        import subprocess
        import tempfile
        
        temp_dir = None
        
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Save modified frames
            for i, frame_bytes in enumerate(modified_frames):
                frame_path = os.path.join(temp_dir, f'frame_{i:04d}.png')
                with open(frame_path, 'wb') as f:
                    f.write(frame_bytes)
            
            # Output file
            output_path = os.path.join(temp_dir, 'output.mp4')
            frame_pattern = os.path.join(temp_dir, 'frame_%04d.png')
            
            # FFmpeg command to reconstruct video
            cmd = [
                'ffmpeg',
                '-framerate', '30',  # Default 30 fps
                '-i', frame_pattern,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                output_path
            ]
            
            # Execute FFmpeg
            subprocess.run(cmd, capture_output=True, timeout=300)
            
            # Read output video
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    return f.read()
            
            return b''
        
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
    
    def get_video_info(self, video_file) -> Dict:
        """Get information about video file."""
        if not self.has_ffmpeg:
            return {
                'status': 'FFmpeg not available',
                'ffmpeg_available': False
            }
        
        try:
            import subprocess
            import json
            
            # Use ffprobe to get video info
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_file.filename if hasattr(video_file, 'filename') else 'input.mp4'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return {
                    'duration': info.get('format', {}).get('duration', 'Unknown'),
                    'size': info.get('format', {}).get('size', 'Unknown'),
                    'bitrate': info.get('format', {}).get('bit_rate', 'Unknown'),
                    'streams': len(info.get('streams', [])),
                    'ffmpeg_available': True
                }
            
            return {'error': 'Failed to get video info'}
        
        except Exception as e:
            logger.error(f'Video info error: {e}')
            return {'error': str(e)}
