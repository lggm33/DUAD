# Lyfter Car Rental System

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone git@github.com:lggm33/DUAD.git
cd semana_5
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=lyfter_car_rental
DB_SCHEMA=lyfter_car_rental
```

### 5. Run the Application
```bash
python main.py
```

The application will automatically:
- Set up the database schema
- Create all required tables
- Populate with sample data
- Start the API server on http://localhost:8000

## 📊 Database Schema

### Users Table
- `id`: Primary key (auto-increment)
- `name`: User's full name
- `email`: Email address (unique)
- `username`: Username (unique)
- `password`: User password
- `date_of_birth`: Birth date
- `account_state`: Account status (active/inactive)
- `created_at`, `updated_at`: Timestamps

### Automobiles Table
- `id`: Primary key (auto-increment)
- `make`: Car manufacturer
- `model`: Car model
- `year_manufactured`: Manufacturing year
- `condition`: Car condition description
- `status`: Car status (available/rented/maintenance/retired)
- `created_at`, `updated_at`: Timestamps

### Rentals Table
- `id`: Primary key (auto-increment)
- `user_id`: Foreign key to users table
- `automobile_id`: Foreign key to automobiles table
- `rental_date`: Rental start date (auto-generated)
- `expected_return_date`: Expected return date
- `actual_return_date`: Actual return date (nullable)
- `rental_status`: Rental status (active/completed/overdue/cancelled)
- `daily_rate`: Daily rental rate
- `total_cost`: Total rental cost
- `created_at`, `updated_at`: Timestamps

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000
```

### Users Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/` | Create new user |
| GET | `/users/` | List users with optional filters |
| GET | `/users/{id}` | Get user by ID |
| PUT | `/users/{id}/status` | Update user account status |
| DELETE | `/users/{id}` | Delete user |
| GET | `/users/stats/summary` | Get user statistics |

#### User Filters
- `username`: Filter by username (partial match)
- `email`: Filter by email (partial match)
- `account_state`: Filter by account status (true/false)
- `limit`: Number of records to return (default: 50)
- `offset`: Number of records to skip (default: 0)

### Automobiles Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/automobiles/` | Add new automobile |
| GET | `/automobiles/` | List automobiles with optional filters |
| GET | `/automobiles/{id}` | Get automobile by ID |
| PUT | `/automobiles/{id}/status` | Update automobile status |
| DELETE | `/automobiles/{id}` | Delete automobile |
| GET | `/automobiles/stats/summary` | Get automobile statistics |

#### Automobile Filters
- `make`: Filter by manufacturer (partial match)
- `model`: Filter by model (partial match)
- `status`: Filter by status (available/rented/maintenance/retired)
- `year_manufactured`: Filter by manufacturing year
- `limit`: Number of records to return (default: 50)
- `offset`: Number of records to skip (default: 0)

### Rentals Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rentals/` | Create new rental |
| GET | `/rentals/` | List rentals with optional filters |
| GET | `/rentals/{id}` | Get rental by ID |
| PUT | `/rentals/{id}/complete` | Complete rental (return car) |
| PUT | `/rentals/{id}/status` | Update rental status |
| DELETE | `/rentals/{id}` | Cancel rental |
| GET | `/rentals/stats/summary` | Get rental statistics |

#### Rental Filters
- `user_id`: Filter by user ID
- `automobile_id`: Filter by automobile ID
- `rental_status`: Filter by status (active/completed/overdue/cancelled)
- `rental_date_from`: Filter rentals from date
- `rental_date_to`: Filter rentals to date
- `limit`: Number of records to return (default: 50)
- `offset`: Number of records to skip (default: 0)

## 🧪 Example Usage

### Create User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "username": "johndoe",
    "password": "securepassword",
    "date_of_birth": "1990-01-01"
  }'
```

### List Available Cars
```bash
curl "http://localhost:8000/automobiles/?status=available"
```

### Create Rental
```bash
curl -X POST "http://localhost:8000/rentals/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "automobile_id": 1,
    "expected_return_date": "2024-12-31",
    "daily_rate": 50.00,
    "total_cost": 350.00
  }'
```

## 🔧 Management Scripts

The system includes utility scripts for common operations:

- `scripts/add_user.py`: Add new user
- `scripts/add_automobile.py`: Add new automobile
- `scripts/create_rental.py`: Create new rental
- `scripts/complete_rental.py`: Complete rental
- `scripts/change_user_status.py`: Change user status
- `scripts/change_automobile_status.py`: Change automobile status
- `scripts/disable_automobile.py`: Disable automobile
- `scripts/get_available_automobiles.py`: Get available cars
- `scripts/get_rented_automobiles.py`: Get rented cars

## 📁 Project Structure

```
semana_5/
├── api/                          # API endpoints
│   ├── __init__.py
│   ├── automobiles.py           # Automobile endpoints
│   ├── models.py                # Pydantic models
│   ├── rentals.py               # Rental endpoints
│   └── users.py                 # User endpoints
├── database_setup/              # Database setup scripts
│   ├── __init__.py
│   ├── setup_automobiles.py     # Automobile table setup
│   ├── setup_complete.py        # Complete system setup
│   ├── setup_database.py        # Database initialization
│   ├── setup_rentals.py         # Rental table setup
│   └── setup_users.py           # User table setup
├── repositories/                # Data access layer
│   ├── __init__.py
│   ├── automobile_repository.py # Automobile data access
│   ├── base_repository.py       # Base repository class
│   ├── rental_repository.py     # Rental data access
│   └── user_repository.py       # User data access
├── scripts/                     # Utility scripts
│   └── [various management scripts]
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── api.http                     # HTTP request examples
├── MOCK_DATA_*.csv             # Sample data files
└── README.md                    # This file
```

## 🏥 Health Check

The system provides health check endpoints:

- `GET /`: Root endpoint with API information
- `GET /health`: Health check with database connectivity test

## 🚨 Error Handling

The API provides comprehensive error handling with:
- HTTP status codes
- Descriptive error messages
- Validation error details
- Database connection error handling

## 🔒 Security Considerations

For production deployment:
- Update CORS settings in `main.py`
- Use environment variables for sensitive data
- Implement proper authentication/authorization
- Use secure password hashing
- Configure SSL/TLS

## 🚀 Deployment

The application is ready for deployment with:
- Docker containerization support
- Environment variable configuration
- Scalable FastAPI architecture
- PostgreSQL database backend

