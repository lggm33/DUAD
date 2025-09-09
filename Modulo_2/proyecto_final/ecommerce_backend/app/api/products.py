from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.security.decorators import admin_only, roles_required
from app.schemas.product import ProductCreateSchema, ProductReadSchema, ProductUpdateSchema
from app.services import product_service
from app.utils.decorators import handle_errors

bp = Blueprint("products", __name__, url_prefix="/products")

@bp.post("/")
@admin_only
@handle_errors("creating product", handle_validation=True)
def create_product():
    """
    Create a new product (Admin only)
    """
    data = ProductCreateSchema().load(request.get_json() or {})
    product = product_service.create_product(data)
    return jsonify(ProductReadSchema().dump(product)), 201

@bp.get("/")
@jwt_required()
@roles_required("admin", "customer")
@handle_errors("getting products")
def get_products():
    """
    Get all products - CACHED (30 min TTL)
    
    Cache: Response is cached for 30 minutes. Cache is automatically 
           invalidated when admin creates, updates, or deletes products.
    """
    products = product_service.get_all_products()
    return jsonify(ProductReadSchema().dump(products, many=True)), 200

@bp.get("/<int:product_id>")
@jwt_required()
@roles_required("admin", "customer")
@handle_errors("getting product")
def get_product(product_id: int):
    """
    Get a specific product by ID - CACHED (1 hour TTL)
    
    Cache: Response is cached for 1 hour. Cache is automatically 
           invalidated when admin updates or deletes this product.
    """
    product = product_service.get_product_by_id(product_id)
    return jsonify(ProductReadSchema().dump(product)), 200

@bp.put("/<int:product_id>")
@admin_only
@handle_errors("updating product", handle_validation=True)
def update_product(product_id: int):
    """
    Update an existing product (Admin only)
    """
    data = ProductUpdateSchema().load(request.get_json() or {})
    product = product_service.update_product(product_id, data)
    return jsonify(ProductReadSchema().dump(product)), 200

@bp.delete("/<int:product_id>")
@admin_only
@handle_errors("deleting product")
def delete_product(product_id: int):
    """
    Delete a product (Admin only)
    
    URL Parameters:
        product_id (int): The ID of the product to delete
        
    Returns:
        HTTP 200: Product deleted successfully
        {
            "id": 1,
            "name": "Deleted Product Name",
            "description": "Product Description",
            "price": 29.99,
            "stock": 0
        }
    """
    product = product_service.delete_product(product_id)
    return jsonify(ProductReadSchema().dump(product)), 200