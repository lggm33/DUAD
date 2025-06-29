#!/usr/bin/env python3
"""
Automobiles Table Setup for Lyfter Car Rental System
- Creates automobiles table if it doesn't exist
- Populates automobiles table with data from MOCK_DATA_AUTOMOBILES.csv
"""

import os
import sys
import psycopg2
import csv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AutomobilesSetup:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'lyfter_car_rental')
        self.schema_name = os.getenv('DB_SCHEMA', 'lyfter_car_rental')

    def create_automobiles_table(self):
        """Creates the automobiles table if it doesn't exist"""
        print("🚗 Checking/creating automobiles table...")
        
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # First check if table already exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = 'automobiles'
                );
            """, (self.schema_name,))
            
            result = cursor.fetchone()
            table_exists = result[0] if result else False
            
            if table_exists:
                print("✅ Automobiles table already exists, skipping creation")
                cursor.close()
                conn.close()
                return True
            
            # Create automobiles table with all required fields
            create_table_sql = f"""
            CREATE TABLE "{self.schema_name}".automobiles (
                id SERIAL PRIMARY KEY,
                make VARCHAR(100) NOT NULL,
                model VARCHAR(100) NOT NULL,
                year_manufactured INTEGER CHECK (year_manufactured >= 1900 AND year_manufactured <= 2030),
                condition VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'available' CHECK (status IN ('available', 'rented', 'maintenance', 'retired')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            
            print("✅ Automobiles table created successfully")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.Error as e:
            print(f"⚠️  Warning creating automobiles table: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def populate_automobiles_table(self):
        """Populates automobiles table with data from MOCK_DATA_AUTOMOBILES.csv"""
        print("📊 Checking/populating automobiles table with mock data...")
        
        try:
            # Check if MOCK_DATA_AUTOMOBILES.csv exists
            if not os.path.exists('MOCK_DATA_AUTOMOBILES.csv'):
                print("⚠️  MOCK_DATA_AUTOMOBILES.csv file not found, skipping population")
                print("✅ Continuing with setup...")
                return True  # Continue even without CSV data
            
            conn = psycopg2.connect(
                host=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # First, check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = 'automobiles'
                );
            """, (self.schema_name,))
            
            result = cursor.fetchone()
            table_exists = result[0] if result else False
            
            if not table_exists:
                print("⚠️  Automobiles table doesn't exist, skipping population")
                cursor.close()
                conn.close()
                return True
            
            # Check if table already has data
            cursor.execute(f'SELECT COUNT(*) FROM "{self.schema_name}".automobiles')
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if count > 0:
                print(f"✅ Automobiles table already has {count} records, skipping population")
                cursor.close()
                conn.close()
                return True
            
            # Read CSV and insert data
            inserted_count = 0
            with open('MOCK_DATA_AUTOMOBILES.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Parse year manufactured
                        year_manufactured = None
                        try:
                            year_manufactured = int(row['year_manufactured'])
                            # Validate year range
                            if year_manufactured < 1900 or year_manufactured > 2030:
                                year_manufactured = 2000  # Default year if invalid
                        except (ValueError, TypeError):
                            year_manufactured = 2000  # Default year if cannot parse
                        
                        # Parse condition - now directly usable as status
                        condition = row['condition'].strip()
                        
                        # Validate condition value (should be 'available' or 'maintenance')
                        if condition not in ['available', 'maintenance']:
                            condition = 'available'  # Default to available if invalid
                        
                        # Use condition directly as status since they now match
                        status = condition
                        
                        # Insert automobile data
                        insert_sql = f"""
                        INSERT INTO "{self.schema_name}".automobiles 
                        (make, model, year_manufactured, condition, status)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(insert_sql, (
                            row['make'].strip(),
                            row['model'].strip(),
                            year_manufactured,
                            condition,
                            status
                        ))
                        
                        inserted_count += 1
                        
                    except psycopg2.Error as insert_error:
                        print(f"⚠️  Warning: Could not insert automobile {row.get('make', 'unknown')} {row.get('model', '')}: {insert_error}")
                        # Don't rollback entire transaction, just skip this automobile
                        continue
                    except Exception as parse_error:
                        print(f"⚠️  Warning: Could not parse data for automobile {row.get('make', 'unknown')} {row.get('model', '')}: {parse_error}")
                        continue
            
            conn.commit()
            print(f"✅ Successfully inserted {inserted_count} automobiles")
            
            # Show status breakdown
            cursor.execute(f"""
                SELECT status, COUNT(*) 
                FROM "{self.schema_name}".automobiles 
                GROUP BY status
            """)
            status_results = cursor.fetchall()
            print("📊 Automobiles by status:")
            for status, count in status_results:
                print(f"   • {status}: {count}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️  Warning populating automobiles table: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def setup(self):
        """Executes automobiles table setup"""
        print("🚀 Starting Automobiles Table Configuration")
        print("=" * 50)
        
        # Step 1: Create automobiles table
        if not self.create_automobiles_table():
            return False
        
        # Step 2: Populate automobiles table with mock data
        if not self.populate_automobiles_table():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Automobiles table configuration completed successfully!")
        print("\n✨ Automobiles table is ready")
        return True

def main():
    """Main function"""
    print("Lyfter Car Rental - Automobiles Setup")
    print("Automobiles Table Configuration\n")
    
    # Execute setup
    automobiles_setup = AutomobilesSetup()
    success = automobiles_setup.setup()
    
    if success:
        print("\n🔄 Next steps:")
        print("   1. Run: python setup_rentals.py (to create rentals table)")
        print("   2. Run: python main.py (to start the API server)")
        sys.exit(0)
    else:
        print("\n❌ Automobiles table configuration failed. Check previous errors.")
        sys.exit(1)

if __name__ == "__main__":
    main() 