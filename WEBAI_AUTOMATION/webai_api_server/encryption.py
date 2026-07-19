"""
Credential encryption/decryption using Fernet symmetric encryption.

This file is the "vault" of the WebAI API server (see walkthrough.md →
"Component 1: The Warehouse" → Security). It protects sensitive user
secrets — for example the password a user wants the automation to type
into a login form — so that even if someone steals the database, they
cannot read those secrets.

How it works:
1. The encryption key lives in the `.env` file as `ENCRYPTION_KEY`
   (NOT in the database). The same key both locks and unlocks — that's
   what "symmetric" means.
2. When a user saves a config with secrets, `encrypt_secrets()` turns the
   secrets dict into an unreadable encrypted string before it is stored in
   the `automation_configs.encrypted_secrets` column.
3. When the API prepares steps for execution, `decrypt_secrets()` turns the
   encrypted string back into the original dict so the values can be
   substituted into `{{placeholder}}` steps.

⚠️ IMPORTANT: If `ENCRYPTION_KEY` is lost, every secret already encrypted
becomes permanently unreadable. Back up the `.env` file!
"""
from cryptography.fernet import Fernet
import json
import os
from dotenv import load_dotenv

load_dotenv()


class CredentialManager:
    """
    Locks and unlocks user secrets using Fernet symmetric encryption.

    A single instance `credential_manager` is created at the bottom of this
    file and reused across the whole API server. It reads `ENCRYPTION_KEY`
    from the environment once, at construction time.

    Fernet guarantees that encrypted text cannot be tampered with: it signs
    the ciphertext with an HMAC, so any change makes decryption fail.
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
        Turn a dict of plain secrets into an encrypted string for DB storage.

        Used by `crud.create_automation_config()` / `update_automation_config()`
        before writing to the `encrypted_secrets` column. The dict is
        JSON-serialised first, then encrypted with the Fernet key.

        Args:
            secrets_dict (dict): Plain secrets to lock away, e.g.
                `{"irctc_username": "alice", "irctc_password": "p@ss"}`.

        Returns:
            str | None: An encrypted string like "gAAAAABm...=" that is safe
            to store in the database, or None if the input was empty/falsy
            (so the column can stay NULL).

        Example:
            >>> credential_manager.encrypt_secrets({"password": "secret"})
            'gAAAAABmQ2v...='
        """
        if not secrets_dict:
            return None

        json_str = json.dumps(secrets_dict)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def decrypt_secrets(self, encrypted_str: str) -> dict:
        """
        Turn an encrypted string from the DB back into the original dict.

        Used by `main.get_execution_steps()` when preparing steps for
        playback: the decrypted secrets are merged with the config variables
        and substituted into `{{placeholder}}` step values.

        Args:
            encrypted_str (str): The ciphertext from the
                `automation_configs.encrypted_secrets` column.

        Returns:
            dict: The original secrets dict, e.g.
            `{"irctc_username": "alice", "irctc_password": "p@ss"}`.
            Returns `{}` if `encrypted_str` is empty/None.

        Raises:
            cryptography.fernet.InvalidToken: If the key is wrong or the
            ciphertext was tampered with.

        Example:
            >>> credential_manager.decrypt_secrets('gAAAAABmQ2v...=')
            {'password': 'secret'}
        """
        if not encrypted_str:
            return {}

        decrypted = self.cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())


# Global instance
credential_manager = CredentialManager()


def generate_new_key() -> str:
    """
    Print a fresh Fernet key to copy into the `.env` file.

    Run this once when first setting up the server (`python encryption.py`).
    Copy the printed value into `.env` as `ENCRYPTION_KEY=...`.

    Returns:
        str: The newly generated key (also printed to stdout).

    ⚠️ Generating a new key does NOT re-encrypt existing secrets. If you
    change the key after secrets are already stored, those secrets become
    unreadable. Only run this on a fresh install.
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
