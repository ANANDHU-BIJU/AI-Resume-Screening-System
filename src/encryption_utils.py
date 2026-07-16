"""
encryption_utils.py

Encrypt / decrypt files at rest using cryptography's Fernet (symmetric key).
The key is auto-generated on first use and stored in data/.fernet.key.
"""

import os
from cryptography.fernet import Fernet

KEY_FILE = os.path.join("data", ".fernet.key")


def _get_or_create_key() -> bytes:
    """Load the Fernet key from disk, or generate one if it doesn't exist."""
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def get_fernet() -> Fernet:
    """Return a ready-to-use Fernet instance."""
    return Fernet(_get_or_create_key())


# ── File-level helpers ──────────────────────────────────────────

def encrypt_file(src_path: str, dest_path: str | None = None) -> str:
    """
    Encrypt a file and write the cipher-text to *dest_path*.
    If *dest_path* is None the original file is replaced in-place.
    Returns the path of the encrypted file.
    """
    f = get_fernet()
    with open(src_path, "rb") as fh:
        plaintext = fh.read()
    ciphertext = f.encrypt(plaintext)

    out = dest_path or src_path
    with open(out, "wb") as fh:
        fh.write(ciphertext)
    return out


def decrypt_file(src_path: str) -> bytes:
    """Decrypt a Fernet-encrypted file and return the plain bytes."""
    f = get_fernet()
    with open(src_path, "rb") as fh:
        return f.decrypt(fh.read())


def encrypt_bytes(data: bytes) -> bytes:
    """Encrypt raw bytes and return cipher-text bytes."""
    return get_fernet().encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    """Decrypt Fernet cipher-text bytes and return plain bytes."""
    return get_fernet().decrypt(data)


# ── JSON convenience ────────────────────────────────────────────

def save_encrypted_json(obj, path: str):
    """Serialize a Python object to JSON, encrypt, and write to *path*."""
    import json
    plaintext = json.dumps(obj, indent=2).encode("utf-8")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(get_fernet().encrypt(plaintext))


def load_encrypted_json(path: str):
    """Read an encrypted JSON file and return the deserialized object."""
    import json
    with open(path, "rb") as fh:
        plaintext = get_fernet().decrypt(fh.read())
    return json.loads(plaintext.decode("utf-8"))
