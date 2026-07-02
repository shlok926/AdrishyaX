"""
StegoForge v4.1 - Multi-File Steganography Module
Handles embedding and extracting multiple files with ZIP compression
"""

import zipfile
import io
import json
import os
from datetime import datetime
import py7zr

class MultiFileHandler:
    """Handles multiple file compression and segmentation for steganography."""
    
    MAX_SINGLE_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
    MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB total
    COMPRESSION_LEVEL = 9  # Maximum compression
    
    @staticmethod
    def create_file_manifest(files_list):
        """Create metadata manifest for files."""
        manifest = {
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'file_count': len(files_list),
            'files': []
        }
        
        total_size = 0
        for file_info in files_list:
            total_size += file_info['size']
            manifest['files'].append({
                'name': file_info['name'],
                'size': file_info['size'],
                'mime_type': file_info.get('mime_type', 'application/octet-stream'),
                'checksum': file_info.get('checksum', '')
            })
        
        manifest['total_size'] = total_size
        manifest['compressed_size'] = 0  # Will be set after compression
        
        return manifest
    
    @staticmethod
    def compress_files(files_list):
        """
        Compress multiple files into ZIP archive.
        
        Args:
            files_list: List of (file_name, file_bytes) tuples
        
        Returns:
            Compressed ZIP bytes, manifest dict
        """
        if not files_list:
            raise ValueError("No files provided")
        
        if len(files_list) > 1000:
            raise ValueError("Too many files (max 1000)")
        
        # Validate file sizes
        total_size = sum(len(f[1]) for f in files_list)
        if total_size > MultiFileHandler.MAX_TOTAL_SIZE:
            raise ValueError(f"Total size exceeds maximum ({total_size} > {MultiFileHandler.MAX_TOTAL_SIZE})")
        
        for file_name, file_bytes in files_list:
            if len(file_bytes) > MultiFileHandler.MAX_SINGLE_FILE_SIZE:
                raise ValueError(f"Single file too large: {file_name} ({len(file_bytes)} bytes)")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, 
                            compresslevel=MultiFileHandler.COMPRESSION_LEVEL) as zf:
            
            # Add manifest
            manifest_files = []
            for file_name, file_bytes in files_list:
                manifest_files.append({
                    'name': file_name,
                    'size': len(file_bytes),
                    'mime_type': 'application/octet-stream'
                })
            
            manifest = MultiFileHandler.create_file_manifest(manifest_files)
            zf.writestr('manifest.json', json.dumps(manifest, indent=2))
            
            # Add files
            for file_name, file_bytes in files_list:
                zf.writestr(f'files/{file_name}', file_bytes)
        
        zip_buffer.seek(0)
        compressed = zip_buffer.getvalue()
        
        # Update manifest with compressed size
        manifest['compressed_size'] = len(compressed)
        manifest['compression_ratio'] = round(
            (1 - len(compressed) / total_size) * 100, 2
        )
        
        return compressed, manifest
    
    @staticmethod
    def compress_files_7z(files_list):
        """
        Compress multiple files into 7-Zip archive for better compression.
        
        Args:
            files_list: List of (file_name, file_bytes) tuples
        
        Returns:
            Compressed 7Z bytes, manifest dict
        """
        if not files_list:
            raise ValueError("No files provided")
        
        if len(files_list) > 1000:
            raise ValueError("Too many files (max 1000)")
        
        # Validate file sizes
        total_size = sum(len(f[1]) for f in files_list)
        if total_size > MultiFileHandler.MAX_TOTAL_SIZE:
            raise ValueError(f"Total size exceeds maximum ({total_size} > {MultiFileHandler.MAX_TOTAL_SIZE})")
        
        for file_name, file_bytes in files_list:
            if len(file_bytes) > MultiFileHandler.MAX_SINGLE_FILE_SIZE:
                raise ValueError(f"Single file too large: {file_name} ({len(file_bytes)} bytes)")
        
        # Create 7Z
        sevenz_buffer = io.BytesIO()
        with py7zr.SevenZipFile(sevenz_buffer, 'w') as szf:
            
            # Add manifest
            manifest_files = []
            for file_name, file_bytes in files_list:
                manifest_files.append({
                    'name': file_name,
                    'size': len(file_bytes),
                    'mime_type': 'application/octet-stream'
                })
            
            manifest = MultiFileHandler.create_file_manifest(manifest_files)
            szf.writestr('manifest.json', json.dumps(manifest, indent=2))
            
            # Add files
            for file_name, file_bytes in files_list:
                szf.writestr(f'files/{file_name}', file_bytes)
        
        sevenz_buffer.seek(0)
        compressed = sevenz_buffer.getvalue()
        
        # Update manifest with compressed size
        manifest['compressed_size'] = len(compressed)
        manifest['compression_ratio'] = round(
            (1 - len(compressed) / total_size) * 100, 2
        )
        manifest['compression_method'] = '7z'
        
        return compressed, manifest
    
    @staticmethod
    def decompress_files(zip_bytes):
        """
        Extract files from ZIP archive.
        
        Returns:
            List of (file_name, file_bytes) tuples, manifest dict
        """
        try:
            zip_buffer = io.BytesIO(zip_bytes)
            files = []
            manifest = None
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                # Extract manifest
                if 'manifest.json' in zf.namelist():
                    manifest_data = zf.read('manifest.json')
                    manifest = json.loads(manifest_data)
                
                # Extract files
                for file_info in zf.filelist:
                    if file_info.filename.startswith('files/'):
                        file_name = file_info.filename.replace('files/', '', 1)
                        file_bytes = zf.read(file_info.filename)
                        files.append((file_name, file_bytes))
            
            return files, manifest
        
        except Exception as e:
            raise ValueError(f"ZIP extraction failed: {str(e)}")
    
    @staticmethod
    def decompress_files_7z(sevenz_bytes):
        """
        Extract files from 7-Zip archive.
        
        Returns:
            List of (file_name, file_bytes) tuples, manifest dict
        """
        try:
            sevenz_buffer = io.BytesIO(sevenz_bytes)
            files = []
            manifest = None
            
            with py7zr.SevenZipFile(sevenz_buffer, 'r') as szf:
                # Extract manifest
                if 'manifest.json' in szf.getnames():
                    manifest_data = szf.read('manifest.json')['manifest.json']
                    manifest = json.loads(manifest_data)
                
                # Extract files
                for file_info in szf.getnames():
                    if file_info.startswith('files/'):
                        file_name = file_info.replace('files/', '', 1)
                        file_bytes = szf.read(file_info)[file_info]
                        files.append((file_name, file_bytes))
            
            return files, manifest
        
        except Exception as e:
            raise ValueError(f"7Z extraction failed: {str(e)}")
    
    @staticmethod
    def get_compression_info(original_size, compressed_size):
        """Calculate compression statistics."""
        return {
            'original_bytes': original_size,
            'compressed_bytes': compressed_size,
            'compression_ratio': round((1 - compressed_size / original_size) * 100, 2),
            'space_saved_bytes': original_size - compressed_size,
            'efficiency': f"{(1 - compressed_size / original_size) * 100:.1f}%"
        }


class FileSegmentation:
    """Handles segmentation of large payloads across multiple images."""
    
    SEGMENT_HEADER_SIZE = 16  # Bytes for segment metadata
    MAX_PAYLOAD_PER_IMAGE = 10 * 1024 * 1024  # 10MB per image (conservative)
    
    @staticmethod
    def calculate_segments_needed(payload_size):
        """Calculate number of images needed."""
        return (payload_size + FileSegmentation.MAX_PAYLOAD_PER_IMAGE - 1) // \
               FileSegmentation.MAX_PAYLOAD_PER_IMAGE
    
    @staticmethod
    def create_segment(payload, segment_index, total_segments, encryption_key):
        """Create a segment with metadata."""
        import struct
        
        header = struct.pack('>I I I 16s',
            segment_index,
            total_segments,
            len(payload),
            encryption_key[:16]  # Validation key
        )
        
        return header + payload
    
    @staticmethod
    def extract_segment(segment_data):
        """Extract segment metadata and payload."""
        import struct
        
        if len(segment_data) < FileSegmentation.SEGMENT_HEADER_SIZE:
            raise ValueError("Invalid segment header")
        
        header = segment_data[:FileSegmentation.SEGMENT_HEADER_SIZE]
        payload = segment_data[FileSegmentation.SEGMENT_HEADER_SIZE:]
        
        segment_index, total_segments, payload_size, validation_key = \
            struct.unpack('>I I I 16s', header)
        
        return {
            'segment_index': segment_index,
            'total_segments': total_segments,
            'payload_size': payload_size,
            'validation_key': validation_key,
            'payload': payload[:payload_size]
        }


# Example usage:
if __name__ == '__main__':
    # Test multi-file compression
    test_files = [
        ('document.txt', b'Hello World! This is a secret document.'),
        ('image.bin', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100),
        ('data.json', b'{"secret": "value"}'),
    ]
    
    compressed, manifest = MultiFileHandler.compress_files(test_files)
    print(f"Manifest: {manifest}")
    
    # Test extraction
    extracted, manifest = MultiFileHandler.decompress_files(compressed)
    print(f"Extracted {len(extracted)} files")
    
    # Test segmentation
    segments_needed = FileSegmentation.calculate_segments_needed(len(compressed))
    print(f"Segments needed: {segments_needed}")
