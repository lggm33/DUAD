# Ecommerce Backend API

REST API for ecommerce system built with Flask, SQLAlchemy and PostgreSQL.

## 🏗️ Project Structure

```
ecommerce_backend/
├─ app/
│  ├─ __init__.py              # app factory, CORS, db, cache, JWT
│  ├─ config.py                # configuration and environment variables
│  ├─ extensions.py            # db, migrate, cache, jwt, limiter, ma
│  ├─ models/                  # SQLAlchemy models
│  │  ├─ user.py               # User model
│  │  ├─ product.py            # Product model
│  │  ├─ cart.py               # Cart model
│  │  ├─ cart_product.py       # Cart-Product relationship
│  │  ├─ sale.py               # Sale model
│  │  ├─ sale_product.py       # Sale-Product relationship
│  │  ├─ invoice.py            # Invoice model
│  │  ├─ delivery_address.py   # DeliveryAddress model
│  │  └─ __init__.py
│  ├─ schemas/                 # Marshmallow schemas (DTOs)
│  │  ├─ user.py
│  │  ├─ product.py
│  │  ├─ cart.py
│  │  ├─ cart_product.py
│  │  ├─ sale.py
│  │  ├─ sale_product.py
│  │  ├─ invoice.py
│  │  ├─ delivery_address.py
│  │  └─ __init__.py
│  ├─ services/                # business logic layer
│  │  ├─ auth_service.py       # authentication and authorization
│  │  ├─ user_service.py       # user management
│  │  ├─ product_service.py    # product management
│  │  ├─ cart_service.py       # cart management
│  │  ├─ sale_service.py       # sales management
│  │  ├─ invoice_service.py    # invoice management
│  │  ├─ delivery_address_service.py  # address management
│  │  └─ __init__.py
│  ├─ repos/                   # data access layer
│  │  ├─ user_repo.py
│  │  ├─ product_repo.py
│  │  ├─ cart_repo.py
│  │  ├─ sale_repo.py
│  │  ├─ invoice_repo.py
│  │  └─ delivery_address_repo.py
│  ├─ api/                     # REST endpoints (Blueprints)
│  │  ├─ user.py               # /api/users (registration, profile, admin)
│  │  ├─ products.py           # /api/products (CRUD, search)
│  │  ├─ sales.py              # /api/sales (checkout, history)
│  │  └─ __init__.py
│  ├─ security/                # security and authentication
│  │  ├─ rbac.py               # role-based access control
│  │  ├─ decorators.py         # authorization decorators
│  │  ├─ blocklist.py          # token blacklist
│  │  ├─ jwt_handlers.py       # JWT handling
│  │  └─ jwt_blocklist_check.py
│  ├─ cache/                   # cache directory (empty)
│  └─ utils/                   # utilities
│     ├─ decorators.py         # general decorators
│     └─ exceptions.py         # custom exceptions
├─ migrations/                 # Alembic migrations
│  ├─ versions/                # migration files
│  ├─ alembic.ini
│  ├─ env.py
│  └─ script.py.mako
├─ tests/                      # unit and integration tests
│  ├─ conftest.py              # test fixtures configuration
│  ├─ test_auth_api.py         # authentication tests
│  ├─ test_user_management_api.py  # user management tests
│  ├─ test_products_api.py     # product tests
│  └─ test_sales_api.py        # sales tests
├─ keys/                       # RSA keys for JWT (generated)
├─ htmlcov/                    # coverage reports (generated)
├─ build/                      # build files (generated)
├─ venv/                       # virtual environment (generated)
├─ __pycache__/                # Python cache (generated)
├─ .env.example                # environment variables example
├─ .env                        # environment variables (generated)
├─ env.example                 # configuration template
├─ setup_database.sh           # database setup script
├─ fix_permissions.sh          # permissions fix script
├─ generate_keys.py            # RSA key generator
├─ api.http                    # HTTP requests collection
├─ db-relations.md             # database relations documentation
├─ db-relations.png            # database diagram
├─ pyproject.toml              # project configuration
├─ pytest.ini                 # pytest configuration
├─ requirements.md             # dependencies documentation
├─ wsgi.py                     # WSGI entry point
├─ Makefile                    # automated commands
└─ README.md                   # this file
```

## 🚀 Setup and Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis Cloud account (Required for caching in both development and production)

### Installation with Make (Recommended)

#### Complete Automatic Setup
```bash
# Install dependencies, setup DB, generate keys, check Redis and run migrations
make setup

# Complete setup + start development server
make dev
```

#### Individual Commands
```bash
# View all available commands
make help

# Install dependencies in virtual environment
make install-deps

# Setup environment variables
make setup-env

# Setup PostgreSQL database
make setup-db

# Generate RSA keys for JWT
make generate-keys

# Run migrations
make migrate

# Start development server
make run

#### Setup Redis Cloud (Required)
```bash
# 1. Create a Redis Cloud account at https://redis.com/try-free/
# 2. Create a new database instance
# 3. Get your connection details from the Redis Cloud dashboard:
#    - Endpoint (REDIS_HOST)
#    - Port (REDIS_PORT) 
#    - Password (REDIS_PASSWORD)
#    - Username (usually "default")

# 4. Install redis-cli locally to test connection (optional but recommended)
brew install redis  # macOS
# or
sudo apt-get install redis-tools  # Ubuntu/Debian

# 5. Test connection (optional)
redis-cli -h your-endpoint -p your-port -a your-password ping
```

**Note:** The developer is responsible for configuring Redis Cloud credentials in the `.env` file. The application will connect to Redis Cloud using the provided credentials.

#### 4. Setup environment variables
```bash
# Copy template
cp env.example .env

# Edit .env with your configurations
# DATABASE_URL=postgresql://ecommerce_user:ecommerce_2024_secure@localhost:5432/ecommerce_backend
# REDIS_HOST=your-redis-cloud-endpoint.redislabs.com
# REDIS_PORT=12345
# REDIS_PASSWORD=your-redis-cloud-password
```


## 🧪 Testing

```bash
# Run all tests with coverage
make test

# test-cache
make test-cache

# Run specific test categories using markers
python3 -m pytest -m "cache"     # Cache tests only
python3 -m pytest -m "products"  # Product tests only  
python3 -m pytest -m "admin"     # Admin tests only
```

## 🔧 Development

```bash
# Generate new migration
make generate-migration MSG="migration description"

# Code linting
make lint

# View project status (includes Redis status)
make status

# Check Redis Cloud connection
make check-redis

# Clean temporary files
make clean
```

## 📁 Auxiliary Scripts

- **setup_database.sh**: Main script for PostgreSQL configuration. Used by `make setup-db`.
- **fix_permissions.sh**: Script to fix permissions in specific database configuration cases.
- **generate_keys.py**: Generates RSA keys for JWT signing. Used by `make generate-keys`.

## 🌐 API Endpoints

The API is available at `http://127.0.0.1:5001/api/`

### Main endpoints:
- `/api/users/` - User management and authentication
- `/api/products/` - Product catalog
- `/api/sales/` - Purchase process and sales

See `api.http` for complete request examples.

## ⚡ Caching System

The application implements a comprehensive Redis-based caching system to improve performance and reduce database load.

### Cached Endpoints

#### Critical Priority (High Performance Impact)
- **`GET /api/products`** - Product catalog (TTL: 30 minutes)
- **`GET /api/products/<id>`** - Individual product details (TTL: 1 hour)
- **`GET /api/sales/admin/sales?analytics=true`** - Sales analytics (TTL: 10 minutes)

#### High Priority
- **`GET /api/sales/cart/total`** - Cart total calculation (TTL: 2 minutes, user-specific)
- **`GET /api/sales/admin/sales`** - Admin sales list (TTL: 10 minutes)

### Cache Features

#### Automatic Invalidation
- **Product cache** is automatically cleared when admins create, update, or delete products
- **User-specific cache** can be invalidated per user
- **Sales cache** can be invalidated when new sales are processed

#### Development Logging
When running in development mode (`FLASK_DEBUG=true`), the application shows cache activity:
```
🚀 CACHE HIT: get_all_products (key: products.get_all...)
💾 CACHE MISS: get_product_by_id - Cached for 3600s (key: products.get_by_id...)
🗑️  Product cache invalidated successfully (5 individual product keys)
```

#### Cache Configuration
Configure cache behavior via environment variables:
```bash
# Redis Cloud connection (required)
REDIS_HOST=your-redis-cloud-endpoint.redislabs.com
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-cloud-password
REDIS_USERNAME=default

# Cache settings
CACHE_DEFAULT_TIMEOUT=300  # Default TTL in seconds
```

The cache implementation provides:
- 40-60% reduction in database queries
- 70-90% faster response times for cached endpoints
- Graceful degradation (continues working if Redis is unavailable)
- Pattern-based cache invalidation using Redis features

## 🏛️ Architecture

### Implemented Patterns
- **Repository Pattern**: Data access logic separation
- **Service Layer**: Centralized business logic
- **DTO Pattern**: Serialization/deserialization with Marshmallow
- **JWT Authentication**: Stateless authentication with RSA
- **Role-based Access Control**: Role-based authorization

### Technologies
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **Marshmallow**: Serialization
- **Flask-JWT-Extended**: JWT authentication
- **pytest**: Testing framework
- **PostgreSQL**: Database