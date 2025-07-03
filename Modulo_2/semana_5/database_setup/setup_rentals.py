#!/usr/bin/env python3
"""
Rentals Table Setup for Lyfter Car Rental System
- Creates rentals table if it doesn't exist (relationship between users and automobiles)
- Populates rentals table with some sample rental data
- Includes rental date (auto-generated) and rental status
"""

import os
import sys
import psycopg2
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .database_config import DatabaseConfig

# Load environment variables
load_dotenv()

class RentalsSetup(DatabaseConfig):
    def __init__(self):
        super().__init__()

    def create_rentals_table(self):
        """Creates the rentals table if it doesn't exist"""
        print("🚙 Checking/creating rentals table...")
        
        try:
            # Check if table already exists using inherited method
            if self.table_exists('rentals'):
                print("✅ Rentals table already exists, skipping creation")
                return True
            
            # Create rentals table with foreign keys and additional data using inherited methods
            create_table_sql = f"""
            CREATE TABLE {self.get_qualified_table_name('rentals')} (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                automobile_id INTEGER NOT NULL,
                rental_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_return_date DATE,
                actual_return_date TIMESTAMP NULL,
                rental_status VARCHAR(50) DEFAULT 'active' CHECK (rental_status IN ('active', 'completed', 'overdue', 'cancelled')),
                daily_rate DECIMAL(10,2),
                total_cost DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Foreign key constraints
                CONSTRAINT fk_rental_user 
                    FOREIGN KEY (user_id) 
                    REFERENCES {self.get_qualified_table_name('users')}(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT fk_rental_automobile 
                    FOREIGN KEY (automobile_id) 
                    REFERENCES {self.get_qualified_table_name('automobiles')}(id) 
                    ON DELETE CASCADE
            );
            """
            
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute(create_table_sql)
                    conn.commit()
                    
                    print("✅ Rentals table created successfully")
                    print("✅ Foreign key constraints added")
            
            return True
            
        except psycopg2.Error as e:
            return self.handle_setup_error(e, "creating rentals table")

    def populate_rentals_table(self):
        """Populates rentals table with sample rental data"""
        print("📊 Checking/populating rentals table with sample data...")
        
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # First, check if rentals table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = 'rentals'
                );
            """, (self.schema_name,))
            
            result = cursor.fetchone()
            table_exists = result[0] if result else False
            
            if not table_exists:
                print("⚠️  Rentals table doesn't exist, skipping population")
                cursor.close()
                conn.close()
                return True
            
            # Check if table already has data
            cursor.execute(f'SELECT COUNT(*) FROM "{self.schema_name}".rentals')
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if count > 0:
                print(f"✅ Rentals table already has {count} records, skipping population")
                cursor.close()
                conn.close()
                return True
            
            # Check if we have users and automobiles to create rentals
            cursor.execute(f'SELECT COUNT(*) FROM "{self.schema_name}".users WHERE account_state = true')
            users_result = cursor.fetchone()
            users_count = users_result[0] if users_result else 0
            
            cursor.execute(f'SELECT COUNT(*) FROM "{self.schema_name}".automobiles WHERE status = \'available\'')
            cars_result = cursor.fetchone()
            cars_count = cars_result[0] if cars_result else 0
            
            if users_count == 0 or cars_count == 0:
                print(f"⚠️  Not enough data to create rentals (users: {users_count}, available cars: {cars_count})")
                print("✅ Continuing with setup...")
                return True
            
            # Get available users and cars
            cursor.execute(f'SELECT id FROM "{self.schema_name}".users WHERE account_state = true LIMIT 20')
            user_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute(f'SELECT id FROM "{self.schema_name}".automobiles WHERE status = \'available\' LIMIT 15')
            car_ids = [row[0] for row in cursor.fetchall()]
            
            # Create sample rentals
            inserted_count = 0
            rental_statuses = ['active', 'completed', 'overdue']
            
            # Create a mix of rental scenarios
            for i in range(min(15, len(user_ids), len(car_ids))):
                try:
                    user_id = random.choice(user_ids)
                    car_id = car_ids[i]  # Use different car for each rental
                    
                    # Generate rental dates (mix of past, current, and future)
                    days_offset = random.randint(-30, 5)  # From 30 days ago to 5 days in future
                    rental_date = datetime.now() + timedelta(days=days_offset)
                    
                    # Expected return date (3-14 days from rental)
                    rental_duration = random.randint(3, 14)
                    expected_return_date = rental_date + timedelta(days=rental_duration)
                    
                    # Determine status based on dates
                    now = datetime.now()
                    if rental_date > now:
                        status = 'active'  # Future rental
                        actual_return_date = None
                    elif expected_return_date.date() < now.date():
                        # Past expected return date - could be completed or overdue
                        status = random.choice(['completed', 'overdue'])
                        if status == 'completed':
                            actual_return_date = expected_return_date + timedelta(days=random.randint(-1, 1))
                        else:
                            actual_return_date = None
                    else:
                        # Current active rental
                        status = 'active'
                        actual_return_date = None
                    
                    # Generate realistic daily rates ($30-150 per day)
                    daily_rate = round(random.uniform(30.00, 150.00), 2)
                    
                    # Calculate total cost
                    if status == 'completed' and actual_return_date:
                        actual_days = (actual_return_date - rental_date).days + 1
                        total_cost = round(daily_rate * actual_days, 2)
                    else:
                        expected_days = rental_duration
                        total_cost = round(daily_rate * expected_days, 2)
                    
                    # Insert rental data
                    insert_sql = f"""
                    INSERT INTO "{self.schema_name}".rentals 
                    (user_id, automobile_id, rental_date, expected_return_date, actual_return_date, 
                     rental_status, daily_rate, total_cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        user_id,
                        car_id,
                        rental_date,
                        expected_return_date.date(),
                        actual_return_date,
                        status,
                        daily_rate,
                        total_cost
                    ))
                    
                    # Update automobile status if rental is active
                    if status == 'active':
                        cursor.execute(f"""
                            UPDATE "{self.schema_name}".automobiles 
                            SET status = 'rented' 
                            WHERE id = %s
                        """, (car_id,))
                    
                    inserted_count += 1
                    
                except psycopg2.Error as insert_error:
                    print(f"⚠️  Warning: Could not insert rental for user {user_id}: {insert_error}")
                    continue
                except Exception as parse_error:
                    print(f"⚠️  Warning: Could not create rental data: {parse_error}")
                    continue
            
            conn.commit()
            print(f"✅ Successfully inserted {inserted_count} sample rentals")
            
            # Show status breakdown
            cursor.execute(f"""
                SELECT rental_status, COUNT(*) 
                FROM "{self.schema_name}".rentals 
                GROUP BY rental_status
            """)
            status_results = cursor.fetchall()
            print("📊 Rentals by status:")
            for status, count in status_results:
                print(f"   • {status}: {count}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"⚠️  Warning populating rentals table: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def setup(self):
        """Executes rentals table setup"""
        print("🚀 Starting Rentals Table Configuration")
        print("=" * 50)
        
        # Step 1: Create rentals table
        if not self.create_rentals_table():
            return False
        
        # Step 2: Populate rentals table with sample data
        if not self.populate_rentals_table():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Rentals table configuration completed successfully!")
        print("\n✨ Rentals table is ready")
        return True

def main():
    """Main function"""
    print("Lyfter Car Rental - Rentals Setup")
    print("Rentals Table Configuration\n")
    
    # Execute setup
    rentals_setup = RentalsSetup()
    success = rentals_setup.setup()
    
    if success:
        print("\n🔄 Next steps:")
        print("   1. Run: python main.py (to start the API server)")
        print("   2. Visit: http://localhost:8000/docs (to see API documentation)")
        print("   3. Test the endpoints with real data!")
        sys.exit(0)
    else:
        print("\n❌ Rentals table configuration failed. Check previous errors.")
        sys.exit(1)

if __name__ == "__main__":
    main() 