# Import all necessary modules
from database_config import validate_sqlalchemy_setup
from database_setup import setup_database
from user_manager import UserManager
from address_manager import AddressManager
from automobile_manager import AutomobileManager

# Demo functions
def clean_database():
    """Clean all data from the database for demo purposes"""
    print("\nCleaning database for demo...")
    
    # Initialize managers
    user_manager = UserManager()
    address_manager = AddressManager()
    automobile_manager = AutomobileManager()
    
    # Delete all existing data
    for automobile in automobile_manager.get_all_automobiles():
        automobile_manager.delete_automobile(automobile.id)
    
    for address in address_manager.get_all_addresses():
        address_manager.delete_address(address.id)
    
    for user in user_manager.get_all_users():
        user_manager.delete_user(user.id)
    
    print("Database cleaned successfully!")
    
    # Close sessions
    user_manager.close_session()
    address_manager.close_session()
    automobile_manager.close_session()

def demo_operations():
    """Demonstrate all the required operations"""
    print("\n" + "="*50)
    print("DEMO: Testing all operations")
    print("="*50)
    
    # Clean database first
    clean_database()
    
    # Initialize managers
    user_manager = UserManager()
    address_manager = AddressManager()
    automobile_manager = AutomobileManager()
    
    # Create users
    print("\n1. Creating users...")
    user1 = user_manager.create_user("Juan Pérez", "juan@email.com", "123456789")
    user2 = user_manager.create_user("María García", "maria@email.com", "987654321")
    print(f"Created user: {user1}")
    print(f"Created user: {user2}")
    
    # Create addresses
    print("\n2. Creating addresses...")
    address1 = address_manager.create_address("123 Main St", "Bogotá", "Cundinamarca", "110111", user1.id)
    address2 = address_manager.create_address("456 Oak Ave", "Medellín", "Antioquia", "050001", user2.id)
    print(f"Created address: {address1}")
    print(f"Created address: {address2}")
    
    # Create automobiles
    print("\n3. Creating automobiles...")
    auto1 = automobile_manager.create_automobile("Toyota", "Corolla", 2020, "White", "ABC123")
    auto2 = automobile_manager.create_automobile("Honda", "Civic", 2019, "Blue", "XYZ789", user1.id)
    print(f"Created automobile: {auto1}")
    print(f"Created automobile: {auto2}")
    
    # Associate automobile to user
    print("\n4. Associating automobile to user...")
    automobile_manager.associate_automobile_to_user(auto1.id, user2.id)
    print(f"Associated automobile {auto1.id} to user {user2.id}")
    
    # Query all records
    print("\n5. Querying all records...")
    
    print("\nAll users:")
    users = user_manager.get_all_users()
    for user in users:
        print(f"  - {user}")
    
    print("\nAll addresses:")
    addresses = address_manager.get_all_addresses()
    for address in addresses:
        print(f"  - {address}")
    
    print("\nAll automobiles:")
    automobiles = automobile_manager.get_all_automobiles()
    for automobile in automobiles:
        print(f"  - {automobile}")
    
    # Update operations
    print("\n6. Testing update operations...")
    updated_user = user_manager.update_user(user1.id, phone="111222333")
    print(f"Updated user: {updated_user}")
    
    updated_address = address_manager.update_address(address1.id, street="789 New Street")
    print(f"Updated address: {updated_address}")
    
    updated_auto = automobile_manager.update_automobile(auto1.id, color="Red")
    print(f"Updated automobile: {updated_auto}")
    
    print("\nDemo completed successfully!")
    
    # Close sessions
    user_manager.close_session()
    address_manager.close_session()
    automobile_manager.close_session()

def main():
    """Main function to run the complete setup and demo"""
    print("SQLAlchemy ORM Setup and Demo")
    print("="*30)
    
    # 1. Validate SQLAlchemy setup
    validate_sqlalchemy_setup()
    
    # 2. Setup database (check and create if needed)
    setup_database()
    
    # 3. Run demo operations
    demo_operations()
    
    print("\n" + "="*50)
    print("Setup and demo completed successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
