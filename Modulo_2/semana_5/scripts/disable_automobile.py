#!/usr/bin/env python3
"""
Script to disable automobile from rental in Lyfter Car Rental System
Usage: python disable_automobile.py
"""

import sys
import os

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import AutomobileRepository

def get_automobile_id():
    """Get automobile ID from input"""
    try:
        automobile_id = int(input("Enter Automobile ID to disable: ").strip())
        return automobile_id
    except ValueError:
        print("❌ Invalid Automobile ID. Must be a number")
        return None

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - DISABLE AUTOMOBILE")
    print("=" * 50)
    
    try:
        # Initialize automobile repository
        automobile_repo = AutomobileRepository()
        
        # Get automobile ID
        automobile_id = get_automobile_id()
        if automobile_id is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Check if automobile exists
        automobile = automobile_repo.get_automobile_by_id(automobile_id)
        if not automobile:
            print(f"❌ Automobile with ID {automobile_id} not found")
            sys.exit(1)
        
        # Show current automobile info
        print(f"\n📋 Automobile Information:")
        print(f"ID: {automobile['id']}")
        print(f"Make: {automobile['make']}")
        print(f"Model: {automobile['model']}")
        print(f"Year: {automobile['year_manufactured']}")
        print(f"Condition: {automobile['condition']}")
        print(f"Current Status: {automobile['status'].title()}")
        
        # Check if already retired
        if automobile['status'] == 'retired':
            print(f"ℹ️ Automobile is already disabled (retired)")
            sys.exit(0)
        
        # Warning if currently rented
        if automobile['status'] == 'rented':
            print("\n⚠️ WARNING: This automobile is currently rented!")
            print("Disabling it will not affect active rentals, but it will be unavailable for new rentals.")
        
        # Confirm disabling
        confirm = input(f"\nConfirm disabling automobile from rental? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Disable automobile (set status to retired)
        disabled_automobile = automobile_repo.disable_automobile(automobile_id)
        
        if disabled_automobile:
            print("\n✅ Automobile disabled successfully!")
            print("=" * 40)
            print(f"ID: {disabled_automobile['id']}")
            print(f"Make: {disabled_automobile['make']}")
            print(f"Model: {disabled_automobile['model']}")
            print(f"Status: {disabled_automobile['status'].title()}")
            print(f"Updated: {disabled_automobile['updated_at']}")
            print("\n🚫 Automobile is now disabled and unavailable for rental!")
        else:
            print("❌ Error disabling automobile")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 