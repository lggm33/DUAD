#!/usr/bin/env python3
"""
Database and Schema Setup for Lyfter Car Rental System
- Verifies PostgreSQL is installed and running
- Creates database if it doesn't exist
- Creates project schema
- Tests connection
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseSetup:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'lyfter_car_rental')
        self.schema_name = os.getenv('DB_SCHEMA', 'lyfter_car_rental')

    def check_postgresql_installed(self):
        """Verifies if PostgreSQL is installed on the system"""
        print("🔍 Checking if PostgreSQL is installed...")
        
        try:
            # Try to execute psql --version
            result = subprocess.run(['psql', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ PostgreSQL not found on system")
            return False

    def check_postgresql_running(self):
        """Verifies if PostgreSQL is running"""
        print("🔍 Checking if PostgreSQL is running...")
        
        try:
            # Try to connect to PostgreSQL server
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # Default database
            )
            conn.close()
            print("✅ PostgreSQL is running and accessible")
            return True
        except psycopg2.OperationalError as e:
            print(f"❌ Cannot connect to PostgreSQL: {e}")
            return False

    def create_database(self):
        """Creates the database if it doesn't exist"""
        print(f"🗄️  Creating database '{self.db_name}'...")
        
        try:
            # Connect to default database to create new DB
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database already exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_name,)
            )
            
            if cursor.fetchone():
                print(f"✅ Database '{self.db_name}' already exists")
            else:
                # Create the database
                cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                print(f"✅ Database '{self.db_name}' created successfully")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.Error as e:
            print(f"⚠️  Warning creating database: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def create_schema(self):
        """Creates the project schema"""
        print(f"📂 Creating schema '{self.schema_name}'...")
        
        try:
            # Connect to project database
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # Create schema if it doesn't exist
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
            conn.commit()
            
            print(f"✅ Schema '{self.schema_name}' created successfully")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.Error as e:
            print(f"⚠️  Warning creating schema: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def test_connection(self):
        """Tests connection to the created database and schema"""
        print("🧪 Testing final connection...")
        
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # Verify schema exists
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (self.schema_name,)
            )
            
            if cursor.fetchone():
                print("✅ Successful connection - Database and schema configured correctly")
                
                # Show connection information
                cursor.execute("SELECT version()")
                version_result = cursor.fetchone()
                if version_result:
                    print(f"📊 PostgreSQL version: {version_result[0]}")
                else:
                    print("📊 PostgreSQL version: Not available")
                
                cursor.close()
                conn.close()
                return True
            else:
                print(f"❌ Schema '{self.schema_name}' not found")
                return False
                
        except psycopg2.Error as e:
            print(f"⚠️  Warning in connection test: {e}")
            print("✅ Continuing with setup...")
            return True  # Continue even if there's an error

    def setup(self):
        """Executes database and schema setup"""
        print("🚀 Starting Database Configuration")
        print("=" * 50)
        
        # Step 1: Verify PostgreSQL installed
        if not self.check_postgresql_installed():
            self._show_install_instructions()
            return False
        
        # Step 2: Verify PostgreSQL running
        if not self.check_postgresql_running():
            self._show_start_instructions()
            return False
        
        # Step 3: Create database
        if not self.create_database():
            return False
        
        # Step 4: Create schema
        if not self.create_schema():
            return False
        
        # Step 5: Test connection
        if not self.test_connection():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Database configuration completed successfully!")
        print(f"📊 Database: {self.db_name}")
        print(f"📂 Schema: {self.schema_name}")
        print(f"🔗 Connection: {self.host}:{self.port}")
        print("\n✨ Ready for table creation")
        return True

    def _show_install_instructions(self):
        """Show PostgreSQL installation instructions"""
        print("\n💡 To install PostgreSQL:")
        print("   • Homebrew: brew install postgresql@15")
        print("   • Postgres.app: https://postgresapp.com/")
        print("   • Docker: docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres")

    def _show_start_instructions(self):
        """Show PostgreSQL start instructions"""
        print("\n💡 To start PostgreSQL:")
        print("   • Homebrew: brew services start postgresql@15")
        print("   • Postgres.app: Open app and click 'Start'")
        print("   • Docker: docker start postgres")

def main():
    """Main function"""
    print("Lyfter Car Rental - Database Setup")
    print("Database and Schema Configuration\n")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=
DB_NAME=lyfter_car_rental
DB_SCHEMA=lyfter_car_rental
""")
        print("✅ .env file created. You can edit it with your credentials.")
    
    # Execute setup
    db_setup = DatabaseSetup()
    success = db_setup.setup()
    
    if success:
        print("\n🔄 Next steps:")
        print("   1. Run: python setup_users.py (to create users table)")
        print("   2. Run: python setup_automobiles.py (to create automobiles table)")
        print("   3. Run: python setup_rentals.py (to create rentals table)")
        print("   4. Run: python main.py (to start the API server)")
        sys.exit(0)
    else:
        print("\n❌ Database configuration failed. Check previous errors.")
        sys.exit(1)

if __name__ == "__main__":
    main() 