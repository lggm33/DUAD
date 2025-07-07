#!/usr/bin/env python3
"""
Script to get all available automobiles in Lyfter Car Rental System
Usage: python get_available_automobiles.py
"""

import sys
import os

# Add parent directory to Python path to import repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from repositories import AutomobileRepository

def display_automobiles(automobiles, title):
    """Display automobiles in a formatted table"""
    print(f"\n{title}")
    print("=" * 80)
    
    if not automobiles:
        print("No automobiles found.")
        return
    
    print(f"{'ID':<5} {'Make':<15} {'Model':<20} {'Year':<6} {'Condition':<12} {'Status':<12}")
    print("-" * 80)
    
    for auto in automobiles:
        print(f"{auto['id']:<5} {auto['make']:<15} {auto['model']:<20} "
              f"{auto['year_manufactured']:<6} {auto['condition']:<12} {auto['status'].title():<12}")

def main():
    """Main function"""
    print("🚀 LYFTER CAR RENTAL - AVAILABLE AUTOMOBILES")
    print("=" * 50)
    
    try:
        # Initialize automobile repository
        automobile_repo = AutomobileRepository()
        
        # Get available automobiles
        available_automobiles = automobile_repo.get_available_automobiles()
        
        # Display results
        display_automobiles(available_automobiles, "📋 AVAILABLE AUTOMOBILES")
        
        # Show summary statistics
        total_available = len(available_automobiles)
        print(f"\n📊 Summary:")
        print(f"Total available automobiles: {total_available}")
        
        if total_available > 0:
            # Group by make
            makes = {}
            for auto in available_automobiles:
                make = auto['make']
                if make not in makes:
                    makes[make] = 0
                makes[make] += 1
            
            print(f"\n🏷️ Available by Make:")
            for make, count in sorted(makes.items()):
                print(f"   • {make}: {count}")
        
        # Show overall statistics
        stats = automobile_repo.get_automobile_stats()
        if stats:
            print(f"\n📈 Overall Fleet Statistics:")
            print(f"   • Total automobiles: {stats['total_automobiles']}")
            print(f"   • Available: {stats['available_count']}")
            print(f"   • Rented: {stats['rented_count']}")
            print(f"   • In maintenance: {stats['maintenance_count']}")
            print(f"   • Retired: {stats['retired_count']}")
            print(f"   • Availability rate: {(stats['available_count'] / stats['total_automobiles'] * 100):.1f}%")
        
        print("\n✅ Available automobiles retrieved successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 