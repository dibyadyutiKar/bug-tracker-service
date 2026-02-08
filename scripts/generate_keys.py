#!/usr/bin/env python3
"""Generate RSA key pair for JWT signing."""

import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keys(key_dir: str = "./keys", key_size: int = 2048) -> None:
    """Generate RSA key pair for JWT RS256 signing.

    Args:
        key_dir: Directory to store keys
        key_size: RSA key size (default 2048)
    """
    key_path = Path(key_dir)
    key_path.mkdir(parents=True, exist_ok=True)

    private_key_path = key_path / "private_key.pem"
    public_key_path = key_path / "public_key.pem"

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )

    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Get public key
    public_key = private_key.public_key()

    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Write keys to files
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)

    # Set restrictive permissions on private key
    os.chmod(private_key_path, 0o600)

    print(f"Generated RSA key pair:")
    print(f"  Private key: {private_key_path}")
    print(f"  Public key:  {public_key_path}")
    print(f"\nKey size: {key_size} bits")
    print(f"\nIMPORTANT: Keep the private key secure and never commit it to version control!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate RSA keys for JWT signing")
    parser.add_argument(
        "--key-dir",
        default="./keys",
        help="Directory to store keys (default: ./keys)",
    )
    parser.add_argument(
        "--key-size",
        type=int,
        default=2048,
        help="RSA key size (default: 2048)",
    )
    args = parser.parse_args()

    generate_rsa_keys(args.key_dir, args.key_size)
