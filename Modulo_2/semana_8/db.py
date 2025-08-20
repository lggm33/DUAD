from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Date
from sqlalchemy import insert, select, update, delete
import jwt

metadata_obj = MetaData()

user_table = Table(
    "users",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("username", String(30)),
    Column("password", String),
    Column("role", String),
)

product_table = Table(
    "products",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("price", Integer),
    Column("date_entry", Date),
    Column("quantity", Integer),
)

invoice_table = Table(
    "invoices",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer),
    Column("product_id", Integer),
    Column("quantity", Integer),
    Column("total_amount", Integer),
)


class DB_Manager:
    def __init__(self):
        self.engine = create_engine('postgresql+psycopg2://lggm:1234@localhost:5432/semana_7_db')

    def drop_and_create_tables(self):
        metadata_obj.drop_all(self.engine)
        metadata_obj.create_all(self.engine)

    def populate_tables(self):
        from datetime import date

        print("Populating tables...")

        users = [
            {"username": "admin", "password": "admin", "role": "admin"},
            {"username": "user", "password": "user", "role": "user"},
        ]

        products = [
            {"name": "apple", "price": 10, "date_entry": date(2021, 1, 1), "quantity": 100},
            {"name": "banana", "price": 20, "date_entry": date(2021, 1, 1), "quantity": 200},
            {"name": "orange", "price": 30, "date_entry": date(2021, 1, 1), "quantity": 300},
            {"name": "pineapple", "price": 40, "date_entry": date(2021, 1, 1), "quantity": 400},
            {"name": "strawberry", "price": 50, "date_entry": date(2021, 1, 1), "quantity": 500},
            {"name": "watermelon", "price": 60, "date_entry": date(2021, 1, 1), "quantity": 600},
            {"name": "mango", "price": 70, "date_entry": date(2021, 1, 1), "quantity": 700},
            {"name": "peach", "price": 80, "date_entry": date(2021, 1, 1), "quantity": 800},
            {"name": "pear", "price": 90, "date_entry": date(2021, 1, 1), "quantity": 900},
            {"name": "plum", "price": 100, "date_entry": date(2021, 1, 1), "quantity": 1000},
        ]

        invoices = [
            {"user_id": 1, "product_id": 1, "quantity": 10, "total_amount": 100},
            {"user_id": 2, "product_id": 2, "quantity": 20, "total_amount": 200},
            {"user_id": 1, "product_id": 3, "quantity": 30, "total_amount": 300},
        ]

        try:
            with self.engine.begin() as conn:
                # Insert users
                print("Inserting users...")
                stmt_users = insert(user_table).values(users)
                conn.execute(stmt_users)
                
                # Insert products
                print("Inserting products...")
                stmt_products = insert(product_table).values(products)
                conn.execute(stmt_products)
                
                # Insert invoices
                print("Inserting invoices...")
                stmt_invoices = insert(invoice_table).values(invoices)
                conn.execute(stmt_invoices)
                
                print("All data inserted successfully!")
                
        except Exception as e:
            print(f"Error inserting data: {e}")
        
    def insert_user(self, username, password, role):
        stmt = insert(user_table).returning(user_table.c.id).values(username=username, password=password, role=role)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.all()[0]

    def get_user(self, username, password):
        stmt = select(user_table).where(user_table.c.username == username).where(user_table.c.password == password)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            users = result.all()

            if(len(users)==0):
                return None
            else:
                return users[0]

    def get_user_by_id(self, id):
        stmt = select(user_table).where(user_table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            users = result.all()
            if(len(users)==0):
                return None
            else:
                return users[0]

    def get_product_by_id(self, id):
        stmt = select(product_table).where(product_table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            products = result.all()
            if(len(products)==0):
                return None
            else:
                return products[0]
    
    def get_product_dict_by_id(self, id):
        """Returns product as dictionary with named fields for better readability"""
        product = self.get_product_by_id(id)
        if not product:
            return None
        return {
            'id': product[0],
            'name': product[1], 
            'price': product[2],
            'date_entry': product[3],
            'quantity': product[4]
        }
    
    def get_all_products(self):
        stmt = select(product_table)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            products = result.all()
            return products
    
    def insert_product(self, name, price, date_entry, quantity):
        stmt = insert(product_table).returning(product_table.c.id).values(name=name, price=price, date_entry=date_entry, quantity=quantity)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.all()[0]
    
    def update_product(self, id, name, price, date_entry, quantity):    
        stmt = update(product_table).where(product_table.c.id == id).values(name=name, price=price, date_entry=date_entry, quantity=quantity)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.rowcount  # Returns number of rows affected
    
    def update_product_quantity(self, product_id, quantity_to_subtract):
        """Updates product quantity by subtracting the purchased amount"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        current_quantity = product[4]  # quantity is at index 4
        new_quantity = current_quantity - quantity_to_subtract
        
        if new_quantity < 0:
            raise ValueError("Not enough stock available")
        
        stmt = update(product_table).where(product_table.c.id == product_id).values(quantity=new_quantity)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.rowcount
    
    def delete_product(self, id):
        stmt = delete(product_table).where(product_table.c.id == id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.rowcount  # Returns number of rows affected
    
    def insert_invoice(self, user_id, product_id, quantity, total_amount):
        stmt = insert(invoice_table).returning(invoice_table.c.id).values(user_id=user_id, product_id=product_id, quantity=quantity, total_amount=total_amount)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.all()[0]
    
    def get_all_invoices(self):
        stmt = select(invoice_table)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            invoices = result.all()
            return invoices
    
    def get_invoices_by_user_id(self, user_id):
        stmt = select(invoice_table).where(invoice_table.c.user_id == user_id)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            invoices = result.all()
            return invoices
    
 
class JWT_Manager:
    def __init__(self, algorithm="RS256", private_key_path=None, public_key_path=None, secret=None):
        """
        Initialize JWT Manager for different algorithms
        
        Args:
            algorithm: "RS256" or "HS256"
            private_key_path: Path to private key file (for RS256 encoding)
            public_key_path: Path to public key file (for RS256 decoding)
            secret: Secret string (for HS256)
        """
        self.algorithm = algorithm
        
        if algorithm == "RS256":
            if not private_key_path or not public_key_path:
                raise ValueError("RS256 requires both private_key_path and public_key_path")
            
            # Load private key for encoding
            with open(private_key_path, 'rb') as f:
                self.private_key = f.read()
            
            # Load public key for decoding
            with open(public_key_path, 'rb') as f:
                self.public_key = f.read()
                
        elif algorithm == "HS256":
            if not secret:
                raise ValueError("HS256 requires a secret")
            self.secret = secret
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def encode(self, payload):
        """
        Encode JWT token
        
        Args:
            payload: Dictionary to encode in the token
            
        Returns:
            str: Encoded JWT token
        """
        try:
            if self.algorithm == "RS256":
                encoded = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
            else:  # HS256
                encoded = jwt.encode(payload, self.secret, algorithm=self.algorithm)
            return encoded
        except Exception as e:
            print(f"JWT encode error: {e}")
            return None

    def decode(self, token):
        """
        Decode JWT token and raise specific exceptions for better error handling
        
        Args:
            token: JWT token string to decode
            
        Returns:
            dict: Decoded payload
            
        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid (malformed, wrong signature, etc.)
        """
        if self.algorithm == "RS256":
            decoded = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
        else:  # HS256
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        return decoded
    
    def get_public_key_content(self):
        """
        Get public key content as string (for RS256 only)
        Useful for sharing with other services
        """
        if self.algorithm != "RS256":
            raise ValueError("Public key only available for RS256")
        return self.public_key.decode('utf-8')