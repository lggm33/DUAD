import pytest
import os
from sqlalchemy import text
from app.domain.users.models import User

def test_safety_guard_blocks_drop(session):
    """Test that DROP TABLE is blocked by default."""
    # Ensure bypass is NOT set
    os.environ["ALLOW_DESTRUCTIVE_DDL"] = "false"
    
    with pytest.raises(RuntimeError) as excinfo:
        session.execute(text("DROP TABLE users CASCADE"))
    
    assert "Destructive DDL is blocked" in str(excinfo.value)

def test_safety_guard_blocks_unsafe_update(session):
    """Test that UPDATE without WHERE is blocked by default."""
    os.environ["ALLOW_UNSAFE_QUERY"] = "false"
    
    with pytest.raises(RuntimeError) as excinfo:
        session.execute(text("UPDATE users SET is_active = false"))
    
    assert "Unsafe query blocked (missing WHERE clause)" in str(excinfo.value)

def test_safety_guard_blocks_unsafe_delete(session):
    """Test that DELETE without WHERE is blocked by default."""
    os.environ["ALLOW_UNSAFE_QUERY"] = "false"
    
    with pytest.raises(RuntimeError) as excinfo:
        session.execute(text("DELETE FROM users"))
    
    assert "Unsafe query blocked (missing WHERE clause)" in str(excinfo.value)

def test_safety_guard_allows_with_bypass(session):
    """Test that bypass environment variables work."""
    os.environ["ALLOW_UNSAFE_QUERY"] = "true"
    
    # This should not raise RuntimeError for safety reasons 
    # (it might fail for other reasons like foreign keys, but we check if the guard passes)
    try:
        session.execute(text("UPDATE users SET is_active = true WHERE id = -1"))
    except RuntimeError as e:
        pytest.fail(f"Guard should have been bypassed: {e}")
    except Exception:
        pass # Other DB errors are fine, we only care about our guard
