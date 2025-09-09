# app/security/decorators.py
from functools import wraps
from typing import Callable, Iterable, Any
from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity, verify_jwt_in_request
from app.utils.exceptions import json_error

def roles_required(*allowed_roles: str):
    """
    Enforce that current JWT has one of the allowed roles.
    Usage:
        @jwt_required()
        @roles_required("admin")
        def create_product(): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return json_error("Permission denied", 403)
            return fn(*args, **kwargs)
        return decorated
    return wrapper

def optional_roles(allowed_roles: Iterable[str]):
    """
    Decorator that allows optional JWT authentication with role validation.
    If JWT is present and valid, validates that user has one of the allowed roles.
    If no JWT is present, continues without authentication.
    The function can check if user is authenticated/authorized via flask.g.is_authenticated and flask.g.user_role
    """
    def wrapper(fn):
        @wraps(fn)
        @jwt_required(optional=True)
        def decorated(*args, **kwargs):
            from flask import g
            
            # Initialize default values
            g.is_authenticated = False
            g.user_role = None
            g.has_required_role = False
            
            try:
                # Try to get JWT claims - this will be None if no JWT is present
                claims = get_jwt()
                
                if claims:  # JWT is present and valid
                    user_role = claims.get("role")
                    
                    # User is authenticated
                    g.is_authenticated = True
                    g.user_role = user_role
                    
                    # Check if user has one of the required roles
                    if user_role in allowed_roles:
                        g.has_required_role = True
                        
            except Exception:
                # Handle any unexpected errors gracefully
                # This should rarely happen with @jwt_required(optional=True)
                pass
            
            return fn(*args, **kwargs)
        return decorated
    return wrapper

def owner_required(resource_user_id_getter: Callable[..., Any]):
    """
    Ensure the current user owns the resource OR is admin.
    `resource_user_id_getter(*args, **kwargs) -> user_id`
    Example:
        @jwt_required()
        @owner_required(lambda order_id: Order.query.get(order_id).user_id)
        def get_order(order_id): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            claims = get_jwt()
            current_user_id = int(get_jwt_identity())  # Convert string to int for DB queries
            role = claims.get("role")
            try:
                resource_owner_id = resource_user_id_getter(*args, **kwargs)
            except Exception:
                return json_error("Could not resolve resource owner", 400)

            if role == "admin" or resource_owner_id == current_user_id:
                return fn(*args, **kwargs)
            return json_error("Forbidden", 403)
        return decorated
    return wrapper

# Helper combinator for common patterns
def admin_only(fn):
    @wraps(fn)
    @jwt_required()
    @roles_required("admin")
    def decorated(*args, **kwargs):
        return fn(*args, **kwargs)
    return decorated

def owner_or_admin_required(user_id_param: str = "user_id"):
    """
    Decorator that ensures the current user is either:
    1. An admin (can access any resource)
    2. A customer accessing their own resource (user_id matches current user)
    
    Args:
        user_id_param: Name of the URL parameter that contains the user_id
    
    Usage:
        @jwt_required()
        @owner_or_admin_required()
        def update_user_data(user_id): ...
        
        @jwt_required()
        @owner_or_admin_required("owner_id")
        def update_resource(owner_id): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            
            claims = get_jwt()
            current_user_id = int(get_jwt_identity())
            user_role = claims.get("role")
            
            # Get the user_id from URL parameters
            target_user_id = kwargs.get(user_id_param)
            if target_user_id is None:
                return json_error(f"Missing required parameter: {user_id_param}", 400)
            
            # Admin can access anything
            if user_role == "admin":
                g.is_resource_owner = False
                g.is_admin_access = True
                return fn(*args, **kwargs)
            
            # Customer can only access their own resources
            if user_role == "customer":
                if current_user_id == int(target_user_id):
                    g.is_resource_owner = True
                    g.is_admin_access = False
                    return fn(*args, **kwargs)
                else:
                    return json_error("Customers can only access their own resources", 403)
            
            # Unknown role or no permission
            return json_error("Permission denied", 403)
            
        return decorated
    return wrapper

def cart_owner_required(cart_id_param: str = "cart_id"):
    """
    Decorator that ensures the current user owns the specified cart.
    This decorator validates cart ownership by checking that the cart belongs to the current user.
    
    Args:
        cart_id_param: Name of the URL parameter that contains the cart_id
    
    Usage:
        @jwt_required()
        @cart_owner_required()
        def update_cart_status(cart_id): ...
        
        @jwt_required()
        @cart_owner_required("cart_identifier")
        def get_cart(cart_identifier): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            from app.services import cart_service
            
            current_user_id = int(get_jwt_identity())
            
            # Get the cart_id from URL parameters
            cart_id = kwargs.get(cart_id_param)
            if cart_id is None:
                return json_error(f"Missing required parameter: {cart_id_param}", 400)
            
            try:
                # Use cart_service validation which already checks ownership
                cart = cart_service.get_cart_by_id(cart_id, current_user_id)
                g.cart = cart
                g.is_cart_owner = True
                return fn(*args, **kwargs)
                
            except Exception as e:
                # Cart service will raise ForbiddenError if not owner, CartNotFoundError if not found
                error_msg = str(e)
                if "Access denied" in error_msg or "belongs to another user" in error_msg:
                    return json_error("You don't have permission to access this cart", 403)
                elif "not found" in error_msg.lower():
                    return json_error("Cart not found", 404)
                else:
                    return json_error("Error accessing cart", 400)
            
        return decorated
    return wrapper

def customer_only(fn):
    """
    Decorator that ensures the current user has customer role.
    This is useful for endpoints that should only be accessible to customers.
    """
    @wraps(fn)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        user_role = claims.get("role")
        
        if user_role != "customer":
            return json_error("This endpoint is only accessible to customers", 403)
            
        return fn(*args, **kwargs)
    return decorated

def resource_access_required(resource_service, resource_id_param: str, ownership_check=None):
    """
    Decorator that validates resource access with ownership checks.
    
    Args:
        resource_service: Service object with get_*_by_id method
        resource_id_param: Name of the URL parameter containing resource ID
        ownership_check: Function that takes (resource, current_user_id) and returns bool
    
    Usage:
        @jwt_required()
        @resource_access_required(
            delivery_address_service, 
            "delivery_address_id",
            lambda addr, user_id: addr.user_id == user_id
        )
        def update_address(user_id, delivery_address_id): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            
            claims = get_jwt()
            current_user_id = int(get_jwt_identity())
            user_role = claims.get("role")
            
            # Get resource ID from URL parameters
            resource_id = kwargs.get(resource_id_param)
            if resource_id is None:
                return json_error(f"Missing required parameter: {resource_id_param}", 400)
            
            # Get the resource using the service
            method_name = f"get_{resource_service.__class__.__name__.replace('Service', '').lower()}_by_id"
            if hasattr(resource_service, method_name):
                get_method = getattr(resource_service, method_name)
            else:
                # Fallback to generic method name
                get_method = getattr(resource_service, f"get_by_id", None)
                if not get_method:
                    return json_error("Service method not found", 500)
            
            try:
                resource = get_method(resource_id)
                if not resource:
                    return json_error("Resource not found", 404)
            except Exception:
                return json_error("Resource not found", 404)
            
            # Admin can access anything
            if user_role == "admin":
                g.resource = resource
                g.is_resource_owner = False
                g.is_admin_access = True
                return fn(*args, **kwargs)
            
            # Customer needs ownership check
            if user_role == "customer" and ownership_check:
                if ownership_check(resource, current_user_id):
                    g.resource = resource
                    g.is_resource_owner = True
                    g.is_admin_access = False
                    return fn(*args, **kwargs)
                else:
                    return json_error("You don't have permission to access this resource", 403)
            
            return json_error("Permission denied", 403)
            
        return decorated
    return wrapper

def cart_owner_required(cart_id_param: str = "cart_id"):
    """
    Decorator that ensures the current user owns the specified cart.
    This decorator validates cart ownership by checking that the cart belongs to the current user.
    
    Args:
        cart_id_param: Name of the URL parameter that contains the cart_id
    
    Usage:
        @jwt_required()
        @cart_owner_required()
        def update_cart_status(cart_id): ...
        
        @jwt_required()
        @cart_owner_required("cart_identifier")
        def get_cart(cart_identifier): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            from app.services import cart_service
            
            current_user_id = int(get_jwt_identity())
            
            # Get the cart_id from URL parameters
            cart_id = kwargs.get(cart_id_param)
            if cart_id is None:
                return json_error(f"Missing required parameter: {cart_id_param}", 400)
            
            try:
                # Use cart_service validation which already checks ownership
                cart = cart_service.get_cart_by_id(cart_id, current_user_id)
                g.cart = cart
                g.is_cart_owner = True
                return fn(*args, **kwargs)
                
            except Exception as e:
                # Cart service will raise ForbiddenError if not owner, CartNotFoundError if not found
                error_msg = str(e)
                if "Access denied" in error_msg or "belongs to another user" in error_msg:
                    return json_error("You don't have permission to access this cart", 403)
                elif "not found" in error_msg.lower():
                    return json_error("Cart not found", 404)
                else:
                    return json_error("Error accessing cart", 400)
            
        return decorated
    return wrapper

def customer_only(fn):
    """
    Decorator that ensures the current user has customer role.
    This is useful for endpoints that should only be accessible to customers.
    """
    @wraps(fn)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        user_role = claims.get("role")
        
        if user_role != "customer":
            return json_error("This endpoint is only accessible to customers", 403)
            
        return fn(*args, **kwargs)
    return decorated

def delivery_address_access_required(address_id_param: str = "delivery_address_id"):
    """
    Specialized decorator for delivery address access control.
    Validates that:
    1. User has admin or customer role  
    2. Customer can only access their own addresses
    3. Address exists and belongs to the user (for customers)
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            from app.services import delivery_address_service, user_service
            
            claims = get_jwt()
            current_user_id = int(get_jwt_identity())
            user_role = claims.get("role")
            
            # Get parameters
            user_id = kwargs.get("user_id")
            address_id = kwargs.get(address_id_param)
            
            if user_id is None:
                return json_error("Missing user_id parameter", 400)
            
            # Validate user exists
            try:
                user = user_service.get_user_by_id(user_id)
                if not user:
                    return json_error("User not found", 404)
            except Exception:
                return json_error("User not found", 404)
            
            # Admin can access anything
            if user_role == "admin":
                g.is_admin_access = True
                g.is_resource_owner = False
                return fn(*args, **kwargs)
            
            # Customer validation
            if user_role == "customer":
                # Customer can only access their own addresses
                if current_user_id != int(user_id):
                    return json_error("Customers can only access their own delivery addresses", 403)
                
                # If we need to validate a specific address
                if address_id is not None:
                    try:
                        address = delivery_address_service.get_delivery_address_by_id(address_id)
                        if not address:
                            return json_error("Delivery address not found", 404)
                        
                        # Verify ownership
                        if address.user_id != current_user_id:
                            return json_error("This delivery address does not belong to you", 403)
                        
                        g.delivery_address = address
                    except Exception:
                        return json_error("Delivery address not found", 404)
                
                g.is_admin_access = False
                g.is_resource_owner = True
                return fn(*args, **kwargs)
            
            return json_error("Permission denied", 403)
            
        return decorated
    return wrapper

def cart_owner_required(cart_id_param: str = "cart_id"):
    """
    Decorator that ensures the current user owns the specified cart.
    This decorator validates cart ownership by checking that the cart belongs to the current user.
    
    Args:
        cart_id_param: Name of the URL parameter that contains the cart_id
    
    Usage:
        @jwt_required()
        @cart_owner_required()
        def update_cart_status(cart_id): ...
        
        @jwt_required()
        @cart_owner_required("cart_identifier")
        def get_cart(cart_identifier): ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            from flask import g
            from app.services import cart_service
            
            current_user_id = int(get_jwt_identity())
            
            # Get the cart_id from URL parameters
            cart_id = kwargs.get(cart_id_param)
            if cart_id is None:
                return json_error(f"Missing required parameter: {cart_id_param}", 400)
            
            try:
                # Use cart_service validation which already checks ownership
                cart = cart_service.get_cart_by_id(cart_id, current_user_id)
                g.cart = cart
                g.is_cart_owner = True
                return fn(*args, **kwargs)
                
            except Exception as e:
                # Cart service will raise ForbiddenError if not owner, CartNotFoundError if not found
                error_msg = str(e)
                if "Access denied" in error_msg or "belongs to another user" in error_msg:
                    return json_error("You don't have permission to access this cart", 403)
                elif "not found" in error_msg.lower():
                    return json_error("Cart not found", 404)
                else:
                    return json_error("Error accessing cart", 400)
            
        return decorated
    return wrapper

def customer_only(fn):
    """
    Decorator that ensures the current user has customer role.
    This is useful for endpoints that should only be accessible to customers.
    """
    @wraps(fn)
    @jwt_required()
    def decorated(*args, **kwargs):
        claims = get_jwt()
        user_role = claims.get("role")
        
        if user_role != "customer":
            return json_error("This endpoint is only accessible to customers", 403)
            
        return fn(*args, **kwargs)
    return decorated
