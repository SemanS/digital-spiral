"""Encryption service for sensitive data."""

import base64
import os
from typing import Any, Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, encryption_key: str = None):
        """Initialize encryption service.

        Args:
            encryption_key: Base64-encoded encryption key.
                           If not provided, uses ENCRYPTION_KEY env var.
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if encryption_key is None:
            # Generate a new key (for development only!)
            encryption_key = Fernet.generate_key().decode()
            print(f"WARNING: Using generated encryption key: {encryption_key}")
            print("Set ENCRYPTION_KEY environment variable in production!")
        
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string.

        Args:
            data: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        encrypted = self.fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted string
        """
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = self.fernet.decrypt(encrypted)
        return decrypted.decode()

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary.

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted JSON string
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt a dictionary.

        Args:
            encrypted_data: Base64-encoded encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key.

        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """Derive encryption key from password.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)

        Returns:
            Tuple of (base64-encoded key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt


class CredentialEncryption:
    """Helper for encrypting/decrypting credentials."""

    def __init__(self, encryption_service: EncryptionService = None):
        """Initialize credential encryption.

        Args:
            encryption_service: Encryption service instance
        """
        self.encryption_service = encryption_service or get_encryption_service()

    def encrypt_auth_config(self, auth_config: Dict[str, Any]) -> str:
        """Encrypt authentication configuration.

        Args:
            auth_config: Authentication configuration dictionary

        Returns:
            Encrypted auth config string
        """
        return self.encryption_service.encrypt_dict(auth_config)

    def decrypt_auth_config(self, encrypted_auth_config: str) -> Dict[str, Any]:
        """Decrypt authentication configuration.

        Args:
            encrypted_auth_config: Encrypted auth config string

        Returns:
            Decrypted auth config dictionary
        """
        return self.encryption_service.decrypt_dict(encrypted_auth_config)

    def encrypt_api_token(self, token: str) -> str:
        """Encrypt API token.

        Args:
            token: API token

        Returns:
            Encrypted token
        """
        return self.encryption_service.encrypt(token)

    def decrypt_api_token(self, encrypted_token: str) -> str:
        """Decrypt API token.

        Args:
            encrypted_token: Encrypted token

        Returns:
            Decrypted token
        """
        return self.encryption_service.decrypt(encrypted_token)


# Global encryption service instance
_encryption_service: EncryptionService = None


def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def get_credential_encryption() -> CredentialEncryption:
    """Get credential encryption helper.

    Returns:
        CredentialEncryption instance
    """
    return CredentialEncryption(get_encryption_service())


__all__ = [
    "EncryptionService",
    "CredentialEncryption",
    "get_encryption_service",
    "get_credential_encryption",
]

