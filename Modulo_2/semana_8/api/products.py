from flask import Blueprint, request, jsonify, Response
from auth import require_auth
from cache_decorators import cached_response, invalidate_cache, product_cache_key, all_products_cache_key, product_id_from_request

# Create blueprint for products endpoints
products_bp = Blueprint('products', __name__)

# Initialize managers (will be passed from main)
db_manager = None
cache_manager = None

def init_products_bp(db_mgr, cache_mgr):
    """Initialize the products blueprint with managers"""
    global db_manager, cache_manager
    db_manager = db_mgr
    cache_manager = cache_mgr

@products_bp.route('/products/<int:product_id>', methods=['GET'])
@require_auth() 
@cached_response(product_cache_key, ttl=600, debug_name="Product")
def get_product(current_user, product_id):
    """Get a product by ID - requires valid token"""
    if not product_id:
        return Response(status=400, response="Product ID is required")
    if not isinstance(product_id, int):
        return Response(status=400, response="Product ID must be an integer")
    if product_id <= 0:
        return Response(status=400, response="Product ID must be greater than 0")
    
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
    
    return jsonify(product=product_serializable)

@products_bp.route('/products', methods=['GET'])
@require_auth()
@cached_response(all_products_cache_key, ttl=600, debug_name="Products")
def get_products(current_user):
    """Get all products - requires valid token"""
    try:
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
        
        return jsonify(products=products_list)
    except Exception as e:
        return Response(status=500, response="Error retrieving products")

@products_bp.route('/products', methods=['POST'])
@require_auth('admin')
@invalidate_cache(all_products_cache_key)
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

        return jsonify(
            message="Product created successfully",
            product_id=product_id
        ), 201
    except ValueError as e:
        return Response(status=400, response=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return Response(status=500, response=f"Error creating product: {e}")

@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth('admin')
@invalidate_cache(product_cache_key, all_products_cache_key)
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

    return Response(status=204, response="Product deleted successfully")

@products_bp.route('/products/<int:product_id>', methods=['PATCH'])
@require_auth('admin')
@invalidate_cache(product_cache_key, all_products_cache_key)
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
    
    return Response(status=204, response="Product updated successfully")

@products_bp.route('/buy_product', methods=['POST'])
@require_auth()
@invalidate_cache(product_id_from_request, all_products_cache_key)
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
