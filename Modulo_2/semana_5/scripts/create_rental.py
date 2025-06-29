#!/usr/bin/env python3
"""
Script to create a new rental in Lyfter Car Rental System
Usage: python create_rental.py
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import UserRepository, AutomobileRepository, RentalRepository

def get_user_id():
    """Get and validate user ID"""
    try:
        user_id = int(input("Enter User ID: ").strip())
        return user_id
    except ValueError:
        print("❌ Invalid User ID. Must be a number")
        return None

def get_automobile_id():
    """Get and validate automobile ID"""
    try:
        automobile_id = int(input("Enter Automobile ID: ").strip())
        return automobile_id
    except ValueError:
        print("❌ Invalid Automobile ID. Must be a number")
        return None

def get_rental_details():
    """Get rental duration and daily rate"""
    try:
        days = int(input("Rental duration (days): ").strip())
        if days <= 0:
            print("❌ Duration must be greater than 0")
            return None, None
        
        daily_rate = float(input("Daily rate ($): ").strip())
        if daily_rate <= 0:
            print("❌ Daily rate must be greater than 0")
            return None, None
        
        return days, daily_rate
    except ValueError:
        print("❌ Invalid input. Please enter valid numbers")
        return None, None

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - CREATE NEW RENTAL")
    print("=" * 50)
    
    try:
        # Initialize repositories
        user_repo = UserRepository()
        automobile_repo = AutomobileRepository()
        rental_repo = RentalRepository()
        
        # Get user ID and validate
        user_id = get_user_id()
        if user_id is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        user = user_repo.get_user_by_id(user_id)
        if not user:
            print(f"❌ User with ID {user_id} not found")
            sys.exit(1)
        
        if not user['account_state']:
            print(f"❌ User account is inactive. Cannot create rental")
            sys.exit(1)
        
        # Get automobile ID and validate
        automobile_id = get_automobile_id()
        if automobile_id is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        automobile = automobile_repo.get_automobile_by_id(automobile_id)
        if not automobile:
            print(f"❌ Automobile with ID {automobile_id} not found")
            sys.exit(1)
        
        if automobile['status'] != 'available':
            print(f"❌ Automobile is not available (current status: {automobile['status']})")
            sys.exit(1)
        
        # Show details
        print(f"\n📋 Rental Details:")
        print(f"User: {user['name']} ({user['email']})")
        print(f"Automobile: {automobile['make']} {automobile['model']} ({automobile['year_manufactured']})")
        
        # Get rental details
        days, daily_rate = get_rental_details()
        if days is None or daily_rate is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Calculate dates and cost
        today = date.today()
        expected_return_date = today + timedelta(days=days)
        total_cost = daily_rate * days
        
        print(f"\n💰 Cost Calculation:")
        print(f"Daily rate: ${daily_rate:.2f}")
        print(f"Duration: {days} days")
        print(f"Total cost: ${total_cost:.2f}")
        print(f"Expected return date: {expected_return_date}")
        
        # Confirm creation
        confirm = input(f"\nConfirm rental creation? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Create rental data
        rental_data = {
            'user_id': user_id,
            'automobile_id': automobile_id,
            'expected_return_date': expected_return_date,
            'daily_rate': daily_rate,
            'total_cost': total_cost
        }
        
        # Create rental
        new_rental = rental_repo.create_rental(rental_data)
        if not new_rental:
            print("❌ Error creating rental")
            sys.exit(1)
        
        # Update automobile status to rented
        automobile_repo.update_automobile_status(automobile_id, 'rented')
        
        print("\n✅ Rental created successfully!")
        print("=" * 40)
        print(f"Rental ID: {new_rental['id']}")
        print(f"User: {user['name']}")
        print(f"Automobile: {automobile['make']} {automobile['model']}")
        print(f"Rental Date: {new_rental['rental_date']}")
        print(f"Expected Return: {new_rental['expected_return_date']}")
        print(f"Daily Rate: ${new_rental['daily_rate']:.2f}")
        print(f"Total Cost: ${new_rental['total_cost']:.2f}")
        print(f"Status: {new_rental['rental_status'].title()}")
        print("\n🎉 Rental created successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 