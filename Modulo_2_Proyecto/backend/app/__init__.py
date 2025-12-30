from flask import Flask

from app.api.health_routes import health_bp
from app.api.auth_routes import auth_bp
from app.api.user_routes import user_bp
from app.api.game_routes import game_bp

from app.config import get_settings
from app.extensions import db, redis_client


def create_app() -> Flask:
    settings = get_settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["APP_ENV"] = settings.env.value
    app.config["DEBUG"] = settings.debug

    db.init_app(app, settings)
    redis_client.init_app(app, settings)

    # Register Blueprints
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(game_bp)
    _register_error_handlers(app)

    return app


def _register_error_handlers(app: Flask) -> None:
    from werkzeug.exceptions import BadRequest, HTTPException
    from sqlalchemy.exc import IntegrityError
    from app.domain.auth.auth_service import (
        AuthError, 
        EmailAlreadyExistsError, 
        UsernameAlreadyExistsError,
        InvalidCredentialsError, 
        TokenInvalidError
    )
    from app.utils.jwt_service import JwtExpiredError, JwtInvalidError
    from app.presentation.common.errors import error_response

    @app.errorhandler(EmailAlreadyExistsError)
    def handle_email_exists(e):
        return error_response("EMAIL_ALREADY_EXISTS", str(e), status_code=409)

    @app.errorhandler(UsernameAlreadyExistsError)
    def handle_username_exists(e):
        return error_response("USERNAME_ALREADY_EXISTS", str(e), status_code=409)

    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_credentials(e):
        return error_response("INVALID_CREDENTIALS", str(e), status_code=401)

    @app.errorhandler(TokenInvalidError)
    def handle_token_invalid(e):
        return error_response("INVALID_TOKEN", str(e), status_code=401)

    @app.errorhandler(AuthError)
    def handle_auth_error(e):
        return error_response("AUTH_ERROR", str(e), status_code=400)

    @app.errorhandler(JwtExpiredError)
    def handle_jwt_expired(e):
        return error_response("TOKEN_EXPIRED", str(e), status_code=401)

    @app.errorhandler(JwtInvalidError)
    def handle_jwt_invalid(e):
        return error_response("INVALID_TOKEN", str(e), status_code=401)

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return error_response("BAD_REQUEST", "Invalid request body or malformed JSON", status_code=400)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        # Log the error here if necessary
        return error_response("DATABASE_ERROR", "A database integrity error occurred", status_code=409)

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response("NOT_FOUND", "Resource not found", status_code=404)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return error_response(e.name.upper().replace(" ", "_"), e.description, status_code=e.code)

    @app.errorhandler(Exception)
    def handle_server_error(e):
        # In production, you would log this error
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred", status_code=500)


