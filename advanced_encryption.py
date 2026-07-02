"""
StegoForge v4 - Advanced Encryption Module
==========================================

Implements multi-layer encryption with support for:
- AES-256-GCM (authenticated encryption)
- ChaCha20-Poly1305 (alternative AEAD cipher)
- RSA-4096 (public key encryption)
- Hybrid encryption (RSA + AES key exchange)
- Perfect Forward Secrecy (session keys)

Author: StegoForge Development Team
Version: 4.0.0
Status: Production Ready
"""

import os
import json
import hashlib
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import numpy as np
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EncryptionMetadata:
    """Metadata for encrypted payloads"""
    version: str = "4.0.0"
    cipher_suite: str = "AES-256-GCM"  # or "ChaCha20-Poly1305"
    key_derivation: str = "HKDF-SHA256"
    timestamp: str = ""
    expiry_hours: int = 24
    is_double_encrypted: bool = False
    public_key_fingerprint: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class AdvancedEncryption:
    """
    Multi-layer encryption engine for StegoForge.
    
    Supports:
    - Single encryption (AES-256-GCM or ChaCha20-Poly1305)
    - Double encryption (AES + ChaCha20 with different keys)
    - RSA-4096 public key encryption
    - Hybrid encryption (RSA for key exchange, AES for bulk data)
    - Session key rotation (Perfect Forward Secrecy)
    """
    
    # Encryption constants
    AES_KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12    # 96 bits for GCM
    CHACHA_NONCE_SIZE = 12  # 96 bits for ChaCha20-Poly1305
    RSA_KEY_SIZE = 4096
    TAG_SIZE = 16      # 128 bits for GCM/ChaCha20
    
    def __init__(self):
        """Initialize encryption engine"""
        self.rsa_private_key = None
        self.rsa_public_key = None
        self.master_key = None
        logger.info("AdvancedEncryption engine initialized")
    
    # ========== RSA Key Management ==========
    
    def generate_rsa_keypair(self) -> Tuple[str, str]:
        """
        Generate RSA-4096 keypair for public key encryption.
        
        Returns:
            Tuple[private_pem, public_pem]: PEM-encoded keys
        """
        logger.info("Generating RSA-4096 keypair...")
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.RSA_KEY_SIZE,
            backend=default_backend()
        )
        
        # Encode to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        self.rsa_private_key = private_key
        self.rsa_public_key = private_key.public_key()
        
        logger.info("RSA-4096 keypair generated successfully")
        return private_pem, public_pem
    
    def load_rsa_private_key(self, pem_data: str):
        """Load RSA private key from PEM string"""
        try:
            self.rsa_private_key = serialization.load_pem_private_key(
                pem_data.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            self.rsa_public_key = self.rsa_private_key.public_key()
            logger.info("RSA private key loaded")
        except Exception as e:
            logger.error(f"Failed to load RSA private key: {e}")
            raise
    
    def load_rsa_public_key(self, pem_data: str):
        """Load RSA public key from PEM string"""
        try:
            self.rsa_public_key = serialization.load_pem_public_key(
                pem_data.encode('utf-8'),
                backend=default_backend()
            )
            logger.info("RSA public key loaded")
        except Exception as e:
            logger.error(f"Failed to load RSA public key: {e}")
            raise
    
    def get_rsa_fingerprint(self, public_key_pem: str = None) -> str:
        """
        Get SHA256 fingerprint of RSA public key.
        
        Useful for key verification and identification.
        """
        if public_key_pem is None and self.rsa_public_key is None:
            return ""
        
        if public_key_pem:
            self.load_rsa_public_key(public_key_pem)
        
        public_pem = self.rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        fingerprint = hashlib.sha256(public_pem).hexdigest()
        logger.info(f"RSA key fingerprint: {fingerprint[:16]}...")
        return fingerprint
    
    # ========== Key Derivation ==========
    
    def derive_key(self, password: bytes, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using HKDF-SHA256.
        
        Args:
            password: User password
            salt: Optional salt (generated if not provided)
        
        Returns:
            Tuple[key, salt]: Derived key and salt used
        """
        if salt is None:
            salt = os.urandom(16)  # 128-bit salt
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=self.AES_KEY_SIZE,
            salt=salt,
            info=b'stegoforge-v4-encryption',
            backend=default_backend()
        )
        
        key = hkdf.derive(password)
        return key, salt
    
    # ========== AES-256-GCM Encryption ==========
    
    def encrypt_aes_gcm(
        self,
        plaintext: bytes,
        password: bytes,
        associated_data: bytes = None
    ) -> Dict[str, str]:
        """
        Encrypt data using AES-256-GCM.
        
        AES-GCM provides authenticated encryption (AEAD):
        - Confidentiality via AES-256
        - Authenticity via Galois/Counter Mode authentication
        - Detects tampering with ciphertext
        
        Args:
            plaintext: Data to encrypt
            password: Encryption password
            associated_data: Additional authenticated data (not encrypted)
        
        Returns:
            Dict with: ciphertext, nonce, salt, tag, aad
        """
        salt = os.urandom(16)
        nonce = os.urandom(self.NONCE_SIZE)
        
        # Derive key from password
        key, _ = self.derive_key(password, salt)
        
        # Encrypt with AES-256-GCM
        cipher = AESGCM(key)
        
        try:
            ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
            
            logger.info(f"AES-256-GCM encryption: {len(plaintext)} bytes → {len(ciphertext)} bytes")
            
            return {
                'ciphertext': ciphertext.hex(),
                'nonce': nonce.hex(),
                'salt': salt.hex(),
                'tag': ciphertext[-16:].hex(),  # Last 16 bytes are auth tag
                'aad': associated_data.hex() if associated_data else ""
            }
        except Exception as e:
            logger.error(f"AES-256-GCM encryption failed: {e}")
            raise
    
    def decrypt_aes_gcm(
        self,
        ciphertext_hex: str,
        nonce_hex: str,
        password: bytes,
        salt_hex: str = None,
        associated_data: bytes = None
    ) -> Optional[bytes]:
        """
        Decrypt AES-256-GCM ciphertext.
        
        Args:
            ciphertext_hex: Hex-encoded ciphertext (includes tag)
            nonce_hex: Hex-encoded nonce
            password: Decryption password
            salt_hex: Hex-encoded salt
            associated_data: Associated authenticated data
        
        Returns:
            Decrypted plaintext or None if authentication fails
        """
        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
            nonce = bytes.fromhex(nonce_hex)
            salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
            
            # Derive key
            key, _ = self.derive_key(password, salt)
            
            # Decrypt
            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            
            logger.info(f"AES-256-GCM decryption: {len(ciphertext)} bytes → {len(plaintext)} bytes")
            return plaintext
            
        except Exception as e:
            logger.error(f"AES-256-GCM decryption failed: {e}")
            return None
    
    # ========== ChaCha20-Poly1305 Encryption ==========
    
    def encrypt_chacha20(
        self,
        plaintext: bytes,
        password: bytes,
        associated_data: bytes = None
    ) -> Dict[str, str]:
        """
        Encrypt data using ChaCha20-Poly1305.
        
        ChaCha20-Poly1305 is an alternative AEAD cipher:
        - Faster on systems without AES-NI
        - Still provides authenticated encryption
        - Suitable for double encryption
        
        Args:
            plaintext: Data to encrypt
            password: Encryption password
            associated_data: Additional authenticated data
        
        Returns:
            Dict with: ciphertext, nonce, salt, tag, aad
        """
        salt = os.urandom(16)
        nonce = os.urandom(self.CHACHA_NONCE_SIZE)
        
        key, _ = self.derive_key(password, salt)
        
        cipher = ChaCha20Poly1305(key)
        
        try:
            ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
            
            logger.info(f"ChaCha20-Poly1305 encryption: {len(plaintext)} bytes → {len(ciphertext)} bytes")
            
            return {
                'ciphertext': ciphertext.hex(),
                'nonce': nonce.hex(),
                'salt': salt.hex(),
                'tag': ciphertext[-16:].hex(),
                'aad': associated_data.hex() if associated_data else ""
            }
        except Exception as e:
            logger.error(f"ChaCha20-Poly1305 encryption failed: {e}")
            raise
    
    def decrypt_chacha20(
        self,
        ciphertext_hex: str,
        nonce_hex: str,
        password: bytes,
        salt_hex: str = None,
        associated_data: bytes = None
    ) -> Optional[bytes]:
        """Decrypt ChaCha20-Poly1305 ciphertext"""
        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
            nonce = bytes.fromhex(nonce_hex)
            salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
            
            key, _ = self.derive_key(password, salt)
            cipher = ChaCha20Poly1305(key)
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            
            logger.info(f"ChaCha20-Poly1305 decryption successful")
            return plaintext
            
        except Exception as e:
            logger.error(f"ChaCha20-Poly1305 decryption failed: {e}")
            return None
    
    # ========== Double Encryption ==========
    
    def double_encrypt(
        self,
        plaintext: bytes,
        password1: bytes,
        password2: bytes,
        cipher1: str = "AES-GCM",
        cipher2: str = "ChaCha20"
    ) -> Dict[str, Any]:
        """
        Apply double encryption (encrypt with two different ciphers and keys).
        
        Process:
        1. Encrypt with first cipher (AES-256-GCM)
        2. Encrypt result with second cipher (ChaCha20-Poly1305)
        
        Benefits:
        - Protection against single cipher weakness
        - Different key derivation for each layer
        - More resistant to brute force attacks
        
        Args:
            plaintext: Data to encrypt
            password1: First encryption password
            password2: Second encryption password
            cipher1: First cipher ("AES-GCM" or "ChaCha20")
            cipher2: Second cipher ("AES-GCM" or "ChaCha20")
        
        Returns:
            Dict with encrypted payload and metadata
        """
        logger.info(f"Starting double encryption: {cipher1} → {cipher2}")
        
        # First encryption layer
        if cipher1 == "AES-GCM":
            layer1 = self.encrypt_aes_gcm(plaintext, password1)
            ciphertext1 = bytes.fromhex(layer1['ciphertext'])
        else:
            layer1 = self.encrypt_chacha20(plaintext, password1)
            ciphertext1 = bytes.fromhex(layer1['ciphertext'])
        
        # Second encryption layer (encrypt the already-encrypted data)
        if cipher2 == "AES-GCM":
            layer2 = self.encrypt_aes_gcm(ciphertext1, password2)
        else:
            layer2 = self.encrypt_chacha20(ciphertext1, password2)
        
        logger.info(f"Double encryption complete: {len(plaintext)} → {len(ciphertext1)} → {len(bytes.fromhex(layer2['ciphertext']))} bytes")
        
        return {
            'is_double_encrypted': True,
            'cipher1': cipher1,
            'cipher2': cipher2,
            'layer1': layer1,
            'layer2': layer2,
            'metadata': asdict(EncryptionMetadata(
                cipher_suite=f"{cipher1}+{cipher2}",
                is_double_encrypted=True
            ))
        }
    
    def double_decrypt(
        self,
        encrypted_payload: Dict[str, Any],
        password1: bytes,
        password2: bytes
    ) -> Optional[bytes]:
        """
        Decrypt double-encrypted payload.
        
        Process:
        1. Decrypt outer layer with password2
        2. Decrypt inner layer with password1
        
        Args:
            encrypted_payload: Output from double_encrypt()
            password1: First encryption password
            password2: Second encryption password
        
        Returns:
            Original plaintext or None if decryption fails
        """
        try:
            logger.info("Starting double decryption")
            
            layer2_data = encrypted_payload['layer2']
            layer1_data = encrypted_payload['layer1']
            cipher1 = encrypted_payload.get('cipher1', 'AES-GCM')
            cipher2 = encrypted_payload.get('cipher2', 'ChaCha20')
            
            # Decrypt outer layer
            if cipher2 == "AES-GCM":
                ciphertext1 = self.decrypt_aes_gcm(
                    layer2_data['ciphertext'],
                    layer2_data['nonce'],
                    password2,
                    layer2_data['salt']
                )
            else:
                ciphertext1 = self.decrypt_chacha20(
                    layer2_data['ciphertext'],
                    layer2_data['nonce'],
                    password2,
                    layer2_data['salt']
                )
            
            if ciphertext1 is None:
                logger.error("Outer layer decryption failed")
                return None
            
            # Decrypt inner layer
            if cipher1 == "AES-GCM":
                plaintext = self.decrypt_aes_gcm(
                    ciphertext1.hex(),
                    layer1_data['nonce'],
                    password1,
                    layer1_data['salt']
                )
            else:
                plaintext = self.decrypt_chacha20(
                    ciphertext1.hex(),
                    layer1_data['nonce'],
                    password1,
                    layer1_data['salt']
                )
            
            if plaintext:
                logger.info(f"Double decryption successful: {len(plaintext)} bytes recovered")
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Double decryption failed: {e}")
            return None
    
    # ========== RSA-4096 Encryption ==========
    
    def encrypt_rsa(self, plaintext: bytes, public_key_pem: str = None) -> str:
        """
        Encrypt data using RSA-4096 public key.
        
        Warning: RSA has size limitations (4096-bit RSA can encrypt ~470 bytes).
        For larger data, use hybrid encryption (see hybrid_encrypt).
        
        Args:
            plaintext: Data to encrypt (max ~470 bytes)
            public_key_pem: RSA public key in PEM format
        
        Returns:
            Hex-encoded ciphertext
        """
        if public_key_pem:
            self.load_rsa_public_key(public_key_pem)
        
        if self.rsa_public_key is None:
            logger.error("No RSA public key available")
            raise ValueError("RSA public key not loaded")
        
        if len(plaintext) > 470:
            logger.warning(f"Plaintext too large ({len(plaintext)} bytes). Use hybrid_encrypt instead.")
            raise ValueError("Plaintext too large for RSA encryption")
        
        try:
            ciphertext = self.rsa_public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.info(f"RSA-4096 encryption: {len(plaintext)} bytes")
            return ciphertext.hex()
            
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
            raise
    
    def decrypt_rsa(self, ciphertext_hex: str) -> Optional[bytes]:
        """
        Decrypt RSA-4096 ciphertext.
        
        Args:
            ciphertext_hex: Hex-encoded ciphertext
        
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        if self.rsa_private_key is None:
            logger.error("No RSA private key available")
            return None
        
        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
            plaintext = self.rsa_private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.info(f"RSA-4096 decryption: {len(plaintext)} bytes recovered")
            return plaintext
            
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")
            return None
    
    # ========== Hybrid Encryption (RSA + AES) ==========
    
    def hybrid_encrypt(
        self,
        plaintext: bytes,
        public_key_pem: str = None
    ) -> Dict[str, str]:
        """
        Encrypt using hybrid approach: RSA for key exchange, AES-256-GCM for bulk data.
        
        Process:
        1. Generate random 256-bit session key
        2. Encrypt plaintext with AES-256-GCM using session key
        3. Encrypt session key with RSA-4096
        
        Benefits:
        - Can encrypt arbitrary-size data (not limited by RSA)
        - Session key can be discarded after use (Perfect Forward Secrecy)
        - Only receiver with private key can decrypt
        
        Args:
            plaintext: Data to encrypt
            public_key_pem: RSA public key in PEM format
        
        Returns:
            Dict with: encrypted_session_key, ciphertext, nonce, salt
        """
        if public_key_pem:
            self.load_rsa_public_key(public_key_pem)
        
        logger.info(f"Starting hybrid encryption (RSA-4096 + AES-256-GCM): {len(plaintext)} bytes")
        
        # Generate session key (256-bit random)
        session_key = os.urandom(self.AES_KEY_SIZE)
        
        # Encrypt plaintext with session key (AES-256-GCM, no password)
        nonce = os.urandom(self.NONCE_SIZE)
        cipher = AESGCM(session_key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        # Encrypt session key with RSA public key
        encrypted_session_key = self.rsa_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        logger.info(f"Hybrid encryption complete: {len(plaintext)} bytes (session key encrypted with RSA-4096)")
        
        return {
            'encrypted_session_key': encrypted_session_key.hex(),
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex(),
            'method': 'RSA-4096 + AES-256-GCM'
        }
    
    def hybrid_decrypt(
        self,
        encrypted_payload: Dict[str, str]
    ) -> Optional[bytes]:
        """
        Decrypt hybrid-encrypted payload.
        
        Args:
            encrypted_payload: Output from hybrid_encrypt()
        
        Returns:
            Original plaintext or None if decryption fails
        """
        if self.rsa_private_key is None:
            logger.error("No RSA private key available for hybrid decryption")
            return None
        
        try:
            logger.info("Starting hybrid decryption")
            
            # Decrypt session key with RSA private key
            encrypted_session_key = bytes.fromhex(encrypted_payload['encrypted_session_key'])
            session_key = self.rsa_private_key.decrypt(
                encrypted_session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt ciphertext with session key
            ciphertext = bytes.fromhex(encrypted_payload['ciphertext'])
            nonce = bytes.fromhex(encrypted_payload['nonce'])
            
            cipher = AESGCM(session_key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            
            logger.info(f"Hybrid decryption complete: {len(plaintext)} bytes recovered")
            return plaintext
            
        except Exception as e:
            logger.error(f"Hybrid decryption failed: {e}")
            return None
    
    # ========== Key Rotation (Perfect Forward Secrecy) ==========
    
    def rotate_session_key(self, old_key: bytes) -> bytes:
        """
        Generate new session key derived from old key using HKDF.
        
        Supports Perfect Forward Secrecy:
        - Old messages remain secure even if current key is compromised
        - Each session has its own derived key
        - Keys cannot be reversed to find previous keys
        
        Args:
            old_key: Current session key
        
        Returns:
            New session key
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=self.AES_KEY_SIZE,
            salt=os.urandom(16),
            info=b'stegoforge-key-rotation',
            backend=default_backend()
        )
        
        new_key = hkdf.derive(old_key)
        logger.info("Session key rotated (Perfect Forward Secrecy)")
        return new_key


# ========== Utility Functions ==========

def test_encryption_suite():
    """Test all encryption functions"""
    print("\n" + "="*70)
    print("ADVANCED ENCRYPTION TEST SUITE")
    print("="*70)
    
    enc = AdvancedEncryption()
    
    # Test message
    message = b"This is a secret message for testing advanced encryption!"
    password1 = b"secure_password_1"
    password2 = b"secure_password_2"
    
    # ===== AES-256-GCM =====
    print("\n[TEST 1] AES-256-GCM Encryption")
    result = enc.encrypt_aes_gcm(message, password1)
    print(f"  Encrypted: {len(bytes.fromhex(result['ciphertext']))} bytes")
    recovered = enc.decrypt_aes_gcm(result['ciphertext'], result['nonce'], password1, result['salt'])
    assert recovered == message, "AES-GCM decryption failed"
    print(f"  ✓ Decrypted: {recovered}")
    
    # ===== ChaCha20-Poly1305 =====
    print("\n[TEST 2] ChaCha20-Poly1305 Encryption")
    result = enc.encrypt_chacha20(message, password1)
    print(f"  Encrypted: {len(bytes.fromhex(result['ciphertext']))} bytes")
    recovered = enc.decrypt_chacha20(result['ciphertext'], result['nonce'], password1, result['salt'])
    assert recovered == message, "ChaCha20 decryption failed"
    print(f"  ✓ Decrypted: {recovered}")
    
    # ===== Double Encryption =====
    print("\n[TEST 3] Double Encryption (AES-256-GCM + ChaCha20)")
    result = enc.double_encrypt(message, password1, password2)
    print(f"  Layer 1 encrypted: {len(bytes.fromhex(result['layer1']['ciphertext']))} bytes")
    print(f"  Layer 2 encrypted: {len(bytes.fromhex(result['layer2']['ciphertext']))} bytes")
    recovered = enc.double_decrypt(result, password1, password2)
    assert recovered == message, "Double decryption failed"
    print(f"  ✓ Recovered: {recovered}")
    
    # ===== RSA-4096 =====
    print("\n[TEST 4] RSA-4096 Key Generation & Encryption")
    private_pem, public_pem = enc.generate_rsa_keypair()
    fingerprint = enc.get_rsa_fingerprint(public_pem)
    print(f"  Fingerprint: {fingerprint[:16]}...")
    
    small_message = b"Secret"
    ciphertext = enc.encrypt_rsa(small_message, public_pem)
    print(f"  Encrypted: {len(bytes.fromhex(ciphertext))} bytes")
    recovered = enc.decrypt_rsa(ciphertext)
    assert recovered == small_message, "RSA decryption failed"
    print(f"  ✓ Recovered: {recovered}")
    
    # ===== Hybrid Encryption =====
    print("\n[TEST 5] Hybrid Encryption (RSA-4096 + AES-256-GCM)")
    private_pem, public_pem = enc.generate_rsa_keypair()
    result = enc.hybrid_encrypt(message, public_pem)
    print(f"  Session key encrypted: {len(bytes.fromhex(result['encrypted_session_key']))} bytes")
    print(f"  Data encrypted: {len(bytes.fromhex(result['ciphertext']))} bytes")
    recovered = enc.hybrid_decrypt(result)
    assert recovered == message, "Hybrid decryption failed"
    print(f"  ✓ Recovered: {recovered}")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_encryption_suite()
