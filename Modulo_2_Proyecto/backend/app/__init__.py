from flask import Flask

from app.api.health_routes import health_bp
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

    app.register_blueprint(health_bp)

    return app


