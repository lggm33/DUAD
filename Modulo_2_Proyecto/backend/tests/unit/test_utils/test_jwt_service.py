"""
Unit tests for JwtService utility.

These tests verify the JWT token issuance and verification functionality.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.utils import JwtService, JwtError, JwtExpiredError, JwtInvalidError


@pytest.mark.unit
class TestJwtService:
    """Test suite for JwtService."""
    
    @pytest.fixture
    def jwt_service(self):
        """Create a JwtService instance with test secret."""
        return JwtService(secret_key="test-secret-key-12345")
    
    def test_init_with_empty_secret_raises_error(self):
        """Test that __init__ raises ValueError for empty secret key."""
        with pytest.raises(ValueError, match="Secret key cannot be empty"):
            JwtService(secret_key="")
    
    def test_issue_access_creates_valid_jwt(self, jwt_service):
        """Test that issue_access() creates a valid JWT."""
        token = jwt_service.issue_access(
            user_id=123,
            role="USER",
            token_version=1
        )
        
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # header.payload.signature
    
    def test_issue_access_with_invalid_user_id_raises_error(self, jwt_service):
        """Test that issue_access() raises ValueError for invalid user_id."""
        with pytest.raises(ValueError, match="User ID must be positive"):
            jwt_service.issue_access(user_id=0, role="USER", token_version=1)
        
        with pytest.raises(ValueError, match="User ID must be positive"):
            jwt_service.issue_access(user_id=-1, role="USER", token_version=1)
    
    def test_issue_access_with_empty_role_raises_error(self, jwt_service):
        """Test that issue_access() raises ValueError for empty role."""
        with pytest.raises(ValueError, match="Role cannot be empty"):
            jwt_service.issue_access(user_id=123, role="", token_version=1)
        
        with pytest.raises(ValueError, match="Role cannot be empty"):
            jwt_service.issue_access(user_id=123, role="   ", token_version=1)
    
    def test_issue_access_with_invalid_token_version_raises_error(self, jwt_service):
        """Test that issue_access() raises ValueError for invalid token_version."""
        with pytest.raises(ValueError, match="Token version must be at least 1"):
            jwt_service.issue_access(user_id=123, role="USER", token_version=0)
    
    def test_verify_valid_token_returns_claims(self, jwt_service):
        """Test that verify() returns claims for valid token."""
        token = jwt_service.issue_access(
            user_id=123,
            role="USER",
            token_version=1
        )
        
        claims = jwt_service.verify(token)
        
        assert claims["sub"] == "123"
        assert claims["role"] == "USER"
        assert claims["token_version"] == 1
        assert "iat" in claims
        assert "exp" in claims
    
    def test_verify_admin_role_token(self, jwt_service):
        """Test that verify() works with ADMIN role."""
        token = jwt_service.issue_access(
            user_id=456,
            role="ADMIN",
            token_version=2
        )
        
        claims = jwt_service.verify(token)
        
        assert claims["sub"] == "456"
        assert claims["role"] == "ADMIN"
        assert claims["token_version"] == 2
    
    def test_verify_expired_token_raises_error(self, jwt_service):
        """Test that verify() raises JwtExpiredError for expired token."""
        # Create a token that expires immediately
        service_with_short_expiry = JwtService(
            secret_key="test-secret",
            access_token_expires=1  # 1 second
        )
        
        token = service_with_short_expiry.issue_access(123, "USER", 1)
        
        # Wait for token to expire
        time.sleep(2)
        
        with pytest.raises(JwtExpiredError, match="Token has expired"):
            service_with_short_expiry.verify(token)
    
    def test_verify_tampered_token_raises_error(self, jwt_service):
        """Test that verify() raises JwtInvalidError for tampered token."""
        token = jwt_service.issue_access(123, "USER", 1)
        
        # Tamper with the signature
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.xxxxx"
        
        with pytest.raises(JwtInvalidError, match="Invalid token"):
            jwt_service.verify(tampered)
    
    def test_verify_invalid_format_raises_error(self, jwt_service):
        """Test that verify() raises JwtInvalidError for invalid format."""
        with pytest.raises(JwtInvalidError, match="Invalid token"):
            jwt_service.verify("not.a.valid.jwt")
    
    def test_verify_empty_token_raises_error(self, jwt_service):
        """Test that verify() raises JwtInvalidError for empty token."""
        with pytest.raises(JwtInvalidError, match="Token cannot be empty"):
            jwt_service.verify("")
        
        with pytest.raises(JwtInvalidError, match="Token cannot be empty"):
            jwt_service.verify("   ")
    
    def test_different_secret_key_fails_verification(self):
        """Test that tokens from different keys fail verification."""
        service1 = JwtService("secret-key-1")
        service2 = JwtService("secret-key-2")
        
        token = service1.issue_access(123, "USER", 1)
        
        with pytest.raises(JwtInvalidError, match="Invalid token"):
            service2.verify(token)
    
    def test_token_expiration_time_is_correct(self, jwt_service):
        """Test that token expiration is set correctly."""
        token = jwt_service.issue_access(123, "USER", 1)
        
        claims = jwt_service.verify(token)
        
        # Token should expire 3600 seconds (1 hour) from issuance
        exp_time = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
        
        # Check that exp is 3600 seconds after iat
        time_diff = (exp_time - iat_time).total_seconds()
        assert time_diff == 3600
    
    def test_custom_expiration_time(self):
        """Test that custom expiration time works."""
        service = JwtService(
            secret_key="test-secret",
            access_token_expires=7200  # 2 hours
        )
        
        token = service.issue_access(123, "USER", 1)
        claims = service.verify(token)
        
        exp_time = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
        
        # Check that exp is 7200 seconds (2 hours) after iat
        assert (exp_time - iat_time).total_seconds() == 7200
