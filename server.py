"""
StegoForge v4.0 Enterprise Edition
Secure Steganography Platform with Cryptographic Protocols
"""

from flask import Flask, request, jsonify, send_file, session, render_template
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import logging
import os
import io
import struct
import hashlib
import zipfile
import json
import uuid
import time
import tempfile
from PIL import Image
from src.crypto import derive_key, encrypt, decrypt
from src.stego import embed_bytes_into_image, extract_bytes_from_image, calculate_max_payload
from src.multifile import MultiFileHandler, FileSegmentation
from src.steganalysis import SteganalysisDetector
from src.video_stego import VideoSteganography
from src.ecdh import ECDHKeyExchange, perform_key_exchange
from image_optimizer import ImageOptimizer
from audio_steganographer import AudioSteganographer
from advanced_encryption import AdvancedEncryption

# Try to import PQC, but allow graceful fallback if liboqs not available
try:
    from post_quantum_crypto import PostQuantumCrypto
    PQC_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    PQC_AVAILABLE = False
    logging.warning(f"Post-Quantum Crypto not available: {str(e)}")

# ===== CONFIGURATION =====
class Config:
    VERSION = '4.0.0'
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_PASSWORD_LENGTH = 256
    MAX_MESSAGE_LENGTH = 10000
    RATE_LIMIT_PER_MINUTE = 30
    REQUEST_TIMEOUT = 300  # 5 minutes

# ===== GLOBAL STATE =====
# Track failed attempts for self-destruct feature
# Key: image_hash, Value: current_failed_attempts
FAILED_ATTEMPTS = {}
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stegoforge.log')
    ]
)
logger = logging.getLogger(__name__)

# ===== FLASK APP =====
app = Flask(__name__, static_folder='public', static_url_path='/static')
CORS(app, 
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'],
     allow_headers=['Content-Type'],
     max_age=3600)

app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE

# ===== SECURITY MIDDLEWARE =====
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' cdn.tailwindcss.com"
    return response

# ===== RATE LIMITING =====
request_history = {}

def rate_limit(f):
    """Simple rate limiter."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        now = datetime.now()
        
        if client_ip not in request_history:
            request_history[client_ip] = []
        
        # Clean old requests (older than 1 minute)
        request_history[client_ip] = [t for t in request_history[client_ip] 
                                      if (now - t).seconds < 60]
        
        if len(request_history[client_ip]) >= Config.RATE_LIMIT_PER_MINUTE:
            logger.warning(f'Rate limit exceeded for {client_ip}')
            return jsonify({'error': 'Rate limit exceeded. Max 30 requests per minute.'}), 429
        
        request_history[client_ip].append(now)
        return f(*args, **kwargs)
    
    return decorated_function

# ===== VALIDATION =====
def validate_password(pwd):
    """Validate password constraints."""
    if not pwd or len(pwd) < 8:
        return False, 'Password must be at least 8 characters'
    if len(pwd) > Config.MAX_PASSWORD_LENGTH:
        return False, f'Password too long (max {Config.MAX_PASSWORD_LENGTH})'
    return True, ''

def validate_message(msg):
    """Validate message constraints."""
    if len(msg) > Config.MAX_MESSAGE_LENGTH:
        return False, f'Message too long (max {Config.MAX_MESSAGE_LENGTH} bytes)'
    return True, ''

def validate_aes_bits(bits):
    """Validate AES key length."""
    if bits not in [128, 192, 256]:
        return False, 'AES bits must be 128, 192, or 256'
    return True, ''

# ===== FEATURE HELPER FUNCTIONS =====

def remove_exif_data(image_buffer):
    """Remove EXIF metadata from image."""
    try:
        img = Image.open(image_buffer)
        # Create new image without EXIF
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)
        
        out_buffer = io.BytesIO()
        image_without_exif.save(out_buffer, format='PNG')
        out_buffer.seek(0)
        logger.info('EXIF data removed from output image')
        return out_buffer
    except Exception as e:
        logger.warning(f'EXIF removal failed: {str(e)}, continuing without removal')
        image_buffer.seek(0)
        return image_buffer

def apply_double_encryption(plaintext, password, aes_bits):
    """Apply double AES-256 encryption."""
    aes_key_bytes = aes_bits // 8
    
    # First encryption
    salt1 = os.urandom(16)
    key1 = derive_key(password.encode('utf-8'), salt1, aes_key_bytes)
    ciphertext1 = encrypt(key1, plaintext)
    
    # Second encryption with different salt
    salt2 = os.urandom(16)
    key2 = derive_key(password.encode('utf-8'), salt2, aes_key_bytes)
    ciphertext2 = encrypt(key2, ciphertext1)
    
    logger.info(f'Applied double encryption: {aes_bits}-bit AES')
    return ciphertext2, salt1, salt2

def get_message_expiry_marker(ttl_seconds):
    """Generate expiry marker with current timestamp."""
    expiry_time = int(time.time()) + ttl_seconds
    return struct.pack('>I', expiry_time)  # 4 bytes for expiry timestamp

# ===== API ROUTES (v1) =====

@app.route('/')
def serve_index():
    """Serve main UI."""
    logger.info('Serving index.html')
    return send_file('public/index.html', mimetype='text/html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'version': Config.VERSION,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/capacity', methods=['POST'])
@rate_limit
def api_capacity_check():
    """Evaluate capacity of carriers vs required payload size."""
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        carriers = data.get('carriers', [])
        payload_bytes = data.get('payload_size', 0)
        
        total_capacity_bytes = 0
        for w, h in carriers:
            total_capacity_bytes += (w * h * 3) // 8
            
        # Stego & Crypto Estimated Overhead:
        # AES-256 GCM (Double Encryption) -> approx 96 bytes
        # File headers + Stego length indicators -> ~104 bytes
        overhead = 200 
        required_bytes = payload_bytes + overhead
        
        percentage = (required_bytes / total_capacity_bytes * 100) if total_capacity_bytes > 0 else float('inf')
        can_fit = required_bytes <= total_capacity_bytes
        
        recommendations = []
        if not can_fit:
            if (required_bytes * 0.75) <= total_capacity_bytes:
                recommendations.append('7zip')
            recommendations.append('split')
            recommendations.append('lossy')
            
        return jsonify({
            'status': 'success',
            'available_bytes': total_capacity_bytes,
            'required_bytes': required_bytes,
            'percentage': round(percentage, 2),
            'fit': can_fit,
            'recommendations': recommendations
        })
    except Exception as e:
        logger.error(f'Capacity check error: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/encode-split', methods=['POST'])
@rate_limit
def api_encode_split():
    """Encode payload split across multiple carrier images."""
    try:
        # Validate inputs
        if 'images' not in request.files:
            return jsonify({'status': 'error', 'message': 'No carrier images provided'}), 400
        
        images = request.files.getlist('images')
        if len(images) < 1 or len(images) > 20:
            return jsonify({'status': 'error', 'message': 'Provide 1-20 carrier images'}), 400
        
        message = request.form.get('message', '')
        password = request.form.get('password', '')
        aes_bits = int(request.form.get('aes_bits', 256))
        compression_method = request.form.get('compression_method', 'zip')
        
        # Validate password and AES
        valid_pwd, pwd_msg = validate_password(password)
        if not valid_pwd:
            return jsonify({'status': 'error', 'message': pwd_msg}), 400
        
        valid_aes, aes_msg = validate_aes_bits(aes_bits)
        if not valid_aes:
            return jsonify({'status': 'error', 'message': aes_msg}), 400
        
        # Prepare payload
        if message:
            payload_bytes = message.encode('utf-8')
        else:
            # Handle file uploads for batch mode
            files = request.files.getlist('files')
            if not files:
                return jsonify({'status': 'error', 'message': 'No message or files provided'}), 400
            
            file_list = [(f.filename, f.read()) for f in files]
            if compression_method == '7z':
                payload_bytes, manifest = MultiFileHandler.compress_files_7z(file_list)
            else:
                payload_bytes, manifest = MultiFileHandler.compress_files(file_list)
        
        # Calculate segments needed
        segments_needed = FileSegmentation.calculate_segments_needed(len(payload_bytes))
        if segments_needed > len(images):
            return jsonify({
                'status': 'error', 
                'message': f'Need {segments_needed} images, but only {len(images)} provided'
            }), 400
        
        # Encrypt payload
        encrypted_payload, salt1, salt2 = apply_double_encryption(payload_bytes, password, aes_bits)
        
        # Create segments and embed
        output_images = []
        segment_size = len(encrypted_payload) // segments_needed
        encryption_key = derive_key(password.encode('utf-8'), salt1, 32)[:16]  # 16-byte key for validation
        
        for i in range(segments_needed):
            start = i * segment_size
            end = start + segment_size if i < segments_needed - 1 else len(encrypted_payload)
            segment_payload = encrypted_payload[start:end]
            
            segment_data = FileSegmentation.create_segment(
                segment_payload, i, segments_needed, encryption_key
            )
            
            # Embed segment into carrier image
            carrier_img = images[i]
            img_buffer = io.BytesIO()
            embed_bytes_into_image(carrier_img, segment_data, img_buffer)
            
            # Remove EXIF and prepare for download
            clean_buffer = remove_exif_data(img_buffer)
            output_images.append(clean_buffer.getvalue())
        
        # Create ZIP of all output images
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, img_data in enumerate(output_images):
                zf.writestr(f'stego_image_{idx+1}.png', img_data)
        
        zip_buffer.seek(0)
        logger.info(f'Split encoding completed: {segments_needed} segments across {len(images)} images')
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='stego_images_split.zip'
        )
        
    except Exception as e:
        logger.error(f'Split encoding error: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/encode', methods=['POST'])
@rate_limit
def api_encode_v1():
    """Embed secret content into carrier image."""
    try:
        # Validate inputs
        if 'image' not in request.files:
            logger.warning('Encode request: missing image file')
            return jsonify({'error': 'Image file required'}), 400
        
        password = request.form.get('password', '')
        message = request.form.get('message', '')
        aes_bits = request.form.get('aes_bits', '256')
        
        # Get advanced options
        remove_exif = request.form.get('remove_exif', '0') == '1'
        double_encrypt = request.form.get('double_encrypt', '0') == '1'
        self_destruct = request.form.get('self_destruct', '0') == '1'
        ttl_seconds = int(request.form.get('ttl_seconds', '3600'))
        max_attempts = int(request.form.get('max_attempts', '0'))
        compression_method = request.form.get('compression_method', 'zip')  # 'zip' or '7z'
        
        # Validate
        valid, msg = validate_password(password)
        if not valid:
            logger.warning(f'Encode request: invalid password - {msg}')
            return jsonify({'error': msg}), 400
        
        valid, msg = validate_message(message)
        if not valid:
            logger.warning(f'Encode request: invalid message - {msg}')
            return jsonify({'error': msg}), 400
        
        try:
            aes_bits = int(aes_bits)
        except:
            aes_bits = 256
        
        valid, msg = validate_aes_bits(aes_bits)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Encoding
        image_file = request.files['image']
        image_bytes = image_file.read()  # Read FileStorage into bytes
        message_bytes = message.encode('utf-8')
        decoy_password = request.form.get('decoy_password', '')
        decoy_message = request.form.get('decoy_message', '')
        
        flags_str = []
        if remove_exif:
            flags_str.append('EXIF-remove')
        if double_encrypt:
            flags_str.append('2x-AES')
        if self_destruct:
            flags_str.append('Expiry')
        
        logger.info(f'Starting encode: AES-{aes_bits}, payload_size={len(message_bytes)}, flags={flags_str}')
        
        aes_key_bytes = aes_bits // 8
        
        # ===== FEATURE IMPLEMENTATION =====
        
        # Double Encryption
        if double_encrypt:
            real_ciphertext, salt1, salt2 = apply_double_encryption(message_bytes, password, aes_bits)
            # Mark with flag that indicates double encryption
            has_double_enc = 1
            salt = salt1  # Use first salt as main salt
            alt_salt = salt2  # Store second salt
        else:
            has_double_enc = 0
            salt = os.urandom(16)
            key = derive_key(password.encode('utf-8'), salt, aes_key_bytes)
            real_ciphertext = encrypt(key, message_bytes)
            alt_salt = None
        
        # Message Expiry
        expiry_marker = b''
        if self_destruct:
            expiry_marker = get_message_expiry_marker(ttl_seconds)
            logger.info(f'Message expiry set to {ttl_seconds} seconds from now')
        
        has_decoy = 1 if (decoy_password and decoy_message) else 0
        aes_indicator = (aes_bits // 64) - 2
        
        # Build base payload - original format
        payload = struct.pack('>B B I 16s', 1, has_decoy, len(real_ciphertext), salt) + real_ciphertext
        
        logger.info(f'Payload structure (before flags):')
        logger.info(f'  Version: {payload[0]:02x}')
        logger.info(f'  has_decoy: {payload[1]:02x}')
        logger.info(f'  len bytes: {payload[2:6].hex()}')
        logger.info(f'  salt: {payload[6:22].hex()}')
        logger.info(f'  real_ciphertext length: {len(real_ciphertext)} bytes')
        logger.info(f'  base payload: {len(payload)} bytes')
        logger.info(f'Feature flags: has_double_enc={has_double_enc}, alt_salt={alt_salt.hex() if alt_salt else None}, self_destruct={self_destruct}')
        
        # NOW ADD FEATURE FLAGS AFTER BASE PAYLOAD
        # Double Encryption Marker
        if has_double_enc and alt_salt:
            payload += struct.pack('>B', 1) + alt_salt  # 1 byte flag + 16 bytes second salt
            logger.info(f'  Added double encryption marker (now {len(payload)} bytes)')
        
        # Message Expiry Marker  
        if self_destruct:
            expiry_time = int(time.time()) + ttl_seconds
            payload += struct.pack('>B I', 1, expiry_time)  # 1 byte flag + 4 bytes timestamp
            logger.info(f'  Added expiry marker: {expiry_time}')
        
        # Max Attempts Marker
        if max_attempts > 0:
            payload += struct.pack('>B H', 1, max_attempts) # 1 byte flag + 2 bytes max_attempts
            logger.info(f'  Added max attempts marker: {max_attempts}')
        
        if has_decoy:
            d_salt = os.urandom(16)
            d_key = derive_key(decoy_password.encode('utf-8'), d_salt, aes_key_bytes)
            d_ciphertext = encrypt(d_key, decoy_message.encode('utf-8'))
            payload += struct.pack('>I 16s', len(d_ciphertext), d_salt) + d_ciphertext
            logger.info('Decoy protocol activated')
        
        out_buffer = io.BytesIO()
        image_buffer = io.BytesIO(image_bytes)
        image_buffer.seek(0)  # Ensure file pointer is at beginning
        embed_bytes_into_image(image_buffer, payload, out_buffer)
        out_buffer.seek(0)
        
        # Remove EXIF if requested
        if remove_exif:
            out_buffer = remove_exif_data(out_buffer)
        
        logger.info(f'Encoding successful. Total payload: {len(payload)} bytes')
        
        return send_file(out_buffer, mimetype='image/png', as_attachment=True, 
                        download_name=f'stego_{int(datetime.now().timestamp())}.png')
    
    except Exception as e:
        logger.error(f'Encoding error: {str(e)}')
        return jsonify({'error': 'Encoding failed'}), 500

@app.route('/api/v1/decode', methods=['POST'])
@rate_limit
def api_decode_v1():
    """Extract and decrypt hidden content from stego image."""
    try:
        if 'image' not in request.files:
            logger.warning('Decode request: missing image file')
            return jsonify({'error': 'Image file required'}), 400
        
        password = request.form.get('password', '')
        
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        logger.info('Starting decode operation')
        
        image_file = request.files['image']
        image_file.seek(0)
        image_bytes = image_file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        image_file.seek(0)  # Reset for extraction
        data = extract_bytes_from_image(image_file)
        if not data or len(data) < 22:
            logger.warning('Decode: no valid payload found')
            return jsonify({'error': 'No hidden content detected'}), 400
        
        # Check version byte to detect batch-encoded images
        version = data[0]
        logger.info(f'Detected payload version: {version}')
        if version == 2:
            logger.warning('Decode: This is a batch-encoded image. Use decode-batch endpoint instead.')
            return jsonify({'error': 'This is a batch-encoded image. Please use the batch decode feature.'}), 400
        
        if version != 1:
            logger.warning(f'Decode: unsupported protocol version {version}')
            return jsonify({'error': 'Unsupported format version'}), 400
        
        try:
            has_decoy, real_len, real_salt = struct.unpack('>B I 16s', data[1:22])
            
            real_ct = data[22:22+real_len]
            offset = 22 + real_len
            
            # Check for double encryption marker (optional, only if flag=1)
            has_double_enc = 0
            alt_salt = None
            if len(data) > offset and data[offset] == 1:
                # Double encryption marker found
                if len(data) >= offset + 17:
                    has_double_enc = 1
                    alt_salt = data[offset+1:offset+17]
                    offset += 17
                    logger.info('Double encryption marker detected')
            
            # Check for expiry marker (optional, only if flag=1)
            has_expiry = 0
            if len(data) > offset and data[offset] == 1:
                # Expiry marker found
                if len(data) >= offset + 5:
                    has_expiry = 1
                    expiry_time = struct.unpack('>I', data[offset+1:offset+5])[0]
                    offset += 5
                    current_time = int(time.time())
                    if current_time > expiry_time:
                        logger.warning(f'Message expired at {expiry_time}')
                        return jsonify({'error': 'Message has expired'}), 403
                    logger.info(f'Message expires at {expiry_time}')
            
            # Check for max attempts marker (optional, only if flag=1)
            has_limit = 0
            max_limit = 0
            if len(data) > offset and data[offset] == 1:
                # Max attempts marker found
                if len(data) >= offset + 3:
                    has_limit = 1
                    max_limit = struct.unpack('>H', data[offset+1:offset+3])[0]
                    offset += 3
                    logger.info(f'Max attempts limit detected: {max_limit}')
                    
                    # Check if already locked
                    current_fails = FAILED_ATTEMPTS.get(image_hash, 0)
                    if current_fails >= max_limit:
                        logger.warning(f'Access denied: Max attempts ({max_limit}) exceeded for image {image_hash}')
                        return jsonify({'error': 'Message self-destructed: too many failed attempts'}), 403
            
            # Now offset points to optional decoy data
            key = derive_key(password.encode('utf-8'), real_salt, 32)
            
            # Handle double encryption - must decrypt in REVERSE order
            if has_double_enc and alt_salt:
                try:
                    logger.info(f"DEBUG: real_salt={real_salt.hex()}, alt_salt={alt_salt.hex()}")
                    logger.info(f"DEBUG: real_ct len={len(real_ct)}")
                    # Decrypt with key2 (salt2) FIRST to reverse the second encryption
                    key2 = derive_key(password.encode('utf-8'), alt_salt, 32)
                    intermediate = decrypt(key2, real_ct)
                    logger.info(f"DEBUG: derived intermediate len={len(intermediate)}")
                    # Then decrypt with key1 (salt1) to reverse the first encryption
                    plaintext = decrypt(key, intermediate)
                    logger.info('Decryption successful (double encryption, real password)')
                    return jsonify({'message': plaintext.decode('utf-8')}), 200
                except Exception as e:
                    import traceback
                    logger.warning(f'Double decryption failed: {str(e)}')
                    logger.warning(traceback.format_exc())

            else:
                try:
                    plaintext = decrypt(key, real_ct)
                    logger.info('Decryption successful (real password)')
                    return jsonify({'message': plaintext.decode('utf-8')}), 200
                
                except Exception as e:
                    logger.warning(f'Real password decryption failed: {str(e)}')
            
            # Try decoy if available
            if has_decoy:
                if len(data) >= offset + 20:
                    try:
                        d_len, d_salt = struct.unpack('>I 16s', data[offset:offset+20])
                        d_ct = data[offset+20:offset+20+d_len]
                        d_key = derive_key(password.encode('utf-8'), d_salt, 32)
                        plaintext = decrypt(d_key, d_ct)
                        logger.info('Decryption successful (decoy password)')
                        return jsonify({'message': plaintext.decode('utf-8')}), 200
                    except Exception as e:
                        logger.warning(f'Decoy decryption failed: {str(e)}')
            
            logger.warning('Decode: authentication failed - wrong password')
            
            # Increment failed attempts if limit exists
            if has_limit:
                FAILED_ATTEMPTS[image_hash] = FAILED_ATTEMPTS.get(image_hash, 0) + 1
                remaining = max_limit - FAILED_ATTEMPTS[image_hash]
                logger.info(f'Failed attempt {FAILED_ATTEMPTS[image_hash]}/{max_limit} for {image_hash}')
                if remaining <= 0:
                    return jsonify({'error': 'Authentication failed. Message self-destructed.'}), 403
                return jsonify({'error': f'Authentication failed. {remaining} attempts remaining.'}), 403

            return jsonify({'error': 'Authentication failed. Invalid password.'}), 403
        
        except struct.error as e:
            logger.error(f'Decode struct parsing error: {str(e)}')
            return jsonify({'error': 'Corrupted payload'}), 400
        except Exception as e:
            logger.error(f'Decode parsing error: {str(e)}')
            return jsonify({'error': 'Corrupted payload'}), 400
    
    except Exception as e:
        logger.error(f'Decode error: {str(e)}')
        return jsonify({'error': 'Decoding failed'}), 500

# ===== MULTI-FILE STEGANOGRAPHY =====

@app.route('/api/v1/encode-batch', methods=['POST'])
@rate_limit
def api_encode_batch_v1():
    """Embed multiple files into carrier image with compression."""
    try:
        # Debug: Log what files are in the request
        logger.debug(f'Batch encode request files keys: {list(request.files.keys())}')
        
        if 'image' not in request.files:
            logger.warning('Batch encode: missing image file')
            return jsonify({'error': 'Image file required'}), 400
        
        password = request.form.get('password', '')
        aes_bits = request.form.get('aes_bits', '256')
        compression_method = request.form.get('compression_method', 'zip')
        
        # Validate
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        try:
            aes_bits = int(aes_bits)
        except:
            aes_bits = 256
        
        valid, msg = validate_aes_bits(aes_bits)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Collect files
        files_list = []
        uploaded_files = request.files.getlist('files')
        
        logger.debug(f'Batch encode: getlist("files") returned {len(uploaded_files)} files')
        
        if len(uploaded_files) == 0:
            logger.warning('Batch encode: no files provided')
            return jsonify({'error': 'At least one file required'}), 400
        
        if len(uploaded_files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400
        
        if len(uploaded_files) > 1000:
            return jsonify({'error': 'Too many files (max 1000)'}), 400
        
        for uf in uploaded_files:
            if uf.filename == '':
                continue
            file_bytes = uf.read()
            files_list.append((uf.filename, file_bytes))
        
        if not files_list:
            return jsonify({'error': 'No valid files provided'}), 400
        
        logger.info(f'Batch encode: {len(files_list)} files, AES-{aes_bits}')
        
        try:
            # Read image bytes ONCE and keep as BytesIO
            image_file = request.files['image']
            image_bytes = image_file.read()
            
            # Calculate max capacity for clear early failure
            # Create fresh BytesIO for capacity check
            capacity_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(capacity_stream)
            max_bytes = calculate_max_payload(pil_image)
            
            total_payload_size = sum(len(b) for _, b in files_list)
            logger.info(f"Batch encode cover capacity: {max_bytes} bytes")
            
            # Note: We compare against uncompressed size first. Compression helps, 
            # but if uncompressed is 100x bigger than capacity, compression won't save it.
            if total_payload_size > max_bytes * 5: # Assuming max ~80% compression ratio
                 return jsonify({'error': f'Files too large ({total_payload_size / 1024:.1f} KB). Image max capacity is {(max_bytes / 1024):.1f} KB.'}), 400
            
            if compression_method == '7z':
                compressed_payload, manifest = MultiFileHandler.compress_files_7z(files_list)
            else:
                compressed_payload, manifest = MultiFileHandler.compress_files(files_list)
            logger.info(f'Compression complete ({compression_method}): {manifest["compressed_size"]} bytes ' \
                       f'(saved {manifest["total_size"] - manifest["compressed_size"]} bytes)')
            
            # Hard check on exact compressed size
            if len(compressed_payload) > max_bytes:
                return jsonify({'error': f'Image too small for payload. Requires {(len(compressed_payload) / 1024):.1f} KB, but image max capacity is {(max_bytes / 1024):.1f} KB.'}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        # Get advanced options
        remove_exif = request.form.get('remove_exif', '0') == '1'
        double_encrypt = request.form.get('double_encrypt', '0') == '1'
        self_destruct = request.form.get('self_destruct', '0') == '1'
        ttl_seconds = int(request.form.get('ttl_seconds', '3600'))
        max_attempts = int(request.form.get('max_attempts', '0'))

        # Encrypt and embed
        aes_key_bytes = aes_bits // 8
        
        if double_encrypt:
            ciphertext, salt1, salt2 = apply_double_encryption(compressed_payload, password, aes_bits)
            has_double_enc = 1
            salt = salt1
            alt_salt = salt2
        else:
            has_double_enc = 0
            salt = os.urandom(16)
            key = derive_key(password.encode('utf-8'), salt, aes_key_bytes)
            ciphertext = encrypt(key, compressed_payload)
            alt_salt = None

        logger.info(f'Encryption: aes_bits={aes_bits}, salt={salt.hex()}, ciphertext={len(ciphertext)} bytes')
        
        # Metadata: version(1) + file_count(2) + aes_ind(1) + salt(16) + cipher_len(4)
        payload = struct.pack('>B H B 16s I', 2, len(files_list), (aes_bits // 64) - 2, 
                             salt, len(ciphertext)) + ciphertext
        
        # ADD FEATURE FLAGS AFTER BASE PAYLOAD
        # Double Encryption Marker
        if has_double_enc and alt_salt:
            payload += struct.pack('>B', 1) + alt_salt  # 1 byte flag + 16 bytes second salt
        
        # Message Expiry Marker  
        if self_destruct:
            expiry_time = int(time.time()) + ttl_seconds
            payload += struct.pack('>B I', 1, expiry_time)  # 1 byte flag + 4 bytes timestamp
        
        # Max Attempts Marker
        if max_attempts > 0:
            payload += struct.pack('>B H', 1, max_attempts) # 1 byte flag + 2 bytes max_attempts
        
        # Embed into image - use BytesIO instead of FileStorage
        image_buffer = io.BytesIO(image_bytes)
        out_buffer = io.BytesIO()
        try:
            logger.info(f'Embedding payload into image buffer. Image size: {len(image_bytes)} bytes, Payload: {len(payload)} bytes')
            embed_bytes_into_image(image_buffer, payload, out_buffer)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        out_buffer.seek(0)
        
        logger.info(f'Batch encoding successful. Total payload: {len(payload)} bytes')
        
        response_buffer = io.BytesIO()
        response_buffer.write(out_buffer.getvalue())
        response_buffer.seek(0)
        
        return send_file(response_buffer, mimetype='image/png', as_attachment=True, 
                        download_name=f'stego_batch_{int(datetime.now().timestamp())}.png')
    
    except Exception as e:
        logger.error(f'Batch encoding error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/decode-batch', methods=['POST'])
@rate_limit
def api_decode_batch_v1():
    """Extract and decrypt multiple files from stego image."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Image file required'}), 400
        
        password = request.form.get('password', '')
        
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        logger.info('Starting batch decode')
        
        data = extract_bytes_from_image(request.files['image'])
        logger.info(f'Extracted data length: {len(data) if data else 0} bytes')
        
        if not data or len(data) < 24:
            logger.warning(f'Decode: invalid payload length - got {len(data) if data else 0}, need 24')
            return jsonify({'error': 'No valid batch payload found'}), 400
        
        try:
            logger.debug(f'First 24 bytes (hex): {data[:24].hex()}')
            version, file_count, aes_ind, salt, cipher_len = \
                struct.unpack('>B H B 16s I', data[:24])
            
            logger.info(f'Decoded header: version={version}, files={file_count}, aes_ind={aes_ind}, cipher_len={cipher_len}')
            logger.debug(f'Salt (hex): {salt.hex()}')
            
            if version != 2:
                logger.warning(f'Decode: version mismatch - got {version}, expected 2')
                return jsonify({'error': 'Not a batch-encoded image (version mismatch)'}), 400
            
            ciphertext = data[24:24+cipher_len]
            offset = 24 + cipher_len
            
            # Check for double encryption marker (optional, only if flag=1)
            has_double_enc = 0
            alt_salt = None
            if len(data) > offset and data[offset] == 1:
                if len(data) >= offset + 17:
                    has_double_enc = 1
                    alt_salt = data[offset+1:offset+17]
                    offset += 17
                    logger.info('Batch: Double encryption marker detected')
            
            # Check for expiry marker (optional, only if flag=1)
            if len(data) > offset and data[offset] == 1:
                if len(data) >= offset + 5:
                    expiry_time = struct.unpack('>I', data[offset+1:offset+5])[0]
                    offset += 5
                    if int(time.time()) > expiry_time:
                        return jsonify({'error': 'Message has expired'}), 403
            
            # Check for max attempts marker (optional, only if flag=1)
            has_limit = 0
            max_limit = 0
            image_hash = hashlib.sha256(request.files['image'].read()).hexdigest()
            request.files['image'].seek(0) # Reset after hashing
            
            if len(data) > offset and data[offset] == 1:
                if len(data) >= offset + 3:
                    has_limit = 1
                    max_limit = struct.unpack('>H', data[offset+1:offset+3])[0]
                    offset += 3
                    
                    current_fails = FAILED_ATTEMPTS.get(image_hash, 0)
                    if current_fails >= max_limit:
                        return jsonify({'error': 'Message self-destructed: too many failed attempts'}), 403

            # Recover AES key size from aes_ind: aes_bits = (aes_ind + 2) * 64
            aes_key_bytes = ((aes_ind + 2) * 64) // 8
            key = derive_key(password.encode('utf-8'), salt, aes_key_bytes)
            
            try:
                if has_double_enc and alt_salt:
                    key2 = derive_key(password.encode('utf-8'), alt_salt, aes_key_bytes)
                    intermediate = decrypt(key2, ciphertext)
                    compressed_payload = decrypt(key, intermediate)
                else:
                    compressed_payload = decrypt(key, ciphertext)
                
                logger.info(f'Decryption successful: {file_count} files')
            except Exception as e:
                if has_limit:
                    FAILED_ATTEMPTS[image_hash] = FAILED_ATTEMPTS.get(image_hash, 0) + 1
                    remaining = max_limit - FAILED_ATTEMPTS[image_hash]
                    if remaining <= 0:
                        return jsonify({'error': 'Authentication failed. Message self-destructed.'}), 403
                    return jsonify({'error': f'Authentication failed. {remaining} attempts remaining.'}), 403
                return jsonify({'error': 'Invalid password'}), 403
            
            # Decompress
            try:
                logger.info(f'Starting decompression of {len(compressed_payload)} bytes')
                # Try ZIP first, then 7Z if it fails
                try:
                    files, manifest = MultiFileHandler.decompress_files(compressed_payload)
                    logger.info(f'ZIP decompression complete: {len(files)} files extracted')
                except ValueError:
                    # Try 7Z
                    files, manifest = MultiFileHandler.decompress_files_7z(compressed_payload)
                    logger.info(f'7Z decompression complete: {len(files)} files extracted')
            except ValueError as e:
                logger.error(f'Decompression failed: {str(e)}, payload length={len(compressed_payload)}')
                return jsonify({'error': f'Decompression failed: {str(e)}'}), 400
            except Exception as e:
                logger.error(f'Decompression error: {str(e)}, payload length={len(compressed_payload)}')
                return jsonify({'error': f'Decompression error: {str(e)}'}), 400
            
            # Create ZIP response
            zip_buffer = io.BytesIO()
            import zipfile
            import json as json_module
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add manifest as JSON
                zf.writestr('manifest.json', json_module.dumps(manifest, indent=2))
                # Add extracted files
                for file_name, file_bytes in files:
                    zf.writestr(file_name, file_bytes)
            
            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True,
                           download_name=f'extracted_{int(datetime.now().timestamp())}.zip')
        
        except struct.error as e:
            logger.error(f'Struct unpack error: {str(e)}, data length={len(data) if data else 0}')
            return jsonify({'error': f'Invalid payload format: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Batch decode error: {str(e)}')
        return jsonify({'error': 'Batch decoding failed'}), 500

@app.route('/api/v1/decode-split', methods=['POST'])
@rate_limit
def api_decode_split():
    """Decode payload split across multiple images."""
    try:
        images = request.files.getlist('images')
        if len(images) < 1 or len(images) > 20:
            return jsonify({'status': 'error', 'message': 'Provide 1-20 images'}), 400
        
        password = request.form.get('password', '')
        
        # Validate password
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'status': 'error', 'message': msg}), 400
        
        segments = []
        total_segments = None
        encryption_key = None
        
        for img_file in images:
            img_file.seek(0)
            data = extract_bytes_from_image(img_file)
            if not data:
                continue
            
            # Extract segment
            segment_info = FileSegmentation.extract_segment(data)
            segments.append(segment_info)
            
            if total_segments is None:
                total_segments = segment_info['total_segments']
                encryption_key = segment_info['validation_key']
            elif segment_info['total_segments'] != total_segments:
                return jsonify({'status': 'error', 'message': 'Inconsistent segment data'}), 400
        
        if not segments:
            return jsonify({'status': 'error', 'message': 'No valid segments found'}), 400
        
        # Sort segments by index
        segments.sort(key=lambda x: x['segment_index'])
        
        # Check if we have all segments
        if len(segments) != total_segments:
            return jsonify({'status': 'error', 'message': f'Missing segments. Found {len(segments)}/{total_segments}'}), 400
        
        # Reassemble payload
        payload_bytes = b''.join(seg['payload'] for seg in segments)
        
        # Decrypt
        try:
            # For split images, we use double encryption by default
            salt1 = encryption_key[:16]
            salt2 = encryption_key[16:] if len(encryption_key) > 16 else os.urandom(16)
            
            key2 = derive_key(password.encode('utf-8'), salt2, 32)
            intermediate = decrypt(key2, payload_bytes)
            key1 = derive_key(password.encode('utf-8'), salt1, 32)
            decrypted_payload = decrypt(key1, intermediate)
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'Decryption failed'}), 400
        
        # Try to decompress
        try:
            # Try ZIP first
            files, manifest = MultiFileHandler.decompress_files(decrypted_payload)
        except ValueError:
            # Try 7Z
            files, manifest = MultiFileHandler.decompress_files_7z(decrypted_payload)
        
        # Create response ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_name, file_bytes in files:
                zf.writestr(file_name, file_bytes)
        
        zip_buffer.seek(0)
        logger.info(f'Split decode completed: {len(files)} files from {len(images)} images')
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='split_decoded_files.zip'
        )
        
    except Exception as e:
        logger.error(f'Split decode error: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/batch/info', methods=['GET'])
@rate_limit
def api_batch_info():
    """Get batch processing capabilities."""
    return jsonify({
        'max_files_per_batch': 1000,
        'max_single_file_size': '100MB',
        'max_total_size': '500MB',
        'compression_ratio': '60-80%',
        'supported_formats': 'Any binary format',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/analyze', methods=['POST'])
@rate_limit
def api_analyze_v1():
    """Analyze payload robustness against attacks."""
    try:
        if 'image' not in request.files or 'password' not in request.form:
            return jsonify({'error': 'Image and password required'}), 400
        
        image_file = request.files['image']
        password = request.form.get('password')
        
        logger.info('Starting robustness analysis')
        
        jpeg_survived = False
        crop_survived = False
        
        # Test 1: JPEG Compression
        try:
            img = Image.open(image_file)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            img_jpeg = Image.open(buffer).convert('RGB')
            buffer2 = io.BytesIO()
            img_jpeg.save(buffer2, format='PNG')
            buffer2.seek(0)
            
            data = extract_bytes_from_image(buffer2)
            if data and len(data) > 22:
                _, _, _, real_len, real_salt = struct.unpack('>B B B I 16s', data[:22])
                real_ct = data[22:22+real_len]
                key = derive_key(password.encode('utf-8'), real_salt, 32)
                try:
                    decrypt(key, real_ct)
                    jpeg_survived = True
                    logger.info('JPEG compression: survived')
                except:
                    logger.info('JPEG compression: failed')
        except Exception as e:
            logger.warning(f'JPEG test error: {str(e)}')
        
        # Test 2: Cropping Attack
        try:
            image_file.seek(0)
            img = Image.open(image_file)
            w, h = img.size
            crop_box = (w//10, h//10, w*9//10, h*9//10)
            img_crop = img.crop(crop_box).convert('RGB')
            buffer3 = io.BytesIO()
            img_crop.save(buffer3, format='PNG')
            buffer3.seek(0)
            
            data = extract_bytes_from_image(buffer3)
            if data and len(data) > 22:
                crop_survived = True
                logger.info('Cropping attack: survived')
        except Exception as e:
            logger.warning(f'Cropping test error: {str(e)}')
        
        robustness_score = int((jpeg_survived + crop_survived) * 50)
        logger.info(f'Analysis complete. Robustness score: {robustness_score}%')
        
        return jsonify({
            'jpeg_compression_attack': 'Survived' if jpeg_survived else 'Failed',
            'cropping_attack': 'Survived' if crop_survived else 'Failed',
            'robustness_score': robustness_score,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'Analysis error: {str(e)}')
        return jsonify({'error': 'Analysis failed'}), 500

@app.route('/api/v1/preview', methods=['POST'])
@rate_limit
def api_preview_v1():
    """Generate stealth visualization heatmap."""
    try:
        if 'original' not in request.files or 'encoded' not in request.files:
            return jsonify({'error': 'Both original and encoded images required'}), 400
        
        logger.info('Generating stealth preview')
        
        original = Image.open(request.files['original']).convert('RGB')
        encoded = Image.open(request.files['encoded']).convert('RGB')
        
        if original.size != encoded.size:
            return jsonify({'error': 'Image dimensions must match'}), 400
        
        orig_pixels = list(original.getdata())
        enc_pixels = list(encoded.getdata())
        
        changed_count = sum(1 for o, e in zip(orig_pixels, enc_pixels) if o != e)
        total_pixels = len(orig_pixels)
        visibility = (changed_count / total_pixels * 100) if total_pixels > 0 else 0
        
        # Generate heatmap
        heatmap = Image.new('RGB', original.size)
        hm_data = [(255, 0, 0) if o != e else (0, 100, 0) 
                   for o, e in zip(orig_pixels, enc_pixels)]
        heatmap.putdata(hm_data)
        
        hm_buffer = io.BytesIO()
        heatmap.save(hm_buffer, format='PNG')
        hm_buffer.seek(0)
        
        import base64
        heatmap_b64 = base64.b64encode(hm_buffer.getvalue()).decode()
        
        logger.info(f'Preview complete. Visibility: {visibility:.2f}%')
        
        return jsonify({
            'visibility_percent': round(visibility, 2),
            'invisibility_score': round(100 - visibility, 2),
            'changed_pixels': changed_count,
            'total_pixels': total_pixels,
            'heatmap_b64': heatmap_b64,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'Preview error: {str(e)}')
        return jsonify({'error': 'Preview generation failed'}), 500

# ===== ADVANCED STEGANALYSIS =====
@app.route('/api/v1/steganalysis', methods=['POST'])
@rate_limit
def api_steganalysis_v1():
    """Advanced ML-based steganalysis detection."""
    try:
        if 'image' not in request.files:
            logger.warning('Steganalysis: missing image file')
            return jsonify({'error': 'Image file required'}), 400
        
        logger.info('Starting advanced steganalysis')
        
        image_file = request.files['image']
        detector = SteganalysisDetector()
        
        # Run analysis
        result = detector.analyze(image_file)
        
        logger.info(f'Steganalysis complete. Probability: {result["stego_probability"]:.3f}')
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'Steganalysis error: {str(e)}')
        return jsonify({'error': 'Steganalysis failed'}), 500

# ===== VIDEO STEGANOGRAPHY =====
@app.route('/api/v1/video/embed', methods=['POST'])
@rate_limit
def api_video_embed_v1():
    """Embed message or files into video frames."""
    try:
        if 'video' not in request.files:
            logger.warning('Video embed: missing video file')
            return jsonify({'error': 'Video file required'}), 400
        
        if 'message' not in request.form and 'payload' not in request.files:
            return jsonify({'error': 'Message or payload required'}), 400
        
        password = request.form.get('password', '')
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        logger.info('Starting video embedding')
        
        # Prepare payload
        if 'message' in request.form:
            message = request.form.get('message', '')
            payload = message.encode('utf-8')
        else:
            payload = request.files['payload'].read()
        
        # Encrypt payload
        salt = os.urandom(16)
        key = derive_key(password.encode('utf-8'), salt, 32)
        ciphertext = encrypt(key, payload)
        
        # Embed frame count header
        frame_count = int(request.form.get('frames', '10'))
        encrypted_payload = struct.pack('>I 16s I', len(payload), salt, len(ciphertext)) + ciphertext
        
        # Embed in video
        video_handler = VideoSteganography()
        
        if not video_handler.has_ffmpeg:
            return jsonify({
                'warning': 'FFmpeg not available - using frame-by-frame method',
                'ffmpeg_required': True,
                'message': 'Install FFmpeg to enable video steganography'
            }), 501
        
        try:
            video_file = request.files['video']
            output_video = video_handler.embed_in_video(video_file, encrypted_payload, frame_count)
            
            logger.info(f'Video embedding successful. Payload: {len(encrypted_payload)} bytes')
            
            return send_file(
                io.BytesIO(output_video),
                mimetype='video/mp4',
                as_attachment=True,
                download_name=f'stego_video_{int(datetime.now().timestamp())}.mp4'
            )
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f'Video embed error: {str(e)}')
        return jsonify({'error': 'Video embedding failed'}), 500

@app.route('/api/v1/video/extract', methods=['POST'])
@rate_limit
def api_video_extract_v1():
    """Extract embedded message or files from video."""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video file required'}), 400
        
        password = request.form.get('password', '')
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        logger.info('Starting video extraction')
        
        video_handler = VideoSteganography()
        
        if not video_handler.has_ffmpeg:
            return jsonify({'error': 'FFmpeg not available'}), 501
        
        try:
            video_file = request.files['video']
            encrypted_payload = video_handler.extract_from_video(video_file)
            
            if len(encrypted_payload) < 36:
                return jsonify({'error': 'No valid embedded data found'}), 400
            
            # Parse header
            payload_len, salt, cipher_len = struct.unpack('>I 16s I', encrypted_payload[:36])
            ciphertext = encrypted_payload[36:36+cipher_len]
            
            # Decrypt
            key = derive_key(password.encode('utf-8'), salt, 32)
            try:
                plaintext = decrypt(key, ciphertext)
                message = plaintext.decode('utf-8')
                
                logger.info(f'Extraction successful: {len(plaintext)} bytes')
                return jsonify({'message': message}), 200
            
            except Exception:
                logger.warning('Video extract: authentication failed')
                return jsonify({'error': 'Invalid password'}), 403
        
        except Exception as e:
            logger.error(f'Extraction error: {str(e)}')
            return jsonify({'error': 'Extraction failed'}), 500
    
    except Exception as e:
        logger.error(f'Video extract error: {str(e)}')
        return jsonify({'error': 'Video extraction failed'}), 500

@app.route('/api/v1/video/info', methods=['POST'])
@rate_limit
def api_video_info_v1():
    """Get information about video file."""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video file required'}), 400
        
        video_file = request.files['video']
        video_handler = VideoSteganography()
        info = video_handler.get_video_info(video_file)
        
        return jsonify({
            'filename': video_file.filename,
            'supported_formats': video_handler.SUPPORTED_FORMATS,
            'max_video_size': f'{video_handler.MAX_VIDEO_SIZE // (1024*1024)}MB',
            'ffmpeg_available': video_handler.has_ffmpeg,
            'video_info': info
        }), 200
    
    except Exception as e:
        logger.error(f'Video info error: {str(e)}')
        return jsonify({'error': 'Failed to get video info'}), 500

# ===== ECDH KEY EXCHANGE =====
@app.route('/api/v1/ecdh/curves', methods=['GET'])
@rate_limit
def api_ecdh_curves_v1():
    """List available ECDH curves."""
    try:
        curves = ECDHKeyExchange.get_available_curves()
        logger.info(f'Listed {len(curves)} available ECDH curves')
        return jsonify({
            'available_curves': curves,
            'default_curve': 'p256',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'ECDH curves error: {str(e)}')
        return jsonify({'error': 'Failed to list curves'}), 500

@app.route('/api/v1/ecdh/generate', methods=['POST'])
@rate_limit
def api_ecdh_generate_v1():
    """Generate ECDH keypair."""
    try:
        curve = request.form.get('curve', 'p256').lower()
        
        logger.info(f'Generating ECDH keypair for curve: {curve}')
        
        try:
            ecdh = ECDHKeyExchange(curve)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        private_key, public_key = ecdh.generate_keypair()
        
        # Return keys as base64 for easy transmission
        import base64
        private_b64 = base64.b64encode(private_key if isinstance(private_key, bytes) 
                                       else private_key.encode()).decode()
        public_b64 = base64.b64encode(public_key if isinstance(public_key, bytes) 
                                      else public_key.encode()).decode()
        
        logger.info(f'Generated keypair for {curve}')
        
        return jsonify({
            'success': True,
            'curve': curve,
            'curve_info': ecdh.get_curve_info(),
            'private_key': private_b64,
            'public_key': public_b64,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'ECDH generation error: {str(e)}')
        return jsonify({'error': 'Keypair generation failed'}), 500

@app.route('/api/v1/ecdh/exchange', methods=['POST'])
@rate_limit
def api_ecdh_exchange_v1():
    """Compute shared secret from public key."""
    try:
        if 'private_key' not in request.form or 'peer_public_key' not in request.form:
            return jsonify({'error': 'Private and public keys required'}), 400
        
        curve = request.form.get('curve', 'p256').lower()
        
        import base64
        
        try:
            private_key_b64 = request.form.get('private_key')
            peer_public_key_b64 = request.form.get('peer_public_key')
            
            # Decode from base64
            private_key = base64.b64decode(private_key_b64)
            peer_public_key = base64.b64decode(peer_public_key_b64)
            
            logger.info(f'Computing shared secret for curve: {curve}')
            
            ecdh = ECDHKeyExchange(curve)
            shared_secret = ecdh.compute_shared_secret(private_key, peer_public_key)
            
            shared_secret_b64 = base64.b64encode(shared_secret).decode()
            
            logger.info(f'Shared secret computed ({len(shared_secret)} bytes)')
            
            return jsonify({
                'success': True,
                'curve': curve,
                'shared_secret': shared_secret_b64,
                'secret_length': len(shared_secret),
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        except ValueError as e:
            return jsonify({'error': f'Invalid key format: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'ECDH exchange error: {str(e)}')
        return jsonify({'error': 'Key exchange failed'}), 500

@app.route('/api/v1/ecdh/test', methods=['POST'])
@rate_limit
def api_ecdh_test_v1():
    """Test ECDH key exchange (simulation for verification)."""
    try:
        curve = request.form.get('curve', 'p256').lower()
        
        logger.info(f'Testing ECDH exchange for curve: {curve}')
        
        result = perform_key_exchange(curve)
        
        if result['success']:
            logger.info(f'ECDH test successful for {curve}')
        else:
            logger.warning(f'ECDH test failed: {result.get("error")}')
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'ECDH test error: {str(e)}')
        return jsonify({'error': 'Test failed'}), 500

# ===== CAPACITY MANAGEMENT ENDPOINTS =====

@app.route('/api/v1/capacity-check', methods=['POST'])
@rate_limit
def api_capacity_check_v1():
    """Check capacity for single or multiple carrier images."""
    try:
        if 'image' not in request.files and 'images' not in request.files:
            logger.warning('Capacity check: no image provided')
            return jsonify({'error': 'At least one image required'}), 400
        
        images_list = []
        
        # Handle single image
        if 'image' in request.files:
            img = request.files['image']
            images_list.append(img)
        
        # Handle multiple images
        if 'images' in request.files:
            images_list.extend(request.files.getlist('images'))
        
        if len(images_list) == 0:
            return jsonify({'error': 'No valid images provided'}), 400
        
        if len(images_list) > 20:
            return jsonify({'error': 'Maximum 20 carrier images allowed'}), 400
        
        # Calculate capacity for each image
        capacities = []
        total_capacity = 0
        
        for idx, image_file in enumerate(images_list):
            try:
                img = Image.open(image_file)
                img.verify()
                
                # Re-open after verify (verify closes the file)
                image_file.seek(0)
                img = Image.open(image_file)
                
                capacity = calculate_max_payload(img)
                capacities.append({
                    'image_index': idx,
                    'filename': image_file.filename,
                    'width': img.width,
                    'height': img.height,
                    'capacity_bytes': capacity,
                    'capacity_mb': round(capacity / (1024 * 1024), 2)
                })
                total_capacity += capacity
                
                logger.info(f'Image {idx}: {img.width}x{img.height}, capacity: {capacity} bytes')
                
            except Exception as e:
                logger.warning(f'Invalid image {idx}: {str(e)}')
                return jsonify({'error': f'Invalid image at index {idx}: {str(e)}'}), 400
        
        return jsonify({
            'success': True,
            'image_count': len(capacities),
            'total_capacity_bytes': total_capacity,
            'total_capacity_mb': round(total_capacity / (1024 * 1024), 2),
            'images': capacities
        }), 200
    
    except Exception as e:
        logger.error(f'Capacity check error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/capacity-info', methods=['POST'])
@rate_limit
def api_capacity_info_v1():
    """Get detailed capacity information for images including compression estimates."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Image required'}), 400
        
        image_file = request.files['image']
        
        try:
            img = Image.open(image_file)
            img.verify()
            
            image_file.seek(0)
            img = Image.open(image_file)
            
            capacity = calculate_max_payload(img)
            
            # Estimate compression ratios for payload
            compression_estimates = {
                'no_compression': capacity,
                'light_compression_50': int(capacity * 1.5),  # 50% larger payload possible
                'medium_compression_65': int(capacity * 2.0),  # 65% compression
                'aggressive_compression_75': int(capacity * 3.5)  # 75% compression
            }
            
            return jsonify({
                'success': True,
                'image': {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format
                },
                'raw_capacity': capacity,
                'raw_capacity_mb': round(capacity / (1024 * 1024), 3),
                'compression_estimates': compression_estimates,
                'message': f'Image can hold {capacity} bytes without compression'
            }), 200
            
        except Exception as e:
            logger.warning(f'Invalid image: {str(e)}')
            return jsonify({'error': f'Invalid image: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Capacity info error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/encode-multi-carrier', methods=['POST'])
@rate_limit
def api_encode_multi_carrier_v1():
    """Distribute payload across multiple carrier images."""
    try:
        # Get carrier images
        carrier_images = []
        idx = 0
        while f'carrier_{idx}' in request.files:
            carrier_images.append(request.files[f'carrier_{idx}'])
            idx += 1
        
        if len(carrier_images) == 0:
            logger.warning('Multi-carrier encode: no carrier images')
            return jsonify({'error': 'At least one carrier image required'}), 400
        
        if len(carrier_images) > 20:
            return jsonify({'error': 'Maximum 20 carrier images allowed'}), 400
        
        # Get files to embed
        uploaded_files = request.files.getlist('files')
        if len(uploaded_files) == 0:
            return jsonify({'error': 'At least one file required'}), 400
        
        password = request.form.get('password', '')
        aes_bits = request.form.get('aes_bits', '256')
        
        # Validate
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        try:
            aes_bits = int(aes_bits)
        except:
            aes_bits = 256
        
        valid, msg = validate_aes_bits(aes_bits)
        if not valid:
            return jsonify({'error': msg}), 400
        
        logger.info(f'Multi-carrier encode: {len(carrier_images)} carriers, {len(uploaded_files)} files, AES-{aes_bits}')
        
        # Collect files
        files_list = []
        for uf in uploaded_files:
            if uf.filename == '':
                continue
            file_bytes = uf.read()
            files_list.append((uf.filename, file_bytes))
        
        if not files_list:
            return jsonify({'error': 'No valid files provided'}), 400
        
        # Load and validate carrier images
        carrier_imgs = []
        carrier_capacities = []
        
        for idx, carrier_file in enumerate(carrier_images):
            try:
                img = Image.open(carrier_file)
                img.verify()
                
                carrier_file.seek(0)
                img = Image.open(carrier_file)
                
                capacity = calculate_max_payload(img)
                carrier_imgs.append(img)
                carrier_capacities.append(capacity)
                
                logger.info(f'Carrier {idx}: {img.width}x{img.height}, capacity: {capacity} bytes')
                
            except Exception as e:
                logger.warning(f'Invalid carrier image {idx}: {str(e)}')
                return jsonify({'error': f'Invalid carrier image {idx}'}), 400
        
        total_capacity = sum(carrier_capacities)
        
        # Compress all files into one payload
        try:
            compressed_payload, manifest = MultiFileHandler.compress_files(files_list)
            logger.info(f'Files compressed: {manifest["compressed_size"]} bytes from {manifest["total_size"]} bytes')
        except Exception as e:
            logger.error(f'Compression error: {str(e)}')
            return jsonify({'error': f'Compression failed: {str(e)}'}), 400
        
        payload_size = len(compressed_payload)
        
        # Check if total capacity is sufficient (accounting for encryption overhead ~32 bytes per carrier)
        overhead_per_carrier = 32
        total_overhead = len(carrier_imgs) * overhead_per_carrier
        available_capacity = total_capacity - total_overhead
        
        if payload_size > available_capacity:
            required_carriers = (payload_size + total_overhead) / (total_capacity / len(carrier_imgs))
            logger.warning(f'Insufficient capacity: need ~{required_carriers:.1f} carriers')
            return jsonify({
                'error': f'Files too large. Total payload: {payload_size} bytes, available capacity: {available_capacity} bytes',
                'required_carriers': int(required_carriers) + 1,
                'current_carriers': len(carrier_imgs)
            }), 400
        
        # Get advanced options
        remove_exif = request.form.get('remove_exif', '0') == '1'
        double_encrypt = request.form.get('double_encrypt', '0') == '1'
        self_destruct = request.form.get('self_destruct', '0') == '1'
        ttl_seconds = int(request.form.get('ttl_seconds', '3600'))
        max_attempts = int(request.form.get('max_attempts', '0'))

        # Distribute payload across carriers
        aes_key_bytes = aes_bits // 8
        stego_images = []
        
        try:
            # Split compressed payload across carriers - simple linear distribution
            bytes_per_carrier = (payload_size + len(carrier_imgs) - 1) // len(carrier_imgs)
            payload_chunks = []
            
            for idx in range(len(carrier_imgs)):
                start_idx = idx * bytes_per_carrier
                end_idx = min(start_idx + bytes_per_carrier, payload_size)
                chunk = compressed_payload[start_idx:end_idx]
                payload_chunks.append(chunk)
            
            logger.info(f'Payload split into {len(payload_chunks)} chunks for {len(carrier_imgs)} carriers')
            
            # Embed each chunk into its carrier with encryption
            for carrier_idx, (carrier_img, chunk) in enumerate(zip(carrier_imgs, payload_chunks)):
                logger.info(f'Encoding carrier {carrier_idx}: {len(chunk)} bytes')
                
                # Encrypt each chunk
                if double_encrypt:
                    ciphertext, salt1, salt2 = apply_double_encryption(chunk, password, aes_bits)
                    has_double_enc = 1
                    salt = salt1
                    alt_salt = salt2
                else:
                    has_double_enc = 0
                    salt = os.urandom(16)
                    key = derive_key(password.encode('utf-8'), salt, aes_key_bytes)
                    ciphertext = encrypt(key, chunk)
                    alt_salt = None
                
                # Metadata: version(1) + carrier_index(1) + total_carriers(1) + 
                #           aes_ind(1) + salt(16) + cipher_len(4)
                payload = struct.pack('>B B B B 16s I', 
                                     3,  # version (multi-carrier)
                                     carrier_idx,
                                     len(carrier_imgs),
                                     (aes_bits // 64) - 2,
                                     salt, 
                                     len(ciphertext)) + ciphertext
                
                # ADD FEATURE FLAGS
                if has_double_enc and alt_salt:
                    payload += struct.pack('>B', 1) + alt_salt
                
                if self_destruct:
                    expiry_time = int(time.time()) + ttl_seconds
                    payload += struct.pack('>B I', 1, expiry_time)
                
                if max_attempts > 0:
                    payload += struct.pack('>B H', 1, max_attempts)
                
                # Embed
                carrier_buffer = io.BytesIO()
                carrier_img.save(carrier_buffer, format='PNG')
                carrier_buffer.seek(0)
                
                out_buffer = io.BytesIO()
                embed_bytes_into_image(carrier_buffer, payload, out_buffer)
                out_buffer.seek(0)
                
                stego_images.append(out_buffer.getvalue())
            
            logger.info(f'Successfully encoded {len(stego_images)} stego images')
            
        except Exception as e:
            logger.error(f'Embedding error: {str(e)}')
            return jsonify({'error': f'Embedding failed: {str(e)}'}), 400
        
        # Create ZIP file with all stego images
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, stego_data in enumerate(stego_images):
                    zf.writestr(f'stego_carrier_{idx}.png', stego_data)
            
            zip_buffer.seek(0)
            
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True,
                           download_name=f'stego_multi_{int(datetime.now().timestamp())}.zip')
            
        except Exception as e:
            logger.error(f'ZIP creation error: {str(e)}')
            return jsonify({'error': 'Failed to create output file'}), 500
    
    except Exception as e:
        logger.error(f'Multi-carrier encoding error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== IMAGE OPTIMIZATION ENDPOINT =====
@app.route('/api/v1/optimize', methods=['POST'])
@rate_limit
def api_optimize_image():
    """Analyze and score carrier image for steganography suitability."""
    try:
        if 'image' not in request.files:
            logger.warning('Optimize request: missing image file')
            return jsonify({'error': 'Image file required'}), 400
        
        image_file = request.files['image']
        logger.info(f'Starting image optimization analysis: {image_file.filename}')
        
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                image_file.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                # Initialize optimizer and score image
                optimizer = ImageOptimizer()
                score = optimizer.score_image(tmp_path)
                
                if not score:
                    return jsonify({'error': 'Failed to analyze image'}), 400
                
                # Convert score to response format
                score_dict = score.to_dict()
                
                # Determine risk levels
                entropy_risk = 'Low' if 4.0 <= score.entropy <= 7.8 else 'Medium' if score.entropy > 3.0 else 'High'
                compression_risk = 'Low' if score.compression_ratio < 50 else 'Medium'
                complexity_risk = 'Low' if score.complexity > 60 else 'Medium' if score.complexity > 40 else 'High'
                
                # Generate recommendations
                recommendations = []
                if score.entropy < 3.0:
                    recommendations.append('Consider using images with more visual complexity or gradients')
                elif score.entropy > 7.8:
                    recommendations.append('High entropy - excellent for hiding data')
                
                if score.complexity < 40:
                    recommendations.append('Image has low texture complexity - try images with more detail')
                elif score.complexity > 80:
                    recommendations.append('Image has excellent texture variation for carrier use')
                
                if score.compression_ratio > 80:
                    recommendations.append('Image compresses well - already contains varied data')
                
                if score.overall_score >= 75:
                    recommendations.append('✓ This image is highly suitable for steganography')
                elif score.overall_score >= 50:
                    recommendations.append('~ This image is moderately suitable - consider optimization')
                else:
                    recommendations.append('✗ Consider using a different image for better security')
                
                logger.info(f'Optimization complete: {image_file.filename}, score={score.overall_score:.1f}')
                
                return jsonify({
                    'success': True,
                    'filename': image_file.filename,
                    'overall_score': round(score.overall_score, 1),
                    'score_breakdown': {
                        'capacity_score': round((score.entropy / 8.0) * 100, 1),
                        'quality_score': round(score.complexity, 1),
                        'suitability_score': round(score.overall_score, 1)
                    },
                    'metrics': {
                        'width': score.width,
                        'height': score.height,
                        'dimensions': score_dict['dimensions'],
                        'entropy': score_dict['entropy'],
                        'complexity': score_dict['complexity'],
                        'format': score.path.split('.')[-1].upper(),
                        'file_size': score.capacity_bytes,
                        'color_depth': '24-bit RGB',
                        'is_compressed': False
                    },
                    'capacity_analysis': {
                        'max_payload_bytes': score.capacity_bytes,
                        'max_payload_mb': round(score.capacity_bytes / (1024 * 1024), 3),
                        'optimal': int(score.overall_score > 70)
                    },
                    'recommendations': recommendations,
                    'suggestions': [
                        'Use this image for maximum security in LSB encoding',
                        'Combine with password encryption for additional protection',
                        'Consider using multi-image steganography for larger payloads'
                    ],
                    'risk_assessment': {
                        'compression_risk': compression_risk,
                        'entropy_risk': entropy_risk,
                        'visibility_risk': complexity_risk
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f'Optimization analysis error: {str(e)}', exc_info=True)
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Optimize endpoint error: {str(e)}')
        return jsonify({'error': 'Optimization failed'}), 500

# ===== VISUALIZATION & ANALYSIS ENDPOINTS =====

# Simple in-memory session storage
session_storage = {}
session_history = {}

@app.route('/api/v1/visualization/heatmap', methods=['POST'])
@rate_limit
def api_visualization_heatmap():
    """Generate heatmap data showing real LSB variance across image regions."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Image required'}), 400
        
        image_file = request.files['image']
        message = request.form.get('message', '')
        
        try:
            import numpy as np
            
            img = Image.open(image_file).convert('RGB')
            width, height = img.size
            pixels = np.array(img)
            
            grid_size = 10
            heatmap = []
            cell_h = height // grid_size
            cell_w = width // grid_size
            
            # Approximate overhead (version + length + salt + MAC + padding) = ~50 bytes
            overhead = 50
            message_bytes = len(message.encode('utf-8'))
            payload_size = message_bytes + overhead
            total_payload_bits = payload_size * 8
            pixels_needed = total_payload_bits / 3.0
            
            total_capacity = width * height * 3 // 8
            utilization_percent = min(100, (payload_size / total_capacity) * 100) if total_capacity > 0 else 0
            
            for row in range(grid_size):
                for col in range(grid_size):
                    y1, y2 = row * cell_h, min((row + 1) * cell_h, height)
                    x1, x2 = col * cell_w, min((col + 1) * cell_w, width)
                    
                    # Calculate real payload distribution: how many pixels in this cell will be modified
                    cell_embedded_pixels = 0
                    for y in range(y1, y2):
                        row_start_idx = y * width + x1
                        row_end_idx = y * width + x2
                        
                        if row_end_idx <= pixels_needed:
                            cell_embedded_pixels += (x2 - x1)
                        elif row_start_idx < pixels_needed:
                            cell_embedded_pixels += (pixels_needed - row_start_idx)
                            
                    cell_total_pixels = (y2 - y1) * (x2 - x1)
                    intensity = (cell_embedded_pixels / cell_total_pixels) * 100 if cell_total_pixels > 0 else 0
                    
                    heatmap.append({
                        'x': col,
                        'y': row,
                        'intensity': round(min(100, max(0, intensity)), 1)
                    })
            
            logger.info(f'Heatmap generated: {width}x{height}, utilization: {utilization_percent:.1f}%')
            
            return jsonify({
                'success': True,
                'image': {'width': width, 'height': height},
                'payload_bytes': payload_size,
                'capacity_bytes': total_capacity,
                'utilization_percent': round(utilization_percent, 1),
                'heatmap': heatmap,
                'grid_size': grid_size
            }), 200
            
        except Exception as e:
            logger.warning(f'Heatmap generation error: {str(e)}')
            return jsonify({'error': f'Invalid image: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Visualization error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/analysis/pixel-inspector', methods=['POST'])
@rate_limit
def api_pixel_inspector():
    """Analyze bit-level payload distribution across the entire carrier image."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Image required'}), 400
        
        image_file = request.files['image']
        
        try:
            import numpy as np
            
            img = Image.open(image_file).convert('RGB')
            width, height = img.size
            pixels = np.array(img)
            
            # Extract LSB planes for each channel
            lsb_r = pixels[:, :, 0] & 1
            lsb_g = pixels[:, :, 1] & 1
            lsb_b = pixels[:, :, 2] & 1
            
            def get_stats(lsb_plane):
                ones = np.sum(lsb_plane)
                total = lsb_plane.size
                zeros = total - ones
                one_pct = (ones / total * 100) if total > 0 else 0
                zero_pct = (zeros / total * 100) if total > 0 else 0
                
                # Entropy calculation
                p1 = ones / total if total > 0 else 0
                p0 = zeros / total if total > 0 else 0
                entropy = 0
                if p1 > 0 and p0 > 0:
                    entropy = -(p1 * np.log2(p1) + p0 * np.log2(p0))
                
                # Simple consecutive bit pattern check (sample first 10000 bits for performance)
                flat_bits = lsb_plane.flatten()[:10000]
                max_consecutive = 0
                current_run = 1
                for i in range(1, len(flat_bits)):
                    if flat_bits[i] == flat_bits[i-1]:
                        current_run += 1
                    else:
                        max_consecutive = max(max_consecutive, current_run)
                        current_run = 1
                max_consecutive = max(max_consecutive, current_run)

                return {
                    'ones': int(ones),
                    'zeros': int(zeros),
                    'one_pct': round(one_pct, 2),
                    'zero_pct': round(zero_pct, 2),
                    'entropy': round(float(entropy), 4),
                    'max_consecutive': max_consecutive
                }
            
            stats_r = get_stats(lsb_r)
            stats_g = get_stats(lsb_g)
            stats_b = get_stats(lsb_b)
            
            total_ones = stats_r['ones'] + stats_g['ones'] + stats_b['ones']
            total_zeros = stats_r['zeros'] + stats_g['zeros'] + stats_b['zeros']
            total_bits = pixels.size
            total_one_pct = (total_ones / total_bits * 100) if total_bits > 0 else 0
            total_zero_pct = 100 - total_one_pct
            avg_entropy = round((stats_r['entropy'] + stats_g['entropy'] + stats_b['entropy']) / 3, 4)
            
            capacity = calculate_max_payload(img)
            
            # Anomaly detection logic
            # Natural images usually have LSB bias. Stego (encrypted) is very close to 0.5.
            diff_from_50 = abs(total_one_pct - 50)
            if diff_from_50 < 0.1:
                distribution = "High Risk (Extreme Uniformity)"
            elif diff_from_50 < 1.0:
                distribution = "Suspicious (Possible Encrypted Data)"
            elif diff_from_50 < 5.0:
                distribution = "Balanced (Likely Natural)"
            else:
                distribution = "Natural (Biased)"

            logger.info(f'Full pixel inspection: {width}x{height}, total bits: {total_bits}')
            
            return jsonify({
                'success': True,
                'image': {'width': width, 'height': height, 'total_pixels': width * height},
                'lsb_analysis': {
                    'total_sampled': total_bits,
                    'one_bits': int(total_ones),
                    'zero_bits': int(total_zeros),
                    'one_percent': round(total_one_pct, 2),
                    'zero_percent': round(total_zero_pct, 2),
                    'max_consecutive_bits': max(stats_r['max_consecutive'], stats_g['max_consecutive'], stats_b['max_consecutive'])
                },
                'channels': {
                    'red': stats_r,
                    'green': stats_g,
                    'blue': stats_b
                },
                'entropy': avg_entropy,
                'capacity': capacity,
                'capacity_mb': round(capacity / (1024 * 1024), 3),
                'distribution': distribution
            }), 200
            
        except Exception as e:
            logger.warning(f'Pixel inspector error: {str(e)}')
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Inspector error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/session/history', methods=['GET', 'POST'])
@rate_limit
def api_session_history():
    """Manage session history for encoding/decoding operations."""
    try:
        client_id = request.headers.get('X-Client-ID') or str(uuid.uuid4())
        
        if request.method == 'GET':
            # Retrieve session history
            if client_id in session_history:
                history = session_history[client_id]
                return jsonify({
                    'success': True,
                    'client_id': client_id,
                    'history': history,
                    'total_operations': len(history)
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'client_id': client_id,
                    'history': [],
                    'total_operations': 0,
                    'message': 'No history yet'
                }), 200
        
        elif request.method == 'POST':
            # Record new operation
            operation = {
                'timestamp': datetime.now().isoformat(),
                'type': request.form.get('type', 'unknown'),  # 'encode', 'decode', 'analyze'
                'status': request.form.get('status', 'pending'),  # 'pending', 'success', 'failed'
                'details': {
                    'carrier_size': request.form.get('carrier_size', '0'),
                    'payload_size': request.form.get('payload_size', '0'),
                    'encryption': request.form.get('encryption', 'AES-256'),
                    'operation_id': str(uuid.uuid4())
                }
            }
            
            if client_id not in session_history:
                session_history[client_id] = []
            
            # Keep only last 100 operations
            session_history[client_id].append(operation)
            if len(session_history[client_id]) > 100:
                session_history[client_id] = session_history[client_id][-100:]
            
            logger.info(f'Session {client_id}: Recorded {operation["type"]} operation')
            
            return jsonify({
                'success': True,
                'client_id': client_id,
                'operation': operation,
                'total_operations': len(session_history[client_id])
            }), 200
    
    except Exception as e:
        logger.error(f'Session history error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/session/clear', methods=['POST'])
@rate_limit
def api_session_clear():
    """Clear session history."""
    try:
        client_id = request.headers.get('X-Client-ID')
        
        if client_id and client_id in session_history:
            del session_history[client_id]
            logger.info(f'Session {client_id}: Cleared')
            return jsonify({'success': True, 'message': 'History cleared'}), 200
        else:
            return jsonify({'success': False, 'message': 'No session to clear'}), 400
    
    except Exception as e:
        logger.error(f'Session clear error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== ERROR HANDLERS =====
# ===== AUDIO STEGANOGRAPHY ENDPOINTS (Feature #2) =====

@app.route('/api/v1/audio/analyze', methods=['POST'])
@rate_limit
def api_audio_analyze():
    """Analyze audio file for steganography suitability."""
    try:
        if 'audio' not in request.files:
            logger.warning('Audio analyze: missing audio file')
            return jsonify({'error': 'Audio file required'}), 400
        
        audio_file = request.files['audio']
        logger.info(f'Starting audio analysis: {audio_file.filename}')
        
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                audio_file.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                # Import audio steganographer
                from audio_steganographer import AudioSteganographer
                
                # Initialize and analyze
                steganographer = AudioSteganographer()
                audio_score = steganographer.analyze_audio(tmp_path)
                
                if not audio_score:
                    return jsonify({'error': 'Failed to analyze audio'}), 400
                
                logger.info(f'Audio analysis complete: {audio_file.filename}')
                
                return jsonify({
                    'success': True,
                    'filename': audio_file.filename,
                    'audio_info': {
                        'format': audio_score.format,
                        'duration_seconds': round(audio_score.duration_seconds, 2),
                        'sample_rate': audio_score.sample_rate,
                        'channels': audio_score.channels,
                        'file_size_kb': round(os.path.getsize(tmp_path) / 1024, 2)
                    },
                    'capacity': {
                        'max_payload_bytes': audio_score.capacity_bytes,
                        'max_payload_kb': round(audio_score.capacity_bytes / 1024, 2),
                        'max_payload_mb': round(audio_score.capacity_bytes / (1024 * 1024), 3),
                        'message_limit_chars': audio_score.capacity_bytes  # ASCII text
                    },
                    'quality_score': round(audio_score.quality_score, 1),
                    'suitability': 'Excellent' if audio_score.quality_score >= 75 else 'Good' if audio_score.quality_score >= 50 else 'Fair',
                    'recommendations': [
                        'Audio is suitable for steganography' if audio_score.quality_score >= 50 else 'Consider using higher quality audio',
                        f'Can hide up to {audio_score.capacity_bytes / 1024:.1f} KB of data',
                        'Use password protection for security'
                    ],
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f'Audio analysis error: {str(e)}', exc_info=True)
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Audio analyze endpoint error: {str(e)}')
        return jsonify({'error': 'Analysis failed'}), 500


@app.route('/api/v1/audio/embed', methods=['POST'])
@rate_limit
def api_audio_embed():
    """Embed message or file into audio using frequency domain LSB."""
    try:
        if 'audio' not in request.files:
            logger.warning('Audio embed: missing audio file')
            return jsonify({'error': 'Audio file required'}), 400
        
        if 'message' not in request.form:
            logger.warning('Audio embed: missing message')
            return jsonify({'error': 'Message required'}), 400
        
        audio_file = request.files['audio']
        message = request.form.get('message', '')
        quality = int(request.form.get('quality', '192'))  # MP3 bitrate
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if len(message) > 1000000:  # ~1MB text limit
            return jsonify({'error': 'Message too large (max 1MB)'}), 400
        
        if quality not in [128, 192, 256, 320]:
            quality = 192
        
        logger.info(f'Starting audio embedding: {audio_file.filename}, message size={len(message)}, quality={quality}')
        
        try:
            # Save uploaded audio to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_input:
                audio_file.save(tmp_input.name)
                tmp_input_path = tmp_input.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_output:
                tmp_output_path = tmp_output.name
            
            try:
                # Import audio steganographer
                from audio_steganographer import AudioSteganographer
                
                # Initialize and embed
                steganographer = AudioSteganographer()
                success = steganographer.embed(tmp_input_path, message, tmp_output_path, quality=quality)
                
                if not success:
                    return jsonify({'error': 'Embedding failed'}), 400
                
                # Read output file
                with open(tmp_output_path, 'rb') as f:
                    stego_audio = f.read()
                
                logger.info(f'Audio embedding successful: {len(stego_audio)} bytes output')
                
                return send_file(
                    io.BytesIO(stego_audio),
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name=f'stego_audio_{int(datetime.now().timestamp())}.mp3'
                )
                
            finally:
                # Clean up temporary files
                for path in [tmp_input_path, tmp_output_path]:
                    try:
                        os.unlink(path)
                    except:
                        pass
            
        except Exception as e:
            logger.error(f'Audio embedding error: {str(e)}', exc_info=True)
            return jsonify({'error': f'Embedding failed: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Audio embed endpoint error: {str(e)}')
        return jsonify({'error': 'Embedding failed'}), 500


@app.route('/api/v1/audio/extract', methods=['POST'])
@rate_limit
def api_audio_extract():
    """Extract hidden message from stego audio."""
    try:
        if 'audio' not in request.files:
            logger.warning('Audio extract: missing audio file')
            return jsonify({'error': 'Stego audio file required'}), 400
        
        audio_file = request.files['audio']
        logger.info(f'Starting audio extraction: {audio_file.filename}')
        
        try:
            # Save uploaded audio to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                audio_file.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                # Import audio steganographer
                from audio_steganographer import AudioSteganographer
                
                # Initialize and extract
                steganographer = AudioSteganographer()
                extracted_message = steganographer.extract(tmp_path)
                
                if not extracted_message:
                    logger.warning('No hidden message found in audio')
                    return jsonify({'error': 'No hidden message found in audio'}), 400
                
                # Try to decode as UTF-8
                try:
                    message_str = extracted_message.decode('utf-8')
                except:
                    # If it's not valid UTF-8, return as base64
                    import base64
                    message_str = f"[Binary data: {base64.b64encode(extracted_message).decode()}]"
                
                logger.info(f'Audio extraction successful: {len(extracted_message)} bytes extracted')
                
                return jsonify({
                    'success': True,
                    'message': message_str,
                    'message_size': len(extracted_message),
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f'Audio extraction error: {str(e)}', exc_info=True)
            return jsonify({'error': f'Extraction failed: {str(e)}'}), 400
    
    except Exception as e:
        logger.error(f'Audio extract endpoint error: {str(e)}')
        return jsonify({'error': 'Extraction failed'}), 500


# ===== FEATURE #3: ADVANCED ENCRYPTION =====

@app.route('/api/v1/encrypt/aes', methods=['POST'])
@rate_limit
def api_encrypt_aes():
    """
    AES-256-GCM encryption endpoint
    
    Request:
        - message: Message to encrypt (string or base64)
        - password: Encryption password
    
    Response:
        - ciphertext: Hex-encoded encrypted data
        - nonce: Hex-encoded nonce
        - salt: Hex-encoded salt
        - success: true
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').encode('utf-8') if isinstance(data.get('message'), str) else data.get('message', b'')
        password = data.get('password', '').encode('utf-8')
        
        if not message or not password:
            return jsonify({'error': 'Missing message or password'}), 400
        
        enc = AdvancedEncryption()
        result = enc.encrypt_aes_gcm(message, password)
        
        logger.info(f'AES-256-GCM encryption: {len(message)} bytes')
        return jsonify({
            'success': True,
            'ciphertext': result['ciphertext'],
            'nonce': result['nonce'],
            'salt': result['salt'],
            'method': 'AES-256-GCM',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'AES encryption error: {str(e)}', exc_info=True)
        return jsonify({'error': f'Encryption failed: {str(e)}'}), 400


@app.route('/api/v1/decrypt/aes', methods=['POST'])
@rate_limit
def api_decrypt_aes():
    """
    AES-256-GCM decryption endpoint
    
    Request:
        - ciphertext: Hex-encoded ciphertext
        - nonce: Hex-encoded nonce
        - salt: Hex-encoded salt
        - password: Decryption password
    
    Response:
        - message: Decrypted message (base64 or plaintext)
        - success: true/false
    """
    try:
        data = request.get_json() or {}
        ciphertext = data.get('ciphertext')
        nonce = data.get('nonce')
        salt = data.get('salt')
        password = data.get('password', '').encode('utf-8')
        
        if not all([ciphertext, nonce, salt, password]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        enc = AdvancedEncryption()
        plaintext = enc.decrypt_aes_gcm(ciphertext, nonce, password, salt)
        
        if plaintext is None:
            return jsonify({'error': 'Decryption failed', 'success': False}), 400
        
        logger.info(f'AES-256-GCM decryption: {len(plaintext)} bytes recovered')
        return jsonify({
            'success': True,
            'message': plaintext.decode('utf-8', errors='replace'),
            'method': 'AES-256-GCM'
        }), 200
        
    except Exception as e:
        logger.error(f'AES decryption error: {str(e)}')
        return jsonify({'error': 'Decryption failed'}), 400


@app.route('/api/v1/encrypt/double', methods=['POST'])
@rate_limit
def api_encrypt_double():
    """
    Double encryption endpoint (AES-256-GCM + ChaCha20-Poly1305)
    
    Request:
        - message: Message to encrypt
        - password1: First encryption password
        - password2: Second encryption password
        - cipher1: First cipher ("AES-GCM" or "ChaCha20")
        - cipher2: Second cipher ("AES-GCM" or "ChaCha20")
    
    Response:
        - layer1, layer2: Encrypted layers
        - cipher_suite: "AES-GCM+ChaCha20" etc
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').encode('utf-8') if isinstance(data.get('message'), str) else data.get('message', b'')
        password1 = data.get('password1', '').encode('utf-8')
        password2 = data.get('password2', '').encode('utf-8')
        cipher1 = data.get('cipher1', 'AES-GCM')
        cipher2 = data.get('cipher2', 'ChaCha20')
        
        if not message or not password1 or not password2:
            return jsonify({'error': 'Missing message or passwords'}), 400
        
        enc = AdvancedEncryption()
        result = enc.double_encrypt(message, password1, password2, cipher1, cipher2)
        
        logger.info(f'Double encryption: {len(message)} bytes ({cipher1}+{cipher2})')
        return jsonify({
            'success': True,
            'layer1': result['layer1'],
            'layer2': result['layer2'],
            'cipher_suite': f"{cipher1}+{cipher2}",
            'is_double_encrypted': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Double encryption error: {str(e)}')
        return jsonify({'error': 'Double encryption failed'}), 400


@app.route('/api/v1/decrypt/double', methods=['POST'])
@rate_limit
def api_decrypt_double():
    """Double decryption endpoint"""
    try:
        data = request.get_json() or {}
        encrypted_payload = data.get('encrypted_payload')
        password1 = data.get('password1', '').encode('utf-8')
        password2 = data.get('password2', '').encode('utf-8')
        
        if not encrypted_payload or not password1 or not password2:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        enc = AdvancedEncryption()
        plaintext = enc.double_decrypt(encrypted_payload, password1, password2)
        
        if plaintext is None:
            return jsonify({'error': 'Double decryption failed', 'success': False}), 400
        
        logger.info(f'Double decryption: {len(plaintext)} bytes recovered')
        return jsonify({
            'success': True,
            'message': plaintext.decode('utf-8', errors='replace')
        }), 200
        
    except Exception as e:
        logger.error(f'Double decryption error: {str(e)}')
        return jsonify({'error': 'Decryption failed'}), 400


@app.route('/api/v1/keys/rsa/generate', methods=['POST'])
@rate_limit
def api_generate_rsa_keys():
    """
    Generate RSA-4096 keypair
    
    Response:
        - private_key: PEM-encoded private key
        - public_key: PEM-encoded public key
        - fingerprint: SHA256 fingerprint for verification
    """
    try:
        enc = AdvancedEncryption()
        private_pem, public_pem = enc.generate_rsa_keypair()
        fingerprint = enc.get_rsa_fingerprint(public_pem)
        
        logger.info(f'RSA-4096 keypair generated (fingerprint: {fingerprint[:16]}...)')
        return jsonify({
            'success': True,
            'private_key': private_pem,
            'public_key': public_pem,
            'fingerprint': fingerprint,
            'key_size': 4096,
            'algorithm': 'RSA-OAEP-SHA256'
        }), 200
        
    except Exception as e:
        logger.error(f'RSA key generation error: {str(e)}')
        return jsonify({'error': 'Key generation failed'}), 500


# ===== FEATURE #4: POST-QUANTUM CRYPTOGRAPHY (NIST-STANDARDIZED) =====
# Quantum-safe algorithms: ML-KEM (Kyber), ML-DSA (Dilithium), Hybrid Mode

pqc = PostQuantumCrypto() if PQC_AVAILABLE else None

@app.route('/api/v1/pqc/algorithm-info/<algorithm>', methods=['GET'])
@rate_limit
def get_pqc_algorithm_info(algorithm):
    """Get information about post-quantum cryptography algorithm"""
    try:
        if not PQC_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Post-Quantum Crypto not available in this environment'}), 503
        info = pqc.get_algorithm_info(algorithm)
        return jsonify({
            'success': True,
            'algorithm': algorithm,
            'info': info
        }), 200
    except Exception as e:
        logger.error(f'PQC algorithm info error: {str(e)}')
        return jsonify({'error': str(e)}), 400


# ===== ML-KEM: QUANTUM-SAFE KEY ENCAPSULATION =====

@app.route('/api/v1/pqc/mlkem/generate-keys', methods=['POST'])
@rate_limit
def pqc_mlkem_generate():
    """Generate ML-KEM (Kyber) key pair for quantum-safe key exchange"""
    try:
        if not PQC_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Post-Quantum Crypto not available in this environment'}), 503
        result = pqc.generate_mlkem_keys()
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-KEM key generation error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/mlkem/encapsulate', methods=['POST'])
@rate_limit
def pqc_mlkem_encapsulate():
    """Perform ML-KEM encapsulation using public key"""
    try:
        if not PQC_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Post-Quantum Crypto not available in this environment'}), 503
        data = request.get_json()
        public_key = data.get('public_key')
        
        if not public_key:
            return jsonify({'error': 'Public key required'}), 400
        
        result = pqc.mlkem_encapsulate(public_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-KEM encapsulation error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/mlkem/decapsulate', methods=['POST'])
@rate_limit
def pqc_mlkem_decapsulate():
    """Perform ML-KEM decapsulation using private key"""
    try:
        if not PQC_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Post-Quantum Crypto not available in this environment'}), 503
        data = request.get_json()
        ciphertext = data.get('ciphertext')
        private_key = data.get('private_key')
        
        if not ciphertext or not private_key:
            return jsonify({'error': 'Ciphertext and private key required'}), 400
        
        result = pqc.mlkem_decapsulate(ciphertext, private_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-KEM decapsulation error: {str(e)}')
        return jsonify({'error': str(e)}), 400


# ===== ML-DSA: QUANTUM-SAFE DIGITAL SIGNATURES =====

@app.route('/api/v1/pqc/mldsa/generate-keys', methods=['POST'])
@rate_limit
def pqc_mldsa_generate():
    """Generate ML-DSA (Dilithium) key pair for quantum-safe signatures"""
    try:
        result = pqc.generate_mldsa_keys()
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-DSA key generation error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/mldsa/sign', methods=['POST'])
@rate_limit
def pqc_mldsa_sign():
    """Sign data using ML-DSA private key"""
    try:
        if 'file' not in request.files and 'data' not in request.form:
            return jsonify({'error': 'File or data required'}), 400
        
        private_key = request.form.get('private_key')
        if not private_key:
            return jsonify({'error': 'Private key required'}), 400
        
        # Get data from file or text
        if 'file' in request.files:
            data = request.files['file'].read()
        else:
            data = request.form.get('data', '').encode('utf-8')
        
        result = pqc.mldsa_sign(data, private_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-DSA signing error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/mldsa/verify', methods=['POST'])
@rate_limit
def pqc_mldsa_verify():
    """Verify ML-DSA signature"""
    try:
        if 'file' not in request.files and 'data' not in request.form:
            return jsonify({'error': 'File or data required'}), 400
        
        signature = request.form.get('signature')
        public_key = request.form.get('public_key')
        
        if not signature or not public_key:
            return jsonify({'error': 'Signature and public key required'}), 400
        
        # Get data from file or text
        if 'file' in request.files:
            data = request.files['file'].read()
        else:
            data = request.form.get('data', '').encode('utf-8')
        
        result = pqc.mldsa_verify(data, signature, public_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'ML-DSA verification error: {str(e)}')
        return jsonify({'error': str(e)}), 400


# ===== HYBRID MODE: RSA-4096 + ML-KEM =====

@app.route('/api/v1/pqc/hybrid/generate-keys', methods=['POST'])
@rate_limit
def pqc_hybrid_generate():
    """Generate hybrid key pair (RSA-4096 + ML-KEM-768)"""
    try:
        result = pqc.generate_hybrid_keys()
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'Hybrid key generation error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/hybrid/encrypt', methods=['POST'])
@rate_limit
def pqc_hybrid_encrypt():
    """Hybrid encryption using RSA-4096 + ML-KEM-768"""
    try:
        if 'file' not in request.files and 'data' not in request.form:
            return jsonify({'error': 'File or data required'}), 400
        
        rsa_public_key = request.form.get('rsa_public_key')
        mlkem_public_key = request.form.get('mlkem_public_key')
        
        if not rsa_public_key or not mlkem_public_key:
            return jsonify({'error': 'Both RSA and ML-KEM public keys required'}), 400
        
        # Get data from file or text
        if 'file' in request.files:
            data = request.files['file'].read()
        else:
            data = request.form.get('data', '').encode('utf-8')
        
        result = pqc.hybrid_encrypt(data, rsa_public_key, mlkem_public_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'Hybrid encryption error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/pqc/hybrid/decrypt', methods=['POST'])
@rate_limit
def pqc_hybrid_decrypt():
    """Hybrid decryption using RSA-4096 + ML-KEM-768"""
    try:
        data = request.get_json()
        rsa_ciphertext = data.get('rsa_ciphertext')
        mlkem_ciphertext = data.get('mlkem_ciphertext')
        data_ciphertext = data.get('data_ciphertext')
        rsa_private_key = data.get('rsa_private_key')
        mlkem_private_key = data.get('mlkem_private_key')
        
        required = [rsa_ciphertext, mlkem_ciphertext, data_ciphertext, rsa_private_key, mlkem_private_key]
        if not all(required):
            return jsonify({'error': 'All keys and ciphertexts required'}), 400
        
        result = pqc.hybrid_decrypt(rsa_ciphertext, mlkem_ciphertext, data_ciphertext, 
                                   rsa_private_key, mlkem_private_key)
        return jsonify(result), 200 if result['status'] == 'success' else 400
    except Exception as e:
        logger.error(f'Hybrid decryption error: {str(e)}')
        return jsonify({'error': str(e)}), 400


# ===== FEATURE #3 OPTION C: ADVANCED BATCH PROCESSING =====

# Initialize global batch processor
from batch_processor import BatchProcessor, FileStatus

batch_processor = BatchProcessor(max_workers=4)

@app.route('/api/v1/batch/encrypt', methods=['POST'])
@rate_limit
def api_batch_encrypt():
    """
    Advanced batch processing for multi-file encryption.
    Processes multiple files with progress tracking.
    
    Request:
        - files: Multiple files to encrypt
        - password: Encryption password
        - cipher: Encryption cipher (AES-GCM, ChaCha20, etc)
        - options: Additional options (JSON)
    
    Response:
        - batch_id: Unique batch identifier
        - total_files: Number of files to process
        - status: Initial status (queued)
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Files required'}), 400
        
        password = request.form.get('password', '')
        cipher = request.form.get('cipher', 'AES-GCM')
        
        # Validate password
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        files_list = request.files.getlist('files')
        if not files_list or len(files_list) == 0:
            return jsonify({'error': 'No files provided'}), 400
        
        # Save files temporarily
        temp_files = []
        temp_dir = tempfile.mkdtemp(prefix='batch_encrypt_')
        
        try:
            for f in files_list:
                if f.filename:
                    filepath = os.path.join(temp_dir, f.filename)
                    f.save(filepath)
                    temp_files.append(filepath)
            
            # Create batch job
            batch = batch_processor.create_batch(
                job_type='encrypt',
                files=temp_files,
                options={
                    'password': password,
                    'cipher': cipher,
                    'temp_dir': temp_dir
                }
            )
            
            # Handler function for encryption
            def encrypt_handler(file_job, options):
                try:
                    with open(file_job.filepath, 'rb') as f:
                        file_data = f.read()
                    
                    # Encrypt file
                    enc = AdvancedEncryption()
                    if options.get('cipher') == 'AES-GCM':
                        result = enc.encrypt_aes_gcm(file_data, options['password'].encode())
                        return {
                            'encrypted': True,
                            'cipher': 'AES-256-GCM',
                            'output_size': len(file_data),
                            'ciphertext_size': len(result['ciphertext'])
                        }
                    else:
                        raise ValueError(f"Unsupported cipher: {options.get('cipher')}")
                    
                except Exception as e:
                    return {'encrypted': False, 'error': str(e)}
            
            # Progress callback
            def on_progress(batch_id, progress):
                logger.info(f'Batch {batch_id}: {progress}% complete')
            
            # Submit batch for processing
            batch_processor.submit_batch(batch, encrypt_handler, on_progress)
            
            logger.info(f'Batch encryption started: batch_id={batch.batch_id}, files={len(temp_files)}')
            
            return jsonify({
                'success': True,
                'batch_id': batch.batch_id,
                'total_files': len(temp_files),
                'status': batch.status.value,
                'progress': 0,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        except Exception as e:
            # Clean up temp directory on error
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise
    
    except Exception as e:
        logger.error(f'Batch encrypt error: {str(e)}')
        return jsonify({'error': f'Batch encryption failed: {str(e)}'}), 400


@app.route('/api/v1/batch/status/<batch_id>', methods=['GET'])
@rate_limit
def api_batch_status(batch_id):
    """
    Get status of a batch job.
    
    Response:
        - batch_id: Batch identifier
        - status: Current status (queued, in_progress, completed, failed)
        - progress: 0-100 progress percentage
        - files: Per-file status details (optional)
    """
    try:
        include_files = request.args.get('include_files', 'false').lower() == 'true'
        status = batch_processor.get_batch_status(batch_id, include_files=include_files)
        
        if not status:
            return jsonify({'error': 'Batch not found'}), 404
        
        return jsonify({
            'success': True,
            'batch': status
        }), 200
    
    except Exception as e:
        logger.error(f'Batch status error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/batch/list', methods=['GET'])
@rate_limit
def api_batch_list():
    """
    List all batches with optional filtering.
    
    Query params:
        - status: Filter by status (queued, in_progress, completed, failed)
        - job_type: Filter by job type (encrypt, decrypt, embed, extract)
    
    Response:
        - batches: List of batch summaries
        - total: Total number of batches
    """
    try:
        status_filter = request.args.get('status')
        job_type_filter = request.args.get('job_type')
        
        batches = batch_processor.list_batches(
            status=status_filter,
            job_type=job_type_filter
        )
        
        return jsonify({
            'success': True,
            'batches': batches,
            'total': len(batches),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'Batch list error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/batch/cancel/<batch_id>', methods=['POST'])
@rate_limit
def api_batch_cancel(batch_id):
    """
    Cancel a pending batch job.
    
    Response:
        - success: true/false
        - message: Cancellation status
    """
    try:
        success = batch_processor.cancel_batch(batch_id)
        
        if success:
            logger.info(f'Batch {batch_id} cancelled')
            return jsonify({
                'success': True,
                'message': f'Batch {batch_id} cancelled'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Batch not found or cannot be cancelled'
            }), 400
    
    except Exception as e:
        logger.error(f'Batch cancel error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/batch/clear/<batch_id>', methods=['POST'])
@rate_limit
def api_batch_clear(batch_id):
    """
    Clear completed batch from memory.
    
    Response:
        - success: true/false
    """
    try:
        success = batch_processor.clear_batch(batch_id)
        
        if success:
            logger.info(f'Batch {batch_id} cleared from memory')
            return jsonify({
                'success': True,
                'message': f'Batch {batch_id} cleared'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Batch not found'
            }), 400
    
    except Exception as e:
        logger.error(f'Batch clear error: {str(e)}')
        return jsonify({'error': str(e)}), 400


@app.route('/api/v1/batch/capabilities', methods=['GET'])
@rate_limit
def api_batch_capabilities():
    """
    Get batch processing capabilities and limits.
    
    Response:
        - max_workers: Maximum concurrent workers
        - max_files: Maximum files per batch
        - supported_operations: List of batch operations
        - features: Advanced features available
    """
    return jsonify({
        'success': True,
        'capabilities': {
            'max_workers': batch_processor.max_workers,
            'max_files': 1000,
            'max_file_size': '100MB',
            'supported_operations': [
                'encrypt',
                'decrypt',
                'embed',
                'extract',
                'analyze',
                'compress'
            ],
            'features': [
                'progress_tracking',
                'error_recovery',
                'cancellation',
                'parallel_processing',
                'result_aggregation'
            ]
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/v1/encrypt/hybrid', methods=['POST'])
@rate_limit
def api_encrypt_hybrid():
    """
    Hybrid encryption endpoint (RSA-4096 + AES-256-GCM)
    
    Request:
        - message: Message to encrypt
        - public_key: RSA public key (PEM format)
    
    Response:
        - encrypted_session_key: RSA-encrypted session key
        - ciphertext: AES-encrypted message
        - method: "RSA-4096 + AES-256-GCM"
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').encode('utf-8') if isinstance(data.get('message'), str) else data.get('message', b'')
        public_key_pem = data.get('public_key')
        
        if not message or not public_key_pem:
            return jsonify({'error': 'Missing message or public key'}), 400
        
        enc = AdvancedEncryption()
        result = enc.hybrid_encrypt(message, public_key_pem)
        
        logger.info(f'Hybrid encryption: {len(message)} bytes (RSA-4096 + AES-256-GCM)')
        return jsonify({
            'success': True,
            'encrypted_session_key': result['encrypted_session_key'],
            'ciphertext': result['ciphertext'],
            'nonce': result['nonce'],
            'method': result['method'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Hybrid encryption error: {str(e)}')
        return jsonify({'error': 'Hybrid encryption failed'}), 400


@app.route('/api/v1/decrypt/hybrid', methods=['POST'])
@rate_limit
def api_decrypt_hybrid():
    """Hybrid decryption endpoint (RSA-4096 + AES-256-GCM)"""
    try:
        data = request.get_json() or {}
        private_key_pem = data.get('private_key')
        encrypted_payload = data.get('encrypted_payload')
        
        if not private_key_pem or not encrypted_payload:
            return jsonify({'error': 'Missing private key or encrypted payload'}), 400
        
        enc = AdvancedEncryption()
        enc.load_rsa_private_key(private_key_pem)
        plaintext = enc.hybrid_decrypt(encrypted_payload)
        
        if plaintext is None:
            return jsonify({'error': 'Hybrid decryption failed', 'success': False}), 400
        
        logger.info(f'Hybrid decryption: {len(plaintext)} bytes recovered')
        return jsonify({
            'success': True,
            'message': plaintext.decode('utf-8', errors='replace')
        }), 200
        
    except Exception as e:
        logger.error(f'Hybrid decryption error: {str(e)}')
        return jsonify({'error': 'Decryption failed'}), 400


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(e):
    logger.warning(f'404 error: {request.path}')
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(413)
def payload_too_large(e):
    logger.warning('Payload too large')
    return jsonify({'error': 'File too large (max 50MB)'}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f'Internal server error: {str(e)}')
    return jsonify({'error': 'Internal server error'}), 500

# ===== APPLICATION ENTRY POINT =====
if __name__ == '__main__':
    logger.info(f'StegoForge v{Config.VERSION} Enterprise Edition')
    logger.info(f'Environment: {"development" if Config.DEBUG else "production"}')
    logger.info('Starting Flask application...')
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG, use_reloader=False)
