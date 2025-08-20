from flask import Blueprint, request, jsonify, Response
from db import DB_Manager
from config import get_jwt_config
from auth import require_auth

# Create blueprint for authentication endpoints
auth_bp = Blueprint('auth', __name__)

# Initialize managers (will be passed from main)
db_manager = None
jwt_manager = None

def init_auth_bp(db_mgr, jwt_mgr):
    """Initialize the auth blueprint with managers"""
    global db_manager, jwt_manager
    db_manager = db_mgr
    jwt_manager = jwt_mgr

@auth_bp.route('/login', methods=['POST'])
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

@auth_bp.route('/register', methods=['POST'])
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

@auth_bp.route('/me', methods=['GET'])
@require_auth()
def me(current_user):
    """Get current user information - requires valid token"""
    return jsonify(
        id=current_user['id'],
        username=current_user['username'],
        role=current_user['role']
    )
