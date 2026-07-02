from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

def derive_key(password: bytes, salt: bytes, length: int = 32) -> bytes:
    return hash_secret_raw(password, salt, time_cost=3, memory_cost=65536, parallelism=4, hash_len=length, type=Type.ID)

def encrypt(key: bytes, plaintext: bytes) -> bytes:
    aes = AESGCM(key)
    iv = os.urandom(12)
    ct = aes.encrypt(iv, plaintext, None)
    return iv + ct

def decrypt(key: bytes, data: bytes) -> bytes:
    iv = data[:12]
    ct = data[12:]
    aes = AESGCM(key)
    return aes.decrypt(iv, ct, None)

def generate_ecdh_keypair(curve=ec.SECP256R1()):
    private_key = ec.generate_private_key(curve)
    public_key = private_key.public_key()
    return private_key, public_key

def public_key_fingerprint(public_key):
    der = public_key.public_bytes(encoding=serialization.Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(der)
    return digest.finalize().hex()

def derive_shared_secret(private_key, peer_public_key):
    shared = private_key.exchange(ec.ECDH(), peer_public_key)
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'StegoForge ECDH')
    return hkdf.derive(shared)
