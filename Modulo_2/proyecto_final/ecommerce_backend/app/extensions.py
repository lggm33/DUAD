# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate(compare_type=True, compare_server_default=True)
jwt = JWTManager()
cache = Cache()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
