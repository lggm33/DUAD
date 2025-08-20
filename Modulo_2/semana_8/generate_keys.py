#!/usr/bin/env python3
"""
Script to generate RSA key pair for JWT RS256 algorithm
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

def generate_rsa_keys():
    """Generate RSA private and public key pair"""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048  # 2048 bits is secure for most applications
    )
    
    # Get public key from private key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def save_keys_to_files():
    """Generate and save keys to files"""
    private_pem, public_pem = generate_rsa_keys()
    
    # Create keys directory if it doesn't exist
    os.makedirs('keys', exist_ok=True)
    
    # Save private key
    with open('keys/private_key.pem', 'wb') as f:
        f.write(private_pem)
    
    # Save public key
    with open('keys/public_key.pem', 'wb') as f:
        f.write(public_pem)
    
    print("✅ RSA key pair generated successfully!")
    print("📁 Files created:")
    print("   - keys/private_key.pem (keep secret!)")
    print("   - keys/public_key.pem (can be shared)")
    print()
    print("🔒 IMPORTANT SECURITY NOTES:")
    print("   - Keep private_key.pem SECURE and NEVER commit to git")
    print("   - Only the authentication service needs the private key")
    print("   - Other services only need the public key for verification")
    print("   - Add keys/ to your .gitignore file")

def show_keys_content():
    """Display the content of generated keys"""
    try:
        with open('keys/private_key.pem', 'r') as f:
            private_key_content = f.read()
        
        with open('keys/public_key.pem', 'r') as f:
            public_key_content = f.read()
        
        print("\n📄 PRIVATE KEY (keep secret):")
        print("=" * 50)
        print(private_key_content)
        
        print("\n📄 PUBLIC KEY (shareable):")
        print("=" * 50)
        print(public_key_content)
        
    except FileNotFoundError:
        print("❌ Key files not found. Run generate first.")

if __name__ == "__main__":
    print("🔑 RSA Key Generator for JWT RS256")
    print("=" * 40)
    
    # Check if keys already exist
    if os.path.exists('keys/private_key.pem') and os.path.exists('keys/public_key.pem'):
        print("⚠️  Keys already exist!")
        response = input("Do you want to regenerate them? (y/N): ").lower()
        if response != 'y':
            print("Using existing keys...")
            show_keys_content()
            exit()
    
    # Generate new keys
    save_keys_to_files()
    show_keys_content() 