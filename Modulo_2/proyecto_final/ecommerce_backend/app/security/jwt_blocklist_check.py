from app.extensions import jwt
from app.security.blocklist import is_token_blocked

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    return is_token_blocked(jti)