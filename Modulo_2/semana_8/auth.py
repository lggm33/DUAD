from flask import request, Response
from functools import wraps
from db import DB_Manager, JWT_Manager
from config import get_jwt_config
import jwt

# Initialize database and JWT managers
db_manager = DB_Manager()
jwt_config = get_jwt_config()
jwt_manager = JWT_Manager(**jwt_config)

def require_auth(required_roles=None):
    """
    Unified decorator that requires authentication and optionally specific roles.
    
    Args:
        required_roles: None (any authenticated user), string (single role), 
                       or list of strings (multiple roles)
    
    Usage:
        @require_auth()  # Any authenticated user
        @require_auth('admin')  # Admin role only
        @require_auth(['admin', 'user'])  # Admin or user role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get token from Authorization header
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    return Response(status=401, response="Authorization header is required")
                
                # Extract token from "Bearer <token>" format
                if not auth_header.startswith('Bearer '):
                    return Response(status=401, response="Authorization header must start with 'Bearer '")
                
                token = auth_header.replace("Bearer ", "")
                
                # Decode and validate token
                decoded = jwt_manager.decode(token)
                if decoded is None:
                    return Response(status=401, response="Invalid or expired token")
                
                # Extract user information from token (no DB query needed)
                user_id = decoded.get('id')
                username = decoded.get('username')
                role = decoded.get('role')
                
                if not user_id or not username or not role:
                    return Response(status=401, response="Invalid token payload")
                
                # Add current user info to function kwargs
                kwargs['current_user'] = {
                    'id': user_id,
                    'username': username,
                    'role': role
                }
                
                # Check role requirements if specified
                if required_roles is not None:
                    roles_list = required_roles
                    if isinstance(required_roles, str):
                        roles_list = [required_roles]
                    
                    if role not in roles_list:
                        return Response(
                            status=403, 
                            response=f"Access denied. Required roles: {', '.join(roles_list)}"
                        )
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return Response(status=401, response="Token has expired")
            except jwt.InvalidTokenError:
                return Response(status=401, response="Invalid token")
            except Exception as e:
                return Response(status=500, response=f"Internal server error on authentication: {e}")
        
        return decorated_function
    return decorator 