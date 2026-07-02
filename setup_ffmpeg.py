#!/usr/bin/env python3
"""
FFmpeg Setup Script
Downloads and extracts FFmpeg binaries, then configures pydub to use them.
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path

def setup_ffmpeg():
    """Download and set up FFmpeg."""
    
    # Define paths
    ffmpeg_dir = Path("D:/Desktop/ffmpeg")
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = ffmpeg_dir / "ffmpeg.zip"
    extract_dir = ffmpeg_dir / "extracted"
    
    print("=" * 70)
    print("FFmpeg Setup for StegoForge")
    print("=" * 70)
    
    # Check if FFmpeg is already available
    if shutil.which("ffmpeg"):
        print("✓ FFmpeg already available in PATH")
        return True
    
    print("\n1. Checking existing FFmpeg installation...")
    bin_dir = ffmpeg_dir / "bin"
    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    
    if ffmpeg_exe.exists():
        print(f"✓ Found FFmpeg at: {ffmpeg_exe}")
        # Add to PATH
        os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ['PATH']
        # Also configure pydub
        os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ['PATH']
        print("✓ Added to PATH")
        return True
    
    print("\n2. Downloading FFmpeg (236 MB)...")
    try:
        url = "https://github.com/GyanD/codexffmpeg/releases/download/8.1/ffmpeg-8.1-full_build.zip"
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 // total_size, 100)
            bar_len = 40
            filled = int(bar_len * percent // 100)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f"\r  [{bar}] {percent}%", end='', flush=True)
        
        urllib.request.urlretrieve(url, zip_path, download_progress)
        print("\n✓ Download complete")
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False
    
    print("\n3. Extracting FFmpeg...")
    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("✓ Extraction complete")
        
        # Find the ffmpeg.exe in extracted folder
        ffmpeg_found = False
        for root, dirs, files in os.walk(extract_dir):
            if 'ffmpeg.exe' in files:
                src_bin = Path(root)
                shutil.copytree(src_bin, bin_dir, dirs_exist_ok=True)
                ffmpeg_found = True
                print(f"✓ FFmpeg binaries copied to: {bin_dir}")
                break
        
        if not ffmpeg_found:
            print("✗ Could not find ffmpeg.exe in extracted files")
            return False
            
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return False
    
    print("\n4. Configuring for pydub...")
    try:
        # Add to PATH for current process
        os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ['PATH']
        
        # Also set FFMPEG_BIN environment variable
        os.environ['FFMPEG_BIN'] = str(ffmpeg_exe)
        
        # Configure pydub
        from pydub.utils import get_ffmpeg_path
        print(f"✓ FFmpeg path configured")
        
    except Exception as e:
        print(f"⚠ Warning: Could not auto-configure pydub: {e}")
    
    print("\n5. Verifying FFmpeg installation...")
    try:
        result = subprocess.run(
            [str(ffmpeg_exe), '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg verified: {version_line}")
            return True
        else:
            print(f"✗ FFmpeg verification failed")
            return False
            
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    # Clean up
    if Path("D:/Desktop/ffmpeg/ffmpeg.zip").exists():
        try:
            Path("D:/Desktop/ffmpeg/ffmpeg.zip").unlink()
            Path("D:/Desktop/ffmpeg/extracted").rmdir()
        except:
            pass
    
    success = setup_ffmpeg()
    
    if success:
        print("\n" + "=" * 70)
        print("✓ FFmpeg setup complete! Ready to use StegoForge audio features.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("✗ FFmpeg setup failed. Please install FFmpeg manually.")
        print("=" * 70)
        sys.exit(1)
