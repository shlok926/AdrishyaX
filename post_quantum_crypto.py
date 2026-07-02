"""
Post-Quantum Cryptography Module (PQC)
Implements NIST-standardized quantum-safe algorithms:
- ML-KEM (Kyber) - Key Encapsulation Mechanism
- ML-DSA (Dilithium) - Digital Signature Algorithm
- Hybrid Mode - Classic + Quantum-safe combined
"""

try:
    import oqs
    OQS_AVAILABLE = True
except (ImportError, RuntimeError):
    OQS_AVAILABLE = False

import os
import base64
import hashlib
import json
from typing import Dict, Tuple, Optional
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes


class PostQuantumCrypto:
    """NIST-standardized post-quantum cryptography implementation"""
    
    def __init__(self):
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs library not available on this system")
        self.algorithms = {
            'ML-KEM': 'ML-KEM-768',      # Kyber - 256-bit security equivalent
            'ML-DSA': 'ML-DSA-65',        # Dilithium - 256-bit security equivalent
        }
        self.hybrid_rsa_bits = 4096
    
    # ======================== ML-KEM (Key Encapsulation) ========================
    
    def generate_mlkem_keys(self) -> Dict:
        """
        Generate ML-KEM key pair for quantum-safe key exchange
        
        Returns:
            {
                'algorithm': 'ML-KEM-768',
                'public_key': base64-encoded public key,
                'private_key': base64-encoded private key,
                'key_size': size in bytes,
                'security_level': '256-bit equivalent'
            }
        """
        try:
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'])
            public_key = keygen.generate_keypair()
            private_key = keygen.secret_key()
            
            return {
                'status': 'success',
                'algorithm': 'ML-KEM-768',
                'public_key': base64.b64encode(public_key).decode('utf-8'),
                'private_key': base64.b64encode(private_key).decode('utf-8'),
                'key_size': len(public_key),
                'security_level': '256-bit equivalent',
                'note': 'ML-KEM is NIST-standardized post-quantum KEM (Kyber)'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def mlkem_encapsulate(self, public_key_b64: str) -> Dict:
        """
        Perform ML-KEM encapsulation: derive shared secret using public key
        
        Args:
            public_key_b64: Base64-encoded public key
        
        Returns:
            {
                'ciphertext': base64-encoded encapsulated key,
                'shared_secret': base64-encoded shared secret,
                'size_bytes': size of ciphertext
            }
        """
        try:
            public_key = base64.b64decode(public_key_b64)
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'])
            ciphertext, shared_secret = keygen.encap_secret(public_key)
            
            return {
                'status': 'success',
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'shared_secret': base64.b64encode(shared_secret).decode('utf-8'),
                'size_bytes': len(ciphertext),
                'shared_secret_size': len(shared_secret)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def mlkem_decapsulate(self, ciphertext_b64: str, private_key_b64: str) -> Dict:
        """
        Perform ML-KEM decapsulation: extract shared secret using private key
        
        Args:
            ciphertext_b64: Base64-encoded ciphertext
            private_key_b64: Base64-encoded private key
        
        Returns:
            {
                'shared_secret': base64-encoded shared secret,
                'size_bytes': size of shared secret
            }
        """
        try:
            ciphertext = base64.b64decode(ciphertext_b64)
            private_key = base64.b64decode(private_key_b64)
            
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'], secret_key=private_key)
            shared_secret = keygen.decap_secret(ciphertext)
            
            return {
                'status': 'success',
                'shared_secret': base64.b64encode(shared_secret).decode('utf-8'),
                'size_bytes': len(shared_secret)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # ======================== ML-DSA (Digital Signatures) ========================
    
    def generate_mldsa_keys(self) -> Dict:
        """
        Generate ML-DSA key pair for quantum-safe digital signatures
        
        Returns:
            {
                'algorithm': 'ML-DSA-65',
                'public_key': base64-encoded public key,
                'private_key': base64-encoded private key,
                'security_level': '256-bit equivalent'
            }
        """
        try:
            sig = oqs.Signature(self.algorithms['ML-DSA'])
            public_key = sig.generate_keypair()
            private_key = sig.secret_key()
            
            return {
                'status': 'success',
                'algorithm': 'ML-DSA-65',
                'public_key': base64.b64encode(public_key).decode('utf-8'),
                'private_key': base64.b64encode(private_key).decode('utf-8'),
                'public_key_size': len(public_key),
                'security_level': '256-bit equivalent',
                'note': 'ML-DSA is NIST-standardized signature algorithm (Dilithium)'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def mldsa_sign(self, data: bytes, private_key_b64: str) -> Dict:
        """
        Sign data using ML-DSA private key
        
        Args:
            data: Bytes to sign
            private_key_b64: Base64-encoded private key
        
        Returns:
            {
                'signature': base64-encoded signature,
                'data_hash': SHA-256 hash of data,
                'signature_size': size in bytes
            }
        """
        try:
            private_key = base64.b64decode(private_key_b64)
            sig = oqs.Signature(self.algorithms['ML-DSA'], secret_key=private_key)
            signature = sig.sign(data)
            
            data_hash = hashlib.sha256(data).digest()
            
            return {
                'status': 'success',
                'signature': base64.b64encode(signature).decode('utf-8'),
                'data_hash': base64.b64encode(data_hash).decode('utf-8'),
                'signature_size': len(signature)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def mldsa_verify(self, data: bytes, signature_b64: str, public_key_b64: str) -> Dict:
        """
        Verify ML-DSA signature
        
        Args:
            data: Original data bytes
            signature_b64: Base64-encoded signature
            public_key_b64: Base64-encoded public key
        
        Returns:
            {
                'valid': bool,
                'message': verification result
            }
        """
        try:
            signature = base64.b64decode(signature_b64)
            public_key = base64.b64decode(public_key_b64)
            
            sig = oqs.Signature(self.algorithms['ML-DSA'], secret_key=b'')
            is_valid = sig.verify(data, signature, public_key)
            
            return {
                'status': 'success',
                'valid': is_valid,
                'message': 'Signature is valid!' if is_valid else 'Signature verification failed!'
            }
        except Exception as e:
            return {
                'status': 'error',
                'valid': False,
                'message': f'Verification error: {str(e)}'
            }
    
    # ======================== Hybrid Mode (RSA + ML-KEM) ========================
    
    def generate_hybrid_keys(self) -> Dict:
        """
        Generate hybrid key pair combining RSA-4096 + ML-KEM
        Future-proof: protects against both classical and quantum attacks
        
        Returns:
            {
                'rsa_public_key': PEM format,
                'rsa_private_key': PEM format,
                'mlkem_public_key': base64,
                'mlkem_private_key': base64
            }
        """
        try:
            # Generate RSA keys
            rsa_key = RSA.generate(self.hybrid_rsa_bits)
            rsa_pub = rsa_key.publickey().export_key('PEM').decode('utf-8')
            rsa_priv = rsa_key.export_key('PEM').decode('utf-8')
            
            # Generate ML-KEM keys
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'])
            mlkem_pub = keygen.generate_keypair()
            mlkem_priv = keygen.secret_key()
            
            return {
                'status': 'success',
                'hybrid_type': 'RSA-4096 + ML-KEM-768',
                'rsa_public_key': rsa_pub,
                'rsa_private_key': rsa_priv,
                'mlkem_public_key': base64.b64encode(mlkem_pub).decode('utf-8'),
                'mlkem_private_key': base64.b64encode(mlkem_priv).decode('utf-8'),
                'security_note': 'Protects against both classical and quantum attacks'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def hybrid_encrypt(self, data: bytes, rsa_public_key_pem: str, mlkem_public_key_b64: str) -> Dict:
        """
        Hybrid encryption: RSA + ML-KEM
        Uses both classical (RSA) and quantum-safe (ML-KEM) encryption
        
        Args:
            data: Data to encrypt
            rsa_public_key_pem: PEM-formatted RSA public key
            mlkem_public_key_b64: Base64-encoded ML-KEM public key
        
        Returns:
            {
                'rsa_ciphertext': base64-encoded RSA encrypted key,
                'mlkem_ciphertext': base64-encoded ML-KEM ciphertext,
                'data_ciphertext': base64-encoded encrypted data
            }
        """
        try:
            # Generate AES key for symmetric encryption
            aes_key = get_random_bytes(32)  # 256-bit AES key
            
            # Encrypt AES key with RSA
            rsa_key = RSA.import_key(rsa_public_key_pem.encode('utf-8'))
            rsa_cipher = PKCS1_OAEP.new(rsa_key)
            rsa_ciphertext = rsa_cipher.encrypt(aes_key)
            
            # Encapsulate with ML-KEM
            mlkem_pub = base64.b64decode(mlkem_public_key_b64)
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'])
            mlkem_ct, mlkem_ss = keygen.encap_secret(mlkem_pub)
            
            # XOR AES key with ML-KEM shared secret for additional security
            hybrid_key = bytes(a ^ b for a, b in zip(aes_key, mlkem_ss[:32]))
            
            # Encrypt data with hybrid key using AES-GCM
            from Crypto.Cipher import AES
            cipher = AES.new(hybrid_key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(data)
            
            return {
                'status': 'success',
                'rsa_ciphertext': base64.b64encode(rsa_ciphertext).decode('utf-8'),
                'mlkem_ciphertext': base64.b64encode(mlkem_ct).decode('utf-8'),
                'data_ciphertext': base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8'),
                'encryption_type': 'Hybrid (RSA-4096 + ML-KEM-768 + AES-256-GCM)'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def hybrid_decrypt(self, rsa_ciphertext_b64: str, mlkem_ciphertext_b64: str, 
                      data_ciphertext_b64: str, rsa_private_key_pem: str, 
                      mlkem_private_key_b64: str) -> Dict:
        """
        Hybrid decryption: recover original data using both RSA and ML-KEM
        
        Args:
            rsa_ciphertext_b64: Base64-encoded RSA-encrypted key
            mlkem_ciphertext_b64: Base64-encoded ML-KEM ciphertext
            data_ciphertext_b64: Base64-encoded encrypted data
            rsa_private_key_pem: PEM-formatted RSA private key
            mlkem_private_key_b64: Base64-encoded ML-KEM private key
        
        Returns:
            {
                'decrypted_data': base64-encoded original data
            }
        """
        try:
            # Decrypt AES key with RSA
            rsa_ciphertext = base64.b64decode(rsa_ciphertext_b64)
            rsa_key = RSA.import_key(rsa_private_key_pem.encode('utf-8'))
            rsa_cipher = PKCS1_OAEP.new(rsa_key)
            aes_key = rsa_cipher.decrypt(rsa_ciphertext)
            
            # Decapsulate with ML-KEM
            mlkem_ct = base64.b64decode(mlkem_ciphertext_b64)
            mlkem_priv = base64.b64decode(mlkem_private_key_b64)
            keygen = oqs.KeyEncapsulation(self.algorithms['ML-KEM'], secret_key=mlkem_priv)
            mlkem_ss = keygen.decap_secret(mlkem_ct)
            
            # Reconstruct hybrid key
            hybrid_key = bytes(a ^ b for a, b in zip(aes_key, mlkem_ss[:32]))
            
            # Decrypt data with hybrid key
            from Crypto.Cipher import AES
            data_ct = base64.b64decode(data_ciphertext_b64)
            nonce = data_ct[:16]
            tag = data_ct[16:32]
            ciphertext = data_ct[32:]
            
            cipher = AES.new(hybrid_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return {
                'status': 'success',
                'decrypted_data': base64.b64encode(plaintext).decode('utf-8'),
                'decryption_type': 'Hybrid (RSA-4096 + ML-KEM-768 + AES-256-GCM)'
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Decryption failed: {str(e)}'}
    
    # ======================== Utility Functions ========================
    
    def get_algorithm_info(self, algorithm: str) -> Dict:
        """Get information about algorithm"""
        info = {
            'ML-KEM': {
                'full_name': 'Module-Lattice-Based Key-Encapsulation Mechanism',
                'alias': 'Kyber (NIST standardized)',
                'security': '256-bit post-quantum security',
                'use_case': 'Secure key exchange against quantum adversaries',
                'key_size': '768 bytes (public), 1632 bytes (private)',
                'ciphertext_size': '1088 bytes',
                'shared_secret_size': '32 bytes'
            },
            'ML-DSA': {
                'full_name': 'Module-Lattice-Based Digital Signature Algorithm',
                'alias': 'Dilithium (NIST standardized)',
                'security': '256-bit post-quantum security',
                'use_case': 'Digital signatures resistant to quantum attacks',
                'public_key_size': '1312 bytes',
                'private_key_size': '2544 bytes',
                'signature_size': '3309 bytes'
            },
            'Hybrid': {
                'full_name': 'RSA-4096 + ML-KEM-768 Hybrid Encryption',
                'security': 'Classical + Post-quantum protection',
                'use_case': 'Maximum security: protects against both classical and quantum threats',
                'components': 'RSA-4096 (classical) + ML-KEM-768 (post-quantum)',
                'recommended_for': 'Long-term archival, highly sensitive data'
            }
        }
        return info.get(algorithm, {'status': 'error', 'message': 'Unknown algorithm'})


# Global instance
pqc = PostQuantumCrypto()
