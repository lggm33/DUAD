#!/usr/bin/env python3
"""
Script to add a new user to the Lyfter Car Rental System
Usage: python add_user.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import UserRepository

def get_user_input():
    """Get user data from user input"""
    print("🆕 ADD NEW USER")
    print("=" * 40)
    
    name = input("Full name: ").strip()
    if not name:
        print("❌ Name is required")
        return None
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email is required")
        return None
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username is required")
        return None
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password is required")
        return None
    
    date_of_birth = input("Date of birth (YYYY-MM-DD): ").strip()
    if not date_of_birth:
        print("❌ Date of birth is required")
        return None
    
    # Validate date format
    try:
        datetime.strptime(date_of_birth, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        return None
    
    account_state = input("Account state (active/inactive) [active]: ").strip().lower()
    if not account_state:
        account_state = 'active'
    
    if account_state not in ['active', 'inactive']:
        print("❌ Invalid account state. Use 'active' or 'inactive'")
        return None
    
    return {
        'name': name,
        'email': email,
        'username': username,
        'password': password,
        'date_of_birth': date_of_birth,
        'account_state': account_state == 'active'
    }

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - ADD USER")
    print("=" * 50)
    
    # Get user data from user input
    user_data = get_user_input()
    if not user_data:
        print("❌ Operation cancelled")
        sys.exit(1)
    
    try:
        # Create repository and check if user already exists
        user_repo = UserRepository()
        
        if user_repo.user_exists(email=user_data['email']):
            print(f"❌ Error: Email '{user_data['email']}' already in use")
            sys.exit(1)
        
        if user_repo.user_exists(username=user_data['username']):
            print(f"❌ Error: Username '{user_data['username']}' already in use")
            sys.exit(1)
        
        # Create user
        new_user = user_repo.create_user(user_data)
        
        if new_user:
            print("\n✅ User created successfully!")
            print("=" * 40)
            print(f"ID: {new_user['id']}")
            print(f"Name: {new_user['name']}")
            print(f"Email: {new_user['email']}")
            print(f"Username: {new_user['username']}")
            print(f"Account State: {'Active' if new_user['account_state'] else 'Inactive'}")
            print(f"Created: {new_user['created_at']}")
            print("\n🎉 ¡User added successfully to the system!")
        else:
            print("❌ Error creating the user")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 