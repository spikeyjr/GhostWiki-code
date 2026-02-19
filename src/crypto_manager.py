import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class GhostCrypto:
    def __init__(self, password: str):
        # We hold the password in memory to derive keys
        self.password = password.encode()

    def _derive_key(self, salt: bytes) -> bytes:
        """Derives a Fernet-compatible key using the password and a salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password))

    def encrypt_content(self, plaintext: str) -> bytes:
        """
        Generates a new salt, creates a key, encrypts the data.
        Returns: salt (16 bytes) + encrypted_data
        """
        salt = os.urandom(16)
        key = self._derive_key(salt)
        f = Fernet(key)
        # Encrypt the content
        return salt + f.encrypt(plaintext.encode())

    def decrypt_content(self, file_bytes: bytes) -> str:
        """
        Extracts the salt (first 16 bytes), derives the key, decrypts.
        """
        # The first 16 bytes are always the salt
        salt = file_bytes[:16]
        encrypted_data = file_bytes[16:]
        
        key = self._derive_key(salt)
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()