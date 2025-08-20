"""
Configuration for JWT Authentication
Supports both HS256 and RS256 algorithms
"""
import os
from pathlib import Path

# JWT Configuration
JWT_ALGORITHM = "RS256"  # Change to "HS256" if needed

# Get the directory where this config.py file is located
CONFIG_DIR = Path(__file__).parent

# RS256 Configuration (asymmetric) - using absolute paths
PRIVATE_KEY_PATH = CONFIG_DIR / "keys" / "private_key.pem"
PUBLIC_KEY_PATH = CONFIG_DIR / "keys" / "public_key.pem"

# HS256 Configuration (symmetric) - fallback
JWT_SECRET = os.getenv("JWT_SECRET", "your_super_secret_key_change_in_production")

# Security settings
TOKEN_EXPIRATION_HOURS = 24  # Token expires in 24 hours

def get_jwt_config():
    """
    Get JWT configuration based on selected algorithm
    
    Returns:
        dict: Configuration for JWT_Manager
    """
    if JWT_ALGORITHM == "RS256":
        # Check if key files exist
        if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
            raise FileNotFoundError(
                f"RSA key files not found! Run 'python generate_keys.py' to create them.\n"
                f"Expected files:\n"
                f"  - {PRIVATE_KEY_PATH}\n"
                f"  - {PUBLIC_KEY_PATH}"
            )
        
        return {
            "algorithm": "RS256",
            "private_key_path": str(PRIVATE_KEY_PATH),
            "public_key_path": str(PUBLIC_KEY_PATH)
        }
    
    elif JWT_ALGORITHM == "HS256":
        if len(JWT_SECRET) < 32:
            print("⚠️ WARNING: JWT_SECRET is too short. Use at least 32 characters for security!")
        
        return {
            "algorithm": "HS256",
            "secret": JWT_SECRET
        }
    
    else:
        raise ValueError(f"Unsupported algorithm: {JWT_ALGORITHM}")

def print_config_info():
    """Print current JWT configuration"""
    print(f"🔐 JWT Configuration:")
    print(f"   Algorithm: {JWT_ALGORITHM}")
    
    if JWT_ALGORITHM == "RS256":
        print(f"   Private Key: {PRIVATE_KEY_PATH}")
        print(f"   Public Key: {PUBLIC_KEY_PATH}")
        print(f"   🔒 Security: Asymmetric (High)")
    else:
        print(f"   Secret Length: {len(JWT_SECRET)} characters")
        print(f"   🔒 Security: Symmetric (Medium)")
    
    print(f"   Token Expiration: {TOKEN_EXPIRATION_HOURS} hours")
    print() 