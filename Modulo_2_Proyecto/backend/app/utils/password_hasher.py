from __future__ import annotations

from typing import TYPE_CHECKING

from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

if TYPE_CHECKING:
    pass


class PasswordHasher:
    """
    Utility for hashing and verifying passwords using Argon2id.
    
    This class provides a simple interface for secure password hashing
    using the Argon2id algorithm, which is the recommended algorithm
    by OWASP for password storage.
    
    Example:
        >>> hasher = PasswordHasher()
        >>> hashed = hasher.hash("my_password")
        >>> hasher.verify("my_password", hashed)
        True
        >>> hasher.verify("wrong_password", hashed)
        False
    """

    def __init__(self) -> None:
        """Initialize the PasswordHasher with default Argon2id parameters."""
        self._hasher = Argon2PasswordHasher()

    def hash(self, password: str) -> str:
        """
        Hash a password using Argon2id.

        Args:
            password: The plain text password to hash

        Returns:
            The hashed password string in Argon2 format

        Raises:
            ValueError: If the password is empty

        Example:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash("my_password")
            >>> hashed.startswith("$argon2id$")
            True
        """
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")

        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: The plain text password to verify
            password_hash: The hashed password to verify against

        Returns:
            True if the password matches the hash, False otherwise

        Raises:
            ValueError: If the password is empty or hash is invalid format

        Example:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash("my_password")
            >>> hasher.verify("my_password", hashed)
            True
            >>> hasher.verify("wrong_password", hashed)
            False
        """
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")

        if not password_hash or not password_hash.startswith("$argon2"):
            raise ValueError("Invalid hash format")

        try:
            self._hasher.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False
        except InvalidHashError:
            raise ValueError("Invalid hash format")

    def check_needs_rehash(self, password_hash: str) -> bool:
        """
        Check if a password hash needs to be rehashed with updated parameters.

        This is useful when you upgrade the Argon2 parameters and want to
        rehash existing passwords on next login.

        Args:
            password_hash: The hashed password to check

        Returns:
            True if the hash should be regenerated, False otherwise

        Example:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash("my_password")
            >>> hasher.check_needs_rehash(hashed)
            False
        """
        return self._hasher.check_needs_rehash(password_hash)
