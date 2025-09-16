from flask import Flask
from db import DB_Manager, JWT_Manager
from config import get_jwt_config, print_config_info
from cache_manager import CacheManager
import os
from dotenv import load_dotenv

# Import blueprints
from api.basic import basic_bp
from api.auth import auth_bp, init_auth_bp
from api.products import products_bp, init_products_bp
from api.invoices import invoices_bp, init_invoices_bp

app = Flask(__name__)

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

cache_manager = CacheManager(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD
)

# Initialize database and JWT managers
db_manager = DB_Manager()

# Get JWT configuration and initialize manager
jwt_config = get_jwt_config()
jwt_manager = JWT_Manager(**jwt_config)

# Initialize blueprints with managers
init_auth_bp(db_manager, jwt_manager)
init_products_bp(db_manager, cache_manager)
init_invoices_bp(db_manager)

# Register blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(invoices_bp)

# Print configuration info on startup
print_config_info()

if __name__ == "__main__":
    try:
        db_manager.drop_and_create_tables()
        db_manager.populate_tables()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    app.run(host="localhost", port=3001, debug=True)