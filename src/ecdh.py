"""
ECDH Key Exchange Module
Implements Elliptic Curve Diffie-Hellman for secure key negotiation
Supports multiple curves: Y-256a (custom), Curve25519, P-256 (secp256r1)
"""

import logging
from typing import Tuple, Dict
import os
import struct

logger = logging.getLogger(__name__)


class ECDHKeyExchange:
    """ECDH key exchange implementation with multiple curve support."""
    
    # Supported curves
    CURVES = {
        'curve25519': {
            'name': 'Curve25519',
            'bits': 256,
            'description': 'Daniel Bernstein Montgomery curve (High Speed)'
        },
        'p256': {
            'name': 'P-256',
            'bits': 256,
            'description': 'NIST secp256r1 standard curve (High Compatibility)'
        }
    }
    
    def __init__(self, curve: str = 'curve25519'):
        """Initialize ECDH with specified curve."""
        if curve.lower() not in self.CURVES:
            raise ValueError(f'Unsupported curve: {curve}. Available: {list(self.CURVES.keys())}')
        
        self.curve = curve.lower()
        self.curve_info = self.CURVES[self.curve]
        
        # Load appropriate library
        self._load_curve_library()
    
    def _load_curve_library(self):
        """Load the appropriate cryptography library for the curve."""
        if self.curve == 'p256':
            try:
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.backends import default_backend
                self.ec = ec
                self.backend = default_backend()
                self.key_size = 256
                logger.info('Loaded P-256 (secp256r1) via cryptography library')
            except ImportError:
                raise ImportError('cryptography library required for P-256')
        
        elif self.curve == 'curve25519':
            try:
                from cryptography.hazmat.primitives.asymmetric import x25519
                from cryptography.hazmat.backends import default_backend
                self.x25519 = x25519
                self.backend = default_backend()
                logger.info('Loaded Curve25519 via cryptography library')
            except ImportError:
                raise ImportError('cryptography library required for Curve25519')
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate ECDH keypair (private key, public key).
        
        Returns:
            (private_key_bytes, public_key_bytes)
        """
        try:
            from cryptography.hazmat.primitives import serialization
            
            if self.curve == 'p256':
                # Generate P-256 keypair
                private_key = self.ec.generate_private_key(
                    self.ec.SECP256R1(), 
                    self.backend
                )
                
                # Serialize keys
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_pem = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                logger.info('Generated P-256 keypair')
                return private_pem, public_pem
            
            elif self.curve == 'curve25519':
                # Generate Curve25519 keypair
                private_key = self.x25519.X25519PrivateKey.generate()
                
                # Get raw bytes
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_bytes = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                
                logger.info('Generated Curve25519 keypair')
                return private_bytes, public_bytes
        
        except Exception as e:
            logger.error(f'Keypair generation failed: {e}')
            raise
    
    def compute_shared_secret(self, private_key: bytes, peer_public_key: bytes) -> bytes:
        """
        Compute shared secret using peer's public key.
        
        Args:
            private_key: Our private key (from generate_keypair)
            peer_public_key: Peer's public key
        
        Returns:
            Shared secret (32 bytes)
        """
        try:
            from cryptography.hazmat.primitives import serialization
            
            if self.curve == 'p256':
                # Load private key
                private_key_obj = serialization.load_pem_private_key(
                    private_key,
                    password=None,
                    backend=self.backend
                )
                
                # Load peer public key
                peer_public_key_obj = serialization.load_pem_public_key(
                    peer_public_key,
                    backend=self.backend
                )
                
                # Compute shared secret
                from cryptography.hazmat.primitives.kdf.hkdf import HKDF
                from cryptography.hazmat.primitives import hashes
                
                # ECDH operation
                shared_key = private_key_obj.exchange(
                    self.ec.ECDH(),
                    peer_public_key_obj
                )
                
                # Derive 32-byte key using HKDF
                hkdf = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=None,
                    info=b'stegoforge_ecdh_p256',
                    backend=self.backend
                )
                
                derived_key = hkdf.derive(shared_key)
                logger.info('Computed P-256 shared secret')
                return derived_key
            
            elif self.curve == 'curve25519':
                # Load private key
                private_key_obj = self.x25519.X25519PrivateKey.from_private_bytes(private_key)
                
                # Load peer public key
                peer_public_key_obj = self.x25519.X25519PublicKey.from_public_bytes(peer_public_key)
                
                # Exchange
                shared_secret = private_key_obj.exchange(peer_public_key_obj)
                
                logger.info('Computed Curve25519 shared secret')
                return shared_secret[:32]  # Return 32 bytes
        
        except Exception as e:
            logger.error(f'Shared secret computation failed: {e}')
            raise
    
    def get_curve_info(self) -> Dict:
        """Get information about current curve."""
        return {
            'name': self.curve_info['name'],
            'identifier': self.curve,
            'key_size': self.curve_info['bits'],
            'description': self.curve_info['description']
        }
    
    @staticmethod
    def get_available_curves() -> Dict:
        """Get list of all available curves."""
        return ECDHKeyExchange.CURVES


def perform_key_exchange(curve: str = 'p256') -> Dict:
    """
    Perform a complete ECDH exchange simulation (for testing).
    
    Returns:
        Dict with: shared_secret, alice_public_key, bob_public_key
    """
    try:
        # Alice's side
        alice = ECDHKeyExchange(curve)
        alice_private, alice_public = alice.generate_keypair()
        
        # Bob's side
        bob = ECDHKeyExchange(curve)
        bob_private, bob_public = bob.generate_keypair()
        
        # Exchange
        alice_shared = alice.compute_shared_secret(alice_private, bob_public)
        bob_shared = bob.compute_shared_secret(bob_private, alice_public)
        
        # Verify they match
        if alice_shared != bob_shared:
            logger.warning('Shared secrets do not match!')
        
        return {
            'success': alice_shared == bob_shared,
            'curve': curve,
            'alice_public_key': alice_public.hex() if isinstance(alice_public, bytes) else alice_public,
            'bob_public_key': bob_public.hex() if isinstance(bob_public, bytes) else bob_public,
            'shared_secret': alice_shared.hex(),
            'secret_length': len(alice_shared)
        }
    
    except Exception as e:
        logger.error(f'Key exchange simulation failed: {e}')
        return {
            'success': False,
            'error': str(e)
        }
