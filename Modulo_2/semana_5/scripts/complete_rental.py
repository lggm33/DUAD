#!/usr/bin/env python3
"""
Script to complete rental (car return) in Lyfter Car Rental System
Usage: python complete_rental.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import RentalRepository

def get_rental_id():
    """Get rental ID from input"""
    try:
        rental_id = int(input("Enter Rental ID: ").strip())
        return rental_id
    except ValueError:
        print("❌ Invalid Rental ID. Must be a number")
        return None

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - COMPLETE RENTAL")
    print("=" * 50)
    
    try:
        # Initialize rental repository
        rental_repo = RentalRepository()
        
        # Get rental ID
        rental_id = get_rental_id()
        if rental_id is None:
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Check if rental exists
        rental = rental_repo.get_rental_by_id(rental_id)
        if not rental:
            print(f"❌ Rental with ID {rental_id} not found")
            sys.exit(1)
        
        # Check if rental can be completed
        if rental['rental_status'] not in ['active', 'overdue']:
            print(f"❌ Rental cannot be completed (current status: {rental['rental_status']})")
            sys.exit(1)
        
        # Show rental details
        print(f"\n📋 Rental Information:")
        print(f"Rental ID: {rental['id']}")
        print(f"User: {rental['user_name']} ({rental['user_email']})")
        print(f"Automobile: {rental['automobile_make']} {rental['automobile_model']} ({rental['automobile_year']})")
        print(f"Rental Date: {rental['rental_date']}")
        print(f"Expected Return: {rental['expected_return_date']}")
        print(f"Current Status: {rental['rental_status'].title()}")
        print(f"Daily Rate: ${rental['daily_rate']:.2f}")
        print(f"Total Cost: ${rental['total_cost']:.2f}")
        
        # Check if overdue
        if rental['rental_status'] == 'overdue':
            print("\n⚠️ WARNING: This rental is overdue!")
        
        # Confirm completion
        confirm = input(f"\nConfirm rental completion (car return)? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            sys.exit(1)
        
        # Complete rental
        completed_rental = rental_repo.complete_rental(rental_id)
        
        if completed_rental:
            print("\n✅ Rental completed successfully!")
            print("=" * 40)
            print(f"Rental ID: {completed_rental['id']}")
            print(f"Status: Completed")
            print(f"Return Date: {completed_rental['actual_return_date']}")
            print("\n🎉 Car has been returned and is now available for rental!")
            print("🚗 Automobile status updated to: Available")
        else:
            print("❌ Error completing rental")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 