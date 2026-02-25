"""
Unit tests for PasswordHasher utility.

These tests verify the password hashing and verification functionality
using the Argon2id algorithm.
"""
from __future__ import annotations

import pytest
from app.utils import PasswordHasher


@pytest.mark.unit
class TestPasswordHasher:
    """Test suite for PasswordHasher utility."""
    
    @pytest.fixture
    def hasher(self):
        """Create a PasswordHasher instance."""
        return PasswordHasher()
    
    def test_hash_creates_valid_argon2_hash(self, hasher):
        """Test that hash() creates a valid Argon2id hash."""
        password = "test_password_123"
        hashed = hasher.hash(password)
        
        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50
    
    def test_hash_creates_different_hashes_for_same_password(self, hasher):
        """Test that hash() creates different hashes due to salt."""
        password = "test_password_123"
        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)
        
        assert hash1 != hash2  # Different salts
    
    def test_verify_correct_password_returns_true(self, hasher):
        """Test that verify() returns True for correct password."""
        password = "test_password_123"
        hashed = hasher.hash(password)
        
        assert hasher.verify(password, hashed) is True
    
    def test_verify_incorrect_password_returns_false(self, hasher):
        """Test that verify() returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hasher.hash(password)
        
        assert hasher.verify(wrong_password, hashed) is False
    
    def test_hash_empty_password_raises_error(self, hasher):
        """Test that hash() raises ValueError for empty password."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hasher.hash("")
    
    def test_hash_whitespace_only_password_raises_error(self, hasher):
        """Test that hash() raises ValueError for whitespace-only password."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hasher.hash("   ")
    
    def test_verify_with_invalid_hash_raises_error(self, hasher):
        """Test that verify() raises ValueError for invalid hash."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            hasher.verify("password", "invalid_hash")
    
    def test_verify_empty_password_raises_error(self, hasher):
        """Test that verify() raises ValueError for empty password."""
        hashed = hasher.hash("test_password")
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hasher.verify("", hashed)
    
    def test_check_needs_rehash_returns_false_for_current_hash(self, hasher):
        """Test that check_needs_rehash() returns False for current parameters."""
        password = "test_password_123"
        hashed = hasher.hash(password)
        
        assert hasher.check_needs_rehash(hashed) is False
