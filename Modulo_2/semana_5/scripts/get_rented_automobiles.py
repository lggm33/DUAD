#!/usr/bin/env python3
"""
Script to get all rented automobiles in Lyfter Car Rental System
Usage: python get_rented_automobiles.py
"""

import sys
import os

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import AutomobileRepository, RentalRepository

def display_rented_automobiles(automobiles, rentals):
    """Display rented automobiles with rental details"""
    print(f"\n📋 RENTED AUTOMOBILES")
    print("=" * 100)
    
    if not automobiles:
        print("No rented automobiles found.")
        return
    
    # Create rental lookup dictionary
    rental_lookup = {}
    for rental in rentals:
        if rental['rental_status'] == 'active':
            rental_lookup[rental['automobile_id']] = rental
    
    print(f"{'ID':<5} {'Make':<12} {'Model':<15} {'Year':<6} {'Renter':<20} {'Rental Date':<12} {'Return Due':<12}")
    print("-" * 100)
    
    for auto in automobiles:
        rental = rental_lookup.get(auto['id'], {})
        renter_name = rental.get('user_name', 'Unknown')
        rental_date = str(rental.get('rental_date', 'Unknown'))[:10] if rental.get('rental_date') else 'Unknown'
        return_due = str(rental.get('expected_return_date', 'Unknown'))
        
        print(f"{auto['id']:<5} {auto['make']:<12} {auto['model']:<15} "
              f"{auto['year_manufactured']:<6} {renter_name:<20} {rental_date:<12} {return_due:<12}")

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - RENTED AUTOMOBILES")
    print("=" * 50)
    
    try:
        # Initialize repositories
        automobile_repo = AutomobileRepository()
        rental_repo = RentalRepository()
        
        # Get rented automobiles
        rented_automobiles = automobile_repo.get_rented_automobiles()
        
        # Get active rentals for additional details
        active_rentals = rental_repo.get_active_rentals()
        
        # Display results
        display_rented_automobiles(rented_automobiles, active_rentals)
        
        # Show summary statistics
        total_rented = len(rented_automobiles)
        print(f"\n📊 Summary:")
        print(f"Total rented automobiles: {total_rented}")
        
        if total_rented > 0:
            # Group by make
            makes = {}
            for auto in rented_automobiles:
                make = auto['make']
                if make not in makes:
                    makes[make] = 0
                makes[make] += 1
            
            print(f"\n🏷️ Rented by Make:")
            for make, count in sorted(makes.items()):
                print(f"   • {make}: {count}")
            
            # Calculate daily revenue from active rentals
            total_daily_revenue = sum(rental.get('daily_rate', 0) for rental in active_rentals)
            print(f"\n💰 Revenue Information:")
            print(f"   • Daily revenue from active rentals: ${total_daily_revenue:.2f}")
            
            # Show overdue rentals
            overdue_rentals = rental_repo.get_overdue_rentals()
            if overdue_rentals:
                print(f"   • ⚠️ Overdue rentals: {len(overdue_rentals)}")
        
        # Show overall statistics
        stats = automobile_repo.get_automobile_stats()
        if stats:
            print(f"\n📈 Overall Fleet Statistics:")
            print(f"   • Total automobiles: {stats['total_automobiles']}")
            print(f"   • Available: {stats['available_count']}")
            print(f"   • Rented: {stats['rented_count']}")
            print(f"   • In maintenance: {stats['maintenance_count']}")
            print(f"   • Retired: {stats['retired_count']}")
            print(f"   • Utilization rate: {(stats['rented_count'] / stats['total_automobiles'] * 100):.1f}%")
        
        print("\n✅ Rented automobiles retrieved successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()