from functools import wraps
from flask import request, g
from app.utils.jwt_service import JwtService, JwtError
from app.config import get_settings
from app.domain.auth.models import AuthUser
from app.presentation.common.errors import error_response

def auth_required(f):
    """
    Decorator to protect endpoints with JWT authentication.
    
    Expects 'Authorization: Bearer <token>' header.
    Populates g.auth_user with a AuthUser object if successful.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return error_response("MISSING_AUTH_HEADER", "Authorization header is required", status_code=401)
        
        if not auth_header.startswith("Bearer "):
            return error_response("INVALID_AUTH_HEADER", "Invalid Authorization header format. Expected 'Bearer <token>'", status_code=401)
        
        token = auth_header.split(" ")[1]
        
        settings = get_settings()
        jwt_service = JwtService(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token_expires=settings.jwt_access_token_expires
        )
        
        try:
            claims = jwt_service.verify(token)
            g.auth_user = AuthUser(
                user_id=int(claims["sub"]),
                role=claims["role"]
            )
        except JwtError as e:
            # Errors like JwtExpiredError or JwtInvalidError are handled by 
            # global error handlers if we reraise them, but for the middleware 
            # we want to return a direct 401. 
            # Actually, if we reraise them, the global error handler in app/__init__.py
            # will catch them. Let's reraise to keep it consistent.
            raise e
            
        return f(*args, **kwargs)
    
    return decorated

def roles_required(*allowed_roles):
    """
    Decorator que requiere autenticación + alguno de los roles especificados.
    
    Uso:
        @roles_required("ADMIN", "DM")  -> Admin O DM pueden acceder
        @roles_required("ADMIN")        -> Solo Admin
    """
    def decorator(f):
        @wraps(f)
        @auth_required  # Primero autentica
        def decorated(*args, **kwargs):
            if g.auth_user.role not in allowed_roles:
                return error_response(
                    "UNAUTHORIZED", 
                    f"Requires one of: {', '.join(allowed_roles)}", 
                    status_code=403
                )
            return f(*args, **kwargs)
        return decorated
    return decorator