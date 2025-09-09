from app.schemas.user import UserReadSchema, UserUpdateSchema, RegisterSchema, LoginSchema
from marshmallow import ValidationError
from app.utils.decorators import handle_errors
from app.utils.exceptions import json_error
from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.security.decorators import admin_only, optional_roles, owner_or_admin_required, delivery_address_access_required
from app.services import user_service, auth_service, delivery_address_service
from app.schemas.delivery_address import DeliveryAddressCreateSchema, DeliveryAddressReadSchema, DeliveryAddressUpdateSchema
from app.security.blocklist import block_token

bp = Blueprint("users", __name__, url_prefix="/users")

# Authentication endpoints
@bp.post("/register")
@handle_errors("registering user", handle_validation=True)
@optional_roles(["admin"])
def register():
    """
    Register a new user
    
    Authentication: Optional (JWT token for admin role assignment)
    
    Request Body:
        - email (str): User email (required, unique)
        - password (str): User password (required, min 8 chars)
        - name (str): User full name (required)
        - phone (str): User phone number (optional)
        - role (str): User role (optional, defaults to "customer")
                     Only admins can assign roles other than "customer"
    
    Returns:
        HTTP 201: User registered successfully
        {
            "id": 1,
            "email": "user@example.com",
            "name": "John Doe",
            "phone": "+1234567890",
            "role": "customer"
        }

    """
    # Check if request has data
    if not request.data and not request.form:
        return jsonify({"error": "Request body cannot be empty"}), 400
    
    json_data = request.get_json(silent=True)
    if json_data is None:
        return jsonify({"error": "Request must contain valid JSON"}), 400
    
    try:
        data = RegisterSchema().load(json_data)
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.messages}), 400
    
    # Determine the role for the new user
    requested_role = data.get("role", "customer")
    
    # Only allow role assignment if the current user is authenticated and is admin
    if g.get("has_required_role", False):
        # User is admin, allow any role creation (including admin)
        final_role = requested_role
    else:
        # User is not admin or not authenticated, force role to customer
        final_role = "customer"
    
    user = auth_service.register_user(
        email=data["email"],
        password=data["password"],
        name=data["name"],
        phone=data.get("phone", None),
        role=final_role,
    )
    return jsonify(UserReadSchema().dump(user)), 201


@bp.post("/login")
@handle_errors("logging in", handle_validation=True)
def login():
    """
    Authenticate user and issue JWT tokens
    
    Request Body:
        - email (str): User email (required)
        - password (str): User password (required)
    
    Returns:
        HTTP 200: Login successful
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "name": "John Doe",
                "phone": "+1234567890",
                "role": "customer"
            }
        }
    """
    data = LoginSchema().load(request.get_json() or {})
    user = auth_service.authenticate_user(data["email"], data["password"])
    tokens = auth_service.issue_tokens_for(user)
    return jsonify({
        **tokens,
        "user": UserReadSchema().dump(user)
    }), 200


@bp.post("/refresh")
@jwt_required(refresh=True)
@handle_errors("refreshing token")
def refresh():
    """
    Refresh access token using refresh token
    
    Authentication: Refresh token required (in Authorization header)
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        HTTP 200: New access token issued
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }

    """
    uid = int(get_jwt_identity())
    user = auth_service.get_user_or_404(uid)
    new_access = auth_service.issue_tokens_for(user)["access_token"]
    return jsonify({"access_token": new_access}), 200


@bp.post("/logout")
@jwt_required(refresh=True)
@handle_errors("logging out")
def logout():
    """
    Logout user by revoking refresh token
    
    Authentication: Refresh token required (in Authorization header)
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        HTTP 200: Logout successful
        {
            "message": "Logged out (refresh revoked)"
        }
        
    """
    payload = get_jwt()  # this is the *refresh* token payload
    block_token(payload["jti"], payload["exp"])
    return jsonify({"message": "Logged out (refresh revoked)"}), 200


@bp.post("/logout-access")
@jwt_required()
@handle_errors("revoking access token")
def logout_access():
    """
    Revoke current access token
    
    Authentication: Access token required (in Authorization header)
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        HTTP 200: Access token revoked successfully
        {
            "message": "Access token revoked"
        }
    """
    payload = get_jwt()  # this is the *access* token payload
    block_token(payload["jti"], payload["exp"])
    return jsonify({"message": "Access token revoked"}), 200

#admin user endpoints

@bp.get("/<int:user_id>")
@admin_only
@handle_errors("getting user")
def get_user(user_id: int):
    """
    Get a user by ID
    
    URL Parameters:
        user_id (int): The ID of the user to retrieve
    """
    user = user_service.get_user_by_id(user_id)
    return jsonify(UserReadSchema().dump(user)), 200

@bp.put("/<int:user_id>")
@jwt_required()
@owner_or_admin_required()
@handle_errors("updating user", handle_validation=True)
def update_user(user_id: int):
    """
    Update a user by ID
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only update their own profile
    """
    data = UserUpdateSchema().load(request.get_json() or {})
    user = user_service.update_user(user_id, data)
    return jsonify(UserReadSchema().dump(user)), 200

@bp.delete("/<int:user_id>")
@jwt_required()
@owner_or_admin_required()
@handle_errors("deleting user")
def delete_user(user_id: int):
    """
    Delete a user by ID
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only delete their own account
    """
    user = user_service.delete_user(user_id)
    return jsonify(UserReadSchema().dump(user)), 200

@bp.post("/<int:user_id>/make-admin")
@admin_only
@handle_errors("making user admin")
def make_admin(user_id):
    """
    Promote a user to admin role (Admin only)
    
    URL Parameters:
        user_id (int): The ID of the user to promote to admin
        
    Authentication: JWT token with admin role required
    
    Returns:
        HTTP 200: User promoted to admin successfully
        {
            "id": 2,
            "email": "user@example.com",
            "name": "John Doe",
            "phone": "+1234567890",
            "role": "admin"
        }
        
    """
    user = user_service.get_user_by_id(user_id)
    if user.role == 'admin':
        return json_error("User is already an admin. Please use a different user.", 400)
    user_service.update_user(user_id, {"role": "admin"})
    return jsonify(UserReadSchema().dump(user)), 200


#delivery address endpoints
@bp.post("/<int:user_id>/delivery-addresses")
@jwt_required()
@delivery_address_access_required()
@handle_errors("adding delivery address", handle_validation=True)
def add_delivery_address(user_id: int):
    """
    Add a delivery address to a user
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only add addresses to their own account
    """
    data = DeliveryAddressCreateSchema().load(request.get_json() or {})
    address = delivery_address_service.add_delivery_address(user_id, data)
    return jsonify(DeliveryAddressReadSchema().dump(address)), 201

@bp.get("/<int:user_id>/delivery-addresses")
@jwt_required()
@delivery_address_access_required()
@handle_errors("getting delivery addresses")
def get_delivery_addresses(user_id: int):
    """
    Get all delivery addresses for a user
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only access their own addresses
    """
    addresses = delivery_address_service.get_delivery_addresses_by_user_id(user_id)
    return jsonify(DeliveryAddressReadSchema().dump(addresses, many=True)), 200

@bp.put("/<int:user_id>/delivery-addresses/<int:delivery_address_id>")
@jwt_required()
@delivery_address_access_required()
@handle_errors("updating delivery address", handle_validation=True)
def update_delivery_address(user_id: int, delivery_address_id: int):
    """
    Update a delivery address for a user
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only update their own addresses
    """
    data = DeliveryAddressUpdateSchema().load(request.get_json() or {})
    updated_address = delivery_address_service.update_delivery_address(delivery_address_id, data)
    
    # Return all delivery addresses for the user (as expected by tests)
    addresses = delivery_address_service.get_delivery_addresses_by_user_id(user_id)
    return jsonify(DeliveryAddressReadSchema().dump(addresses, many=True)), 200

@bp.delete("/<int:user_id>/delivery-addresses/<int:delivery_address_id>")
@jwt_required()
@delivery_address_access_required()
@handle_errors("deleting delivery address")
def delete_delivery_address(user_id: int, delivery_address_id: int):
    """
    Delete a delivery address for a user
    
    Authentication: JWT token required (admin or customer)
    Authorization: Customers can only delete their own addresses
    """
    address = delivery_address_service.delete_delivery_address(delivery_address_id)
    return jsonify(DeliveryAddressReadSchema().dump(address)), 200


