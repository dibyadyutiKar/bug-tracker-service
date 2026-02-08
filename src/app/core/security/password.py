"""Password hashing using Argon2."""

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config.settings import settings


class PasswordHasher:
    """Password hashing service using Argon2.

    Argon2 is the winner of the Password Hashing Competition and
    is recommended for secure password storage.
    """

    def __init__(self):
        """Initialize Argon2 hasher with configured parameters."""
        self._hasher = Argon2Hasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost,
            parallelism=settings.argon2_parallelism,
        )

    def hash(self, password: str) -> str:
        """Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash.

        Args:
            password: Plain text password to verify
            password_hash: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            self._hasher.verify(password_hash, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Check if a password hash needs to be rehashed.

        This can happen when Argon2 parameters change.

        Args:
            password_hash: Stored password hash

        Returns:
            True if rehash is needed, False otherwise
        """
        return self._hasher.check_needs_rehash(password_hash)


# Global password hasher instance
password_hasher = PasswordHasher()
