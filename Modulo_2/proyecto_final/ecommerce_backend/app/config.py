# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # carga .env si existe

def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache Configuration - Use Redis for both development and production
    CACHE_TYPE = "RedisCache"  # Always use Redis for consistency
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))  # 5 minutes
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DECODE_RESPONSES = os.getenv("REDIS_DECODE_RESPONSES", "True").lower() == "true"
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    
    # Redis URL for Flask-Caching
    CACHE_REDIS_HOST = REDIS_HOST
    CACHE_REDIS_PORT = REDIS_PORT
    CACHE_REDIS_PASSWORD = REDIS_PASSWORD
    CACHE_REDIS_USERNAME = REDIS_USERNAME

    
    JWT_ALGORITHM = "RS256"
    # Prioridad a variables de entorno (por si las inyectas en prod)
    JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY") or _read_file(os.getenv("JWT_PRIVATE_KEY_FILE", "keys/private_key.pem"))
    JWT_PUBLIC_KEY  = os.getenv("JWT_PUBLIC_KEY")  or _read_file(os.getenv("JWT_PUBLIC_KEY_FILE",  "keys/public_key.pem"))

    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 15 * 60))  # 15 min
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 7 * 24 * 3600))  # 7 días
    
