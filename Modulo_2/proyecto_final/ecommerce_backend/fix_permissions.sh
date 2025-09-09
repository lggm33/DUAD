#!/bin/bash

# Permission fix script for existing ecommerce backend database
# This script only fixes permissions without recreating the database

set -e  # Exit on any error

# Configuration
DB_NAME="ecommerce_backend"
DB_USER="ecommerce_user"
DB_HOST="localhost"

echo "🔧 Fixing PostgreSQL permissions for ecommerce backend..."

# Grant schema privileges
echo "🔐 Granting schema privileges to $DB_USER..."
psql -U postgres -d "$DB_NAME" -c "GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"

# Verify connection and permissions
echo "✅ Testing connection and permissions..."
psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -c "SELECT current_user, current_database();" > /dev/null

echo ""
echo "🎉 Permissions fixed successfully!"
echo ""
echo "📝 Now you can run your Flask migrations:"
echo "  cd ecommerce_backend"
echo "  flask db migrate -m \"create users table\""
echo "  flask db upgrade"
echo ""
