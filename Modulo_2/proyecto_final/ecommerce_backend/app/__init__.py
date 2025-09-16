# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import init_extensions
from .api.user import bp as users_bp

# from .extensions import jwt

def create_app(config=None):
    app = Flask(__name__)
    
    if config:
        app.config.update(config)
    else:
        app.config.from_object(Config)

    init_extensions(app)

    # Import models after extensions are initialized to avoid circular imports
    from . import models

    # Register blueprints
    app.register_blueprint(users_bp)
    
    # Import and register other blueprints
    from .api.products import bp as products_bp
    from .api.sales import bp as sales_bp
    app.register_blueprint(products_bp)
    app.register_blueprint(sales_bp)
    
    from .security import jwt_handlers, jwt_blocklist_check

    # later: register_blueprints(app), error handlers, etc.
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
