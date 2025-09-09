#!/bin/bash

# Database setup script for ecommerce backend
# This script creates database, user and shows connection URL

set -e  # Exit on any error

# Configuration
DB_NAME="ecommerce_backend"
DB_USER="ecommerce_user"
DB_PASSWORD="ecommerce_2024_secure"
DB_HOST="localhost"
DB_PORT="5432"

echo "🚀 Setting up PostgreSQL database for ecommerce backend..."

# Step 1: Create database
echo "📦 Creating database: $DB_NAME"
createdb "$DB_NAME" || echo "⚠️  Database might already exist"

# Step 2: Create user
echo "👤 Creating user: $DB_USER"
psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "⚠️  User might already exist"

# Step 3: Grant privileges
echo "🔐 Granting privileges to user..."
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
psql -U postgres -c "ALTER USER $DB_USER CREATEDB;" # Allow user to create test databases

# Grant schema privileges
echo "🔐 Granting schema privileges..."
psql -U postgres -d "$DB_NAME" -c "GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
psql -U postgres -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"

# Step 4: Verify connection
echo "✅ Testing connection..."
psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -c "SELECT version();" > /dev/null

# Step 5: Show connection details
echo ""
echo "🎉 Database setup completed successfully!"
echo ""
echo "📋 Connection Details:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo ""
echo "🔗 Database URL:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "📝 Add this to your .env file:"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "🧪 Test connection:"
echo "  psql -U $DB_USER -d $DB_NAME -h $DB_HOST"
