import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.presentation.auth.presenters import AccessClaimsPresenter

def test_access_claims_presenter_from_user():
    # Arrange
    user = MagicMock()
    user.id = 123
    user.role = "ADMIN"
    user.token_version = 2
    
    # Act
    claims = AccessClaimsPresenter.from_user(user)
    
    # Assert
    assert claims["sub"] == "123"
    assert claims["role"] == "ADMIN"
    assert claims["token_version"] == 2
    assert "iat" in claims
    assert "exp" in claims
    
    # Verify expiration (15 minutes = 900 seconds)
    duration = claims["exp"] - claims["iat"]
    assert duration == 900

def test_access_claims_presenter_public_raises_error():
    with pytest.raises(NotImplementedError):
        AccessClaimsPresenter.public(MagicMock())
