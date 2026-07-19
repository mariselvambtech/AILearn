"""
Credential encryption/decryption using Fernet symmetric encryption
"""
from cryptography.fernet import Fernet
import json
import os
from dotenv import load_dotenv

load_dotenv()


class CredentialManager:
    """
    Manages encryption and decryption of sensitive credentials
    """
    
    def __init__(self):
        # Get encryption key from environment
        key = os.getenv('ENCRYPTION_KEY')
        
        if not key or key == 'generate-secure-key-using-fernet-generate-key':
            # Generate new key if not set
            key = Fernet.generate_key().decode()
            print(f"⚠️ WARNING: Using generated encryption key. Set ENCRYPTION_KEY in .env:")
            print(f"   ENCRYPTION_KEY={key}")
            print("   Keep this key secret and never share it!")
        
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt_secrets(self, secrets_dict: dict) -> str:
        """
        Encrypt credentials dictionary before storing in database
        
        Args:
            secrets_dict: Dictionary of credentials, e.g.,
                         {"username": "myuser", "password": "mypass123"}
        
        Returns:
            Encrypted string that can be stored in DB
        """
        if not secrets_dict:
            return None
        
        json_str = json.dumps(secrets_dict)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_secrets(self, encrypted_str: str) -> dict:
        """
        Decrypt credentials when needed for execution
        
        Args:
            encrypted_str: Encrypted string from database
        
        Returns:
            Dictionary of decrypted credentials
        """
        if not encrypted_str:
            return {}
        
        decrypted = self.cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())


# Global instance
credential_manager = CredentialManager()


def generate_new_key():
    """
    Generate a new encryption key for the .env file
    Run this once when setting up the server
    """
    key = Fernet.generate_key().decode()
    print("="*60)
    print("New Encryption Key Generated!")
    print("="*60)
    print("\nAdd this to your .env file:")
    print(f"\nENCRYPTION_KEY={key}")
    print("\n⚠️ IMPORTANT: Keep this key secret!")
    print("⚠️ If you lose this key, all encrypted credentials will be lost!")
    print("="*60)
    return key


if __name__ == "__main__":
    # Run this to generate a new key
    generate_new_key()
