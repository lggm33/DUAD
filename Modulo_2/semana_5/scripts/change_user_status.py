#!/usr/bin/env python3
"""
Script to change user status in Lyfter Car Rental System
Usage: python change_user_status.py
"""

import sys
import os

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import UserRepository

def get_user_id():
    """Get user ID from input"""
    try:
        user_id = int(input("Enter User ID: ").strip())
        return user_id
    except ValueError:
        print("❌ Invalid User ID. Must be a number")
        return None

def get_new_status():
    """Get new status from input"""
    print("\nAvailable statuses:")
    print("1. Active")
    print("2. Inactive")
    
    choice = input("Select new status (1-2): ").strip()
    
    if choice == '1':
        return True
    elif choice == '2':
        return False
    else:
        print("❌ Invalid choice. Please select 1 or 2")
        return None

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - CHANGE USER STATUS")
    print("=" * 50)
    
    try:
        # Get user repository
        user_repo = UserRepository()
        
        # Get user ID
        user_id = get_user_id()
        if user_id is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Check if user exists
        user = user_repo.get_user_by_id(user_id)
        if not user:
            print(f"❌ User with ID {user_id} not found")
            sys.exit(1)
        
        # Show current user info
        print(f"\n📋 Current User Information:")
        print(f"ID: {user['id']}")
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Username: {user['username']}")
        print(f"Current Status: {'Active' if user['account_state'] else 'Inactive'}")
        
        # Get new status
        new_status = get_new_status()
        if new_status is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Check if status is already the same
        if user['account_state'] == new_status:
            status_text = 'Active' if new_status else 'Inactive'
            print(f"ℹ️ User is already {status_text}")
            sys.exit(0)
        
        # Update user status
        updated_user = user_repo.update_user_status(user_id, new_status)
        
        if updated_user:
            print("\n✅ User status updated successfully!")
            print("=" * 40)
            print(f"ID: {updated_user['id']}")
            print(f"Name: {updated_user['name']}")
            print(f"Email: {updated_user['email']}")
            print(f"Username: {updated_user['username']}")
            print(f"New Status: {'Active' if updated_user['account_state'] else 'Inactive'}")
            print(f"Updated: {updated_user['updated_at']}")
            print("\n🎉 User status changed successfully!")
        else:
            print("❌ Error updating user status")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 