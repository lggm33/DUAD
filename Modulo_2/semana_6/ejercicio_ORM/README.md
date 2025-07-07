# SQLAlchemy ORM Implementation

This implementation fulfills all specified requirements using a well-organized modular architecture.

## Project Structure

```
ejercicio_ORM/
├── database_config.py      # SQLAlchemy configuration
├── models.py              # Database models
├── database_setup.py      # Database configuration and creation
├── user_manager.py        # User management
├── address_manager.py     # Address management
├── automobile_manager.py  # Automobile management
├── main.py               # Main script with demo
├── requirements.txt      # Dependencies
└── README.md            # This documentation
```

## Files and Responsibilities

### 1. `database_config.py`
- **Responsibility**: SQLAlchemy configuration
- **Functions**:
  - `validate_sqlalchemy_setup()`: Validates and displays SQLAlchemy version
  - `get_database_path()`: Gets database file path
  - `get_session()`: Creates new database session

### 2. `models.py`
- **Responsibility**: Database model definitions
- **Classes**:
  - `User`: User model
  - `Address`: Address model
  - `Automobile`: Automobile model

### 3. `database_setup.py`
- **Responsibility**: Database configuration and creation
- **Functions**:
  - `check_database_exists()`: Checks if .db file exists
  - `create_database_if_not_exists()`: Creates .db file if it doesn't exist
  - `check_and_create_tables()`: Checks and creates tables if they don't exist
  - `setup_database()`: Complete setup process

### 4. `user_manager.py`
- **Responsibility**: User management (Requirement 4.1 and 4.5)
- **CRUD Methods**:
  - `create_user()`: Create user
  - `update_user()`: Update user
  - `delete_user()`: Delete user
  - `get_all_users()`: Query all users
  - `get_user()`: Get user by ID
  - `get_user_by_email()`: Get user by email

### 5. `address_manager.py`
- **Responsibility**: Address management (Requirement 4.3 and 4.7)
- **CRUD Methods**:
  - `create_address()`: Create address
  - `update_address()`: Update address
  - `delete_address()`: Delete address
  - `get_all_addresses()`: Query all addresses
  - `get_address()`: Get address by ID
  - `get_addresses_by_user()`: Get addresses by user

### 6. `automobile_manager.py`
- **Responsibility**: Automobile management (Requirement 4.2, 4.4 and 4.6)
- **CRUD Methods**:
  - `create_automobile()`: Create automobile
  - `update_automobile()`: Update automobile
  - `delete_automobile()`: Delete automobile
  - `get_all_automobiles()`: Query all automobiles
  - `associate_automobile_to_user()`: Associate automobile to user
  - `disassociate_automobile_from_user()`: Disassociate automobile from user
  - `get_automobile()`: Get automobile by ID
  - `get_automobiles_by_user()`: Get automobiles by user
  - `get_available_automobiles()`: Get available automobiles

## Requirements Compliance

### Requirement 1: SQLAlchemy Setup ✅
- **File**: `database_config.py`
- **Function**: `validate_sqlalchemy_setup()`
- **Version**: SQLAlchemy 1.4.46

### Requirement 2: Database Structure ✅
- **File**: `models.py`
- **Tables**: Users, Addresses, Automobiles
- **Relationships**: FKs implemented correctly

### Requirement 3: Table Validation and Creation ✅
- **File**: `database_setup.py`
- **Function**: `setup_database()`
- **Behavior**: Checks if .db exists, creates if not, checks tables and creates them

### Requirement 4: Classes and Methods ✅

#### 4.1 Create/Update/Delete User
- **File**: `user_manager.py`
- **Methods**:
  - `create_user(name, email, phone=None)`
  - `update_user(user_id, name=None, email=None, phone=None)`
  - `delete_user(user_id)`

#### 4.2 Create/Update/Delete Automobile
- **File**: `automobile_manager.py`
- **Methods**:
  - `create_automobile(brand, model, year, color, license_plate, user_id=None)`
  - `update_automobile(automobile_id, brand=None, model=None, year=None, color=None, license_plate=None)`
  - `delete_automobile(automobile_id)`

#### 4.3 Create/Update/Delete Address
- **File**: `address_manager.py`
- **Methods**:
  - `create_address(street, city, state, zip_code, user_id)`
  - `update_address(address_id, street=None, city=None, state=None, zip_code=None)`
  - `delete_address(address_id)`

#### 4.4 Associate Automobile to User
- **File**: `automobile_manager.py`
- **Method**: `associate_automobile_to_user(automobile_id, user_id)`

#### 4.5 Query All Users
- **File**: `user_manager.py`
- **Method**: `get_all_users()`

#### 4.6 Query All Automobiles
- **File**: `automobile_manager.py`
- **Method**: `get_all_automobiles()`

#### 4.7 Query All Addresses
- **File**: `address_manager.py`
- **Method**: `get_all_addresses()`

## Installation and Usage

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the main script
```bash
python main.py
```

### 3. Individual manager usage
```python
from user_manager import UserManager
from address_manager import AddressManager
from automobile_manager import AutomobileManager

# Create managers
user_manager = UserManager()
address_manager = AddressManager()
automobile_manager = AutomobileManager()

# Use specific methods
user = user_manager.create_user("Juan Pérez", "juan@email.com", "123456789")
address = address_manager.create_address("123 Main St", "Bogotá", "Cundinamarca", "110111", user.id)
automobile = automobile_manager.create_automobile("Toyota", "Corolla", 2020, "White", "ABC123")

# Associate automobile to user
automobile_manager.associate_automobile_to_user(automobile.id, user.id)

# Query all records
users = user_manager.get_all_users()
addresses = address_manager.get_all_addresses()
automobiles = automobile_manager.get_all_automobiles()

# Close sessions
user_manager.close_session()
address_manager.close_session()
automobile_manager.close_session()
```

## Technical Features

- **Database**: SQLite
- **ORM**: SQLAlchemy 1.4.46
- **Architecture**: Modular with separation of concerns
- **Type hints**: Static typing for better development
- **Session management**: Proper connection handling
- **Relationships**: FKs and bidirectional relationships
- **Validation**: Automatic database and table verification

## Important Notes

- The script automatically checks for the existence of the `.db` file
- Tables are created automatically if they don't exist
- All addresses must have an associated user (mandatory FK)
- Automobiles can exist without an associated user (optional FK)
- The demo includes database cleanup to avoid unique data conflicts
- Remember to close sessions after using the managers 