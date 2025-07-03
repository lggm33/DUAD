#!/usr/bin/env python3
"""
Script to change automobile status in Lyfter Car Rental System
Usage: python change_automobile_status.py
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
        automobile_id = int(input("Enter Automobile ID: ").strip())
        return automobile_id
    except ValueError:
        print("❌ Invalid Automobile ID. Must be a number")
        return None

def get_new_status():
    """Get new status from input"""
    print("\nAvailable statuses:")
    print("1. Available")
    print("2. Rented")
    print("3. Maintenance")
    print("4. Retired")
    
    choice = input("Select new status (1-4): ").strip()
    
    status_map = {
        '1': 'available',
        '2': 'rented',
        '3': 'maintenance',
        '4': 'retired'
    }
    
    if choice in status_map:
        return status_map[choice]
    else:
        print("❌ Invalid choice. Please select 1-4")
        return None

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - CHANGE AUTOMOBILE STATUS")
    print("=" * 50)
    
    try:
        # Get automobile repository
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
        print(f"\n📋 Current Automobile Information:")
        print(f"ID: {automobile['id']}")
        print(f"Make: {automobile['make']}")
        print(f"Model: {automobile['model']}")
        print(f"Year: {automobile['year_manufactured']}")
        print(f"Condition: {automobile['condition']}")
        print(f"Current Status: {automobile['status'].title()}")
        
        # Get new status
        new_status = get_new_status()
        if new_status is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Check if status is already the same
        if automobile['status'] == new_status:
            print(f"ℹ️ Automobile is already {new_status.title()}")
            sys.exit(0)
        
        # Update automobile status
        updated_automobile = automobile_repo.update_automobile_status(automobile_id, new_status)
        
        if updated_automobile:
            print("\n✅ Automobile status updated successfully!")
            print("=" * 40)
            print(f"ID: {updated_automobile['id']}")
            print(f"Make: {updated_automobile['make']}")
            print(f"Model: {updated_automobile['model']}")
            print(f"New Status: {updated_automobile['status'].title()}")
            print(f"Updated: {updated_automobile['updated_at']}")
            print("\n🎉 Automobile status changed successfully!")
        else:
            print("❌ Error updating automobile status")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 