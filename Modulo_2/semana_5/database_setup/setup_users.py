#!/usr/bin/env python3
"""
Users Table Setup for Lyfter Car Rental System
- Creates users table if it doesn't exist
- Populates users table with data from MOCK_DATA_USERS.csv
"""

import os
import sys
import psycopg2
import csv
import random
from datetime import datetime
from dotenv import load_dotenv
from .database_config import DatabaseConfig

# Load environment variables
load_dotenv()

class UsersSetup(DatabaseConfig):
    def __init__(self):
        super().__init__()

    def create_users_table(self):
        """Creates the users table if it doesn't exist"""
        print("👥 Checking/creating users table...")
        
        try:
            # Check if table already exists using inherited method
            if self.table_exists('users'):
                print("✅ Users table already exists, skipping creation")
                return True
            
            # Create users table with all required fields
            create_table_sql = f"""
            CREATE TABLE {self.get_qualified_table_name('users')} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                date_of_birth DATE,
                account_state BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute(create_table_sql)
                    conn.commit()
                    
                    print("✅ Users table created successfully")
            
            return True
            
        except psycopg2.Error as e:
            return self.handle_setup_error(e, "creating users table")

    def populate_users_table(self):
        """Populates users table with data from MOCK_DATA_USERS.csv"""
        print("📊 Checking/populating users table with mock data...")
        
        try:
            # Check if MOCK_DATA_USERS.csv exists
            if not os.path.exists('MOCK_DATA_USERS.csv'):
                print("⚠️  MOCK_DATA_USERS.csv file not found, skipping population")
                print("✅ Continuing with setup...")
                return True  # Continue even without CSV data
            
            # Check if table exists using inherited method
            if not self.table_exists('users'):
                print("⚠️  Users table doesn't exist, skipping population")
                return True
            
            # Check if table already has data using inherited method
            count = self.count_table_records('users')
            if count > 0:
                print(f"✅ Users table already has {count} records, skipping population")
                return True
            
            # Read CSV and insert data using inherited methods
            inserted_count = 0
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    with open('MOCK_DATA_USERS.csv', 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        
                        for row in reader:
                            try:
                                # Parse date of birth - Generate random dates between 1960-2000 for demo purposes
                                date_of_birth = None
                                try:
                                    # Generate a random date between 1960 and 2000
                                    year = random.randint(1960, 2000)
                                    month = random.randint(1, 12)
                                    day = random.randint(1, 28)  # Use 28 to avoid month length issues
                                    date_of_birth = datetime(year, month, day).date()
                                except Exception:
                                    date_of_birth = None
                                
                                # Parse account state
                                account_state = row['account_state'].lower() == 'true'
                                
                                # Insert user data using qualified table name
                                insert_sql = f"""
                                INSERT INTO {self.get_qualified_table_name('users')} 
                                (name, email, username, password, date_of_birth, account_state)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """
                                
                                cursor.execute(insert_sql, (
                                    row['name'],
                                    row['email'],
                                    row['user_name'],
                                    row['password'],
                                    date_of_birth,
                                    account_state
                                ))
                                
                                inserted_count += 1
                                
                            except psycopg2.Error as insert_error:
                                print(f"⚠️  Warning: Could not insert user {row.get('user_name', 'unknown')}: {insert_error}")
                                # Don't rollback entire transaction, just skip this user
                                continue
                            except Exception as parse_error:
                                print(f"⚠️  Warning: Could not parse data for user {row.get('user_name', 'unknown')}: {parse_error}")
                                continue
                    
                    conn.commit()
                    print(f"✅ Successfully inserted {inserted_count} users")
            
            return True
            
        except Exception as e:
            return self.handle_setup_error(e, "populating users table")

    def setup(self):
        """Executes users table setup"""
        print("🚀 Starting Users Table Configuration")
        print("=" * 50)
        
        # Step 1: Create users table
        if not self.create_users_table():
            return False
        
        # Step 2: Populate users table with mock data
        if not self.populate_users_table():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Users table configuration completed successfully!")
        print("\n✨ Users table is ready")
        return True

def main():
    """Main function"""
    print("Lyfter Car Rental - Users Setup")
    print("Users Table Configuration\n")
    
    # Execute setup
    users_setup = UsersSetup()
    success = users_setup.setup()
    
    if success:
        print("\n🔄 Next steps:")
        print("   1. Run: python setup_automobiles.py (to create automobiles table)")
        print("   2. Run: python setup_rentals.py (to create rentals table)")
        print("   3. Run: python main.py (to start the API server)")
        sys.exit(0)
    else:
        print("\n❌ Users table configuration failed. Check previous errors.")
        sys.exit(1)

if __name__ == "__main__":
    main() 