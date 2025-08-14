from flask import Flask, request, jsonify, Response
from db import DB_Manager, JWT_Manager
from config import get_jwt_config, print_config_info
from auth import require_auth
import jwt
from cache_manager import CacheManager
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

cache_manager = CacheManager(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD
)

# Initialize database and JWT managers
db_manager = DB_Manager()

# Get JWT configuration and initialize manager
jwt_config = get_jwt_config()
jwt_manager = JWT_Manager(**jwt_config)

# Print configuration info on startup
print_config_info()

# Public endpoints
@app.route("/")
def root():
    return "<h1>Hello, World!</h1>"

@app.route("/liveness")
def liveness():
    return "<p>Hello, World!</p>"

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return Response(status=400, response="JSON data is required")
        
        if not data.get('username') or not data.get('password'):
            return Response(status=400, response="Username and password are required")
        
        result = db_manager.get_user(data.get('username'), data.get('password'))
        if not result:
            return Response(status=401, response="Invalid username or password")
        
        # Include user data in token to avoid DB queries
        user_id = result[0]
        username = result[1]
        role = result[3]
        
        token = jwt_manager.encode({
            'id': user_id,
            'username': username,
            'role': role
        })
        return jsonify(token=token)
    except ValueError as e:
        return Response(status=400, response=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return Response(status=500, response="Error during login")

# Protected endpoints

@app.route('/register', methods=['POST'])
@require_auth('admin')
def register(current_user):
    try:
        # Validate that the request content type is application/json
        if not request.is_json:
            return Response(status=400, response="Content-Type must be application/json")
        # Try to parse JSON and catch malformed JSON errors
        try:
            data = request.get_json(force=True)
        except Exception as e:
            return Response(status=400, response=f"Malformed JSON: {str(e)}")
        # Validate JSON structure: must be a dict and not empty
        if not isinstance(data, dict) or not data:
            return Response(status=400, response="JSON body must be a non-empty object")
        data = request.get_json()
        if not data:
            return Response(status=400, response="JSON data is required")
        
        # Validate required fields
        if not data.get('username') or not data.get('password') or not data.get('role'):
            return Response(status=400, response="Username, password and role are required")
        
        # Validate role is valid
        valid_roles = ['admin', 'user']
        if data.get('role') not in valid_roles:
            return Response(status=400, response=f"Invalid role. Valid roles are: {', '.join(valid_roles)}")
        
        result = db_manager.insert_user(data.get('username'), data.get('password'), data.get('role'))
        user_id = result[0]
        
        return jsonify(
            message=f"User '{data.get('username')}' with role '{data.get('role')}' created successfully",
            user_id=user_id
        ), 201
    except ValueError as e:
        return Response(status=400, response=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return Response(status=500, response=f"Error creating user: {e}")

@app.route('/me', methods=['GET'])
@require_auth()
def me(current_user):
    """Get current user information - requires valid token"""
    return jsonify(
        id=current_user['id'],
        username=current_user['username'],
        role=current_user['role']
    )

@app.route('/products/<int:product_id>', methods=['GET'])
@require_auth() 
def get_product(current_user, product_id):
    """Get a product by ID - requires valid token"""
    if not product_id:
        return Response(status=400, response="Product ID is required")
    if not isinstance(product_id, int):
        return Response(status=400, response="Product ID must be an integer")
    if product_id <= 0:
        return Response(status=400, response="Product ID must be greater than 0")
    
    cache_key = f"product_{product_id}"
    cached_product = cache_manager.get_data(cache_key)
    if cached_product:
        print(f"Product {product_id} found in cache")
        return jsonify(product=cached_product)
    
    product = db_manager.get_product_dict_by_id(product_id)
    if not product:
        return Response(status=404, response="Product not found")
    
    # Convert date to string for JSON serialization
    product_serializable = {
        'id': product['id'],
        'name': product['name'],
        'price': product['price'],
        'date_entry': str(product['date_entry']),
        'quantity': product['quantity']
    }
    
    cache_manager.store_data(cache_key, product_serializable, 600)
    return jsonify(product=product_serializable)

@app.route('/products', methods=['GET'])
@require_auth()
def get_products(current_user):
    """Get all products - requires valid token"""
    try:

        cache_key = "all_products"
        cached_products = cache_manager.get_data(cache_key)
        if cached_products:
            print("Products found in cache")
            return jsonify(products=cached_products)

        products = db_manager.get_all_products()
        products_list = []
        for product in products:
            products_list.append({
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'date_entry': str(product[3]),
                'quantity': product[4]
            })
        
        cache_manager.store_data(cache_key, products_list, 600)
        return jsonify(products=products_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving products")

@app.route('/products', methods=['POST'])
@require_auth('admin')
def create_product(current_user):
    """Create new product - requires admin role"""
    try:
        data = request.get_json()
        if not data:
            return Response(status=400, response="JSON data is required")
        
        required_fields = ['name', 'price', 'date_entry', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return Response(status=400, response=f"{field} is required")
        
        result = db_manager.insert_product(
            data.get('name'),
            data.get('price'),
            data.get('date_entry'),
            data.get('quantity')
        )
        product_id = result[0]
        cache_key = 'all_products'
        cache_manager.delete_data(cache_key)

        return jsonify(
            message="Product created successfully",
            product_id=product_id
        ), 201
    except ValueError as e:
        return Response(status=400, response=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return Response(status=500, response=f"Error creating product: {e}")


@app.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth('admin')
def delete_product(current_user, product_id):
    """Delete a product by ID - requires admin role"""
    if not product_id:
        return Response(status=400, response="Product ID is required")
    if not isinstance(product_id, int):
        return Response(status=400, response="Product ID must be an integer")
    if product_id <= 0:
        return Response(status=400, response="Product ID must be greater than 0")
    
    try:
        db_manager.delete_product(product_id)
    except Exception as e:
        return Response(status=500, response=f"Error deleting product: {e}")

    cache_key = f"product_{product_id}"
    cache_manager.delete_data(cache_key)
    cache_key = 'all_products'
    cache_manager.delete_data(cache_key)
    return Response(status=204, response="Product deleted successfully")

@app.route('/products/<int:product_id>', methods=['PATCH'])
@require_auth('admin')
def update_product(current_user, product_id):
    """Update a product by ID - requires admin role"""
    if not product_id:
        return Response(status=400, response="Product ID is required")
    if not isinstance(product_id, int):
        return Response(status=400, response="Product ID must be an integer")
    if product_id <= 0:
        return Response(status=400, response="Product ID must be greater than 0")
    
    try:
        db_manager.update_product(product_id, request.get_json())
    except Exception as e:
        return Response(status=500, response=f"Error updating product: {e}")
    
    cache_key = f"product_{product_id}"
    cache_manager.delete_data(cache_key)
    cache_key = 'all_products'
    cache_manager.delete_data(cache_key)
    return Response(status=204, response="Product updated successfully")

@app.route('/invoices', methods=['GET'])
@require_auth()
def get_user_invoices(current_user):
    """Get current user's invoices - requires valid token"""
    try:
        user_id = current_user['id']
        invoices = db_manager.get_invoices_by_user_id(user_id)
        invoices_list = []
        for invoice in invoices:
            invoices_list.append({
                'id': invoice[0],
                'user_id': invoice[1],
                'product_id': invoice[2],
                'quantity': invoice[3],
                'total_amount': invoice[4]
            })
        return jsonify(invoices=invoices_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving invoices")

@app.route('/invoices/all', methods=['GET'])
@require_auth('admin')
def get_all_invoices(current_user):
    """Get all invoices - requires admin role"""
    try:
        invoices = db_manager.get_all_invoices()
        invoices_list = []
        for invoice in invoices:
            invoices_list.append({
                'id': invoice[0],
                'user_id': invoice[1],
                'product_id': invoice[2],
                'quantity': invoice[3],
                'total_amount': invoice[4]
            })
        return jsonify(invoices=invoices_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving all invoices")

@app.route('/buy_product', methods=['POST'])
@require_auth()
def buy_product(current_user):
    """Buy a product - requires valid token"""
    try:
        data = request.get_json()
        if not data:
            return Response(status=400, response="JSON data is required")
        
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return Response(status=400, response=f"{field} is required")
        
        if data.get('quantity') <= 0:
            return Response(status=400, response="Quantity must be greater than 0")

        product_id = data.get('product_id')
        quantity = data.get('quantity')

        product = db_manager.get_product_dict_by_id(product_id)
        if not product:
            return Response(status=404, response="Product not found")

        if product['quantity'] < quantity:
            return Response(status=400, response="Not enough stock")

        db_manager.update_product_quantity(product_id, quantity)
        cache_key = f"product_{product_id}"
        cache_manager.delete_data(cache_key)
        cache_key = 'all_products'
        cache_manager.delete_data(cache_key)

        total_amount = product['price'] * quantity
        invoice = db_manager.insert_invoice(current_user['id'], product_id, quantity, total_amount)

        return jsonify(
            message="Product bought successfully",
            invoice_id=invoice[0]
        ), 201

    except ValueError as e:
        return Response(status=400, response=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return Response(status=500, response=f"Error buying product: {e}")


if __name__ == "__main__":
    try:
        db_manager.drop_and_create_tables()
        db_manager.populate_tables()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    app.run(host="localhost", port=3001, debug=True)