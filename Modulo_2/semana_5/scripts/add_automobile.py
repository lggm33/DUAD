#!/usr/bin/env python3
"""
Script to add a new automobile to the Lyfter Car Rental System
Usage: python add_automobile.py
"""

import sys
import os

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import AutomobileRepository

def get_automobile_input():
    """Get automobile data from user input"""
    print("🚗 ADD NEW AUTOMOBILE")
    print("=" * 40)
    
    make = input("Make: ").strip()
    if not make:
        print("❌ Make is required")
        return None
    
    model = input("Model: ").strip()
    if not model:
        print("❌ Model is required")
        return None
    
    year_input = input("Year of manufacture: ").strip()
    if not year_input:
        print("❌ Year of manufacture is required")
        return None
    
    try:
        year_manufactured = int(year_input)
        if year_manufactured < 1900 or year_manufactured > 2030:
            print("❌ Invalid year. Must be between 1900 and 2030")
            return None
    except ValueError:
        print("❌ Invalid year. Must be a number")
        return None
    
    condition = input("Condition (available/maintenance) [available]: ").strip().lower()
    if not condition:
        condition = 'available'
    
    if condition not in ['available', 'maintenance']:
        print("❌ Invalid condition. Use 'available' or 'maintenance'")
        return None
    
    status = input("Status (available/rented/maintenance/retired) [available]: ").strip().lower()
    if not status:
        status = 'available'
    
    if status not in ['available', 'rented', 'maintenance', 'retired']:
        print("❌ Invalid status. Use 'available', 'rented', 'maintenance' or 'retired'")
        return None
    
    return {
        'make': make,
        'model': model,
        'year_manufactured': year_manufactured,
        'condition': condition,
        'status': status
    }

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - ADD AUTOMOBILE")
    print("=" * 50)
    
    # Get automobile data from user input
    automobile_data = get_automobile_input()
    if not automobile_data:
        print("❌ Operation cancelled")
        sys.exit(1)
    
    try:
        # Create repository
        automobile_repo = AutomobileRepository()
        
        # Create automobile
        new_automobile = automobile_repo.create_automobile(automobile_data)
        
        if new_automobile:
            print("\n✅ Automobile created successfully!")
            print("=" * 40)
            print(f"ID: {new_automobile['id']}")
            print(f"Make: {new_automobile['make']}")
            print(f"Model: {new_automobile['model']}")
            print(f"Year: {new_automobile['year_manufactured']}")
            print(f"Condition: {new_automobile['condition']}")
            print(f"Status: {new_automobile['status']}")
            print(f"Created: {new_automobile['created_at']}")
            print("\n🎉 ¡Automobile added successfully to the system!")
        else:
            print("❌ Error creating the automobile")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 