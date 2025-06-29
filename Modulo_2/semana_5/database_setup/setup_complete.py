#!/usr/bin/env python3
"""
Complete Setup for Lyfter Car Rental System
- Executes all setup scripts in the correct order
- Database -> Users -> Automobiles -> Rentals
"""

import sys
from .setup_database import DatabaseSetup
from .setup_users import UsersSetup
from .setup_automobiles import AutomobilesSetup
from .setup_rentals import RentalsSetup

def run_complete_setup():
    """
    Executes complete setup for API startup
    Returns True if successful, False otherwise
    """
    print("🚀 Setting up Lyfter Car Rental System...")
    
    # Step 1: Database and Schema Setup
    print("   🏗️  Setting up database and schema...")
    db_setup = DatabaseSetup()
    if not db_setup.setup():
        print("   ❌ Database setup failed!")
        return False
    
    # Step 2: Users Table Setup
    print("   👥 Setting up users table...")
    users_setup = UsersSetup()
    if not users_setup.setup():
        print("   ❌ Users table setup failed!")
        return False
    
    # Step 3: Automobiles Table Setup
    print("   🚗 Setting up automobiles table...")
    automobiles_setup = AutomobilesSetup()
    if not automobiles_setup.setup():
        print("   ❌ Automobiles table setup failed!")
        return False
    
    # Step 4: Rentals Table Setup
    print("   🚙 Setting up rentals table...")
    rentals_setup = RentalsSetup()
    if not rentals_setup.setup():
        print("   ❌ Rentals table setup failed!")
        return False
    
    print("   ✅ Complete setup finished successfully!")
    return True

def main():
    """Main function that executes complete setup"""
    print("🚀 LYFTER CAR RENTAL - COMPLETE SYSTEM SETUP")
    print("=" * 60)
    print("Setting up the entire car rental system...\n")
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Database and Schema Setup
    print("🏗️  STEP 1/4: Database and Schema Setup")
    print("-" * 40)
    db_setup = DatabaseSetup()
    if db_setup.setup():
        success_count += 1
        print("✅ Database setup completed successfully!\n")
    else:
        print("❌ Database setup failed!\n")
        sys.exit(1)
    
    # Step 2: Users Table Setup
    print("👥 STEP 2/4: Users Table Setup")
    print("-" * 40)
    users_setup = UsersSetup()
    if users_setup.setup():
        success_count += 1
        print("✅ Users table setup completed successfully!\n")
    else:
        print("❌ Users table setup failed!\n")
        sys.exit(1)
    
    # Step 3: Automobiles Table Setup
    print("🚗 STEP 3/4: Automobiles Table Setup")
    print("-" * 40)
    automobiles_setup = AutomobilesSetup()
    if automobiles_setup.setup():
        success_count += 1
        print("✅ Automobiles table setup completed successfully!\n")
    else:
        print("❌ Automobiles table setup failed!\n")
        sys.exit(1)
    
    # Step 4: Rentals Table Setup
    print("🚙 STEP 4/4: Rentals Table Setup")
    print("-" * 40)
    rentals_setup = RentalsSetup()
    if rentals_setup.setup():
        success_count += 1
        print("✅ Rentals table setup completed successfully!\n")
    else:
        print("❌ Rentals table setup failed!\n")
        sys.exit(1)
    
    # Final Summary
    print("=" * 60)
    print("🎉 COMPLETE SETUP FINISHED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✅ {success_count}/{total_steps} steps completed successfully")
    print("\n📊 System Components Ready:")
    print("   • PostgreSQL Database: lyfter_car_rental")
    print("   • Schema: lyfter_car_rental")
    print("   • Users Table: ✓ (with sample data)")
    print("   • Automobiles Table: ✓ (with sample data)")
    print("   • Rentals Table: ✓ (with sample relationships)")
    print("\n🔗 Foreign Key Relationships:")
    print("   • Rentals → Users (user_id)")
    print("   • Rentals → Automobiles (automobile_id)")
    print("\n🚀 NEXT STEPS:")
    print("   1. 🌐 Start API Server:")
    print("      python main.py")
    print("\n   2. 📋 View API Documentation:")
    print("      http://localhost:8000/docs")
    print("\n   3. 🧪 Test API Endpoints:")
    print("      http://localhost:8000/users")
    print("      http://localhost:8000/cars")
    print("      http://localhost:8000/rentals")
    print("\n✨ Your Lyfter Car Rental System is ready to use!")

if __name__ == "__main__":
    main() 