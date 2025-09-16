# app/services/cache_service.py
from flask import current_app
from app.extensions import cache
from typing import Optional, List

class CacheKeys:
    """Centralized cache key definitions following the repo's pattern"""
    PRODUCTS_ALL = "products.get_all"
    PRODUCT_BY_ID = "products.get_by_id"
    SALES_ANALYTICS = "admin.sales"
    CART_TOTAL = "cart.total"
    USER_ADDRESSES = "user.addresses"
    ADMIN_SALES = "admin.sales"
    ADMIN_INVOICES = "admin.invoices"

def invalidate_product_cache():
    """
    Invalidate all product-related cache entries using Redis pattern matching
    Following the repo's error handling pattern with try/catch and print
    """
    try:
        # Clear products list cache
        cache.delete(CacheKeys.PRODUCTS_ALL)
        
        # Use Redis pattern matching to clear all product-related keys
        redis_client = cache.cache._write_client
        # Flask-Caching adds 'flask_cache_' prefix to all keys
        flask_cache_prefix = cache.cache._get_prefix()
        product_pattern = f"{flask_cache_prefix}{CacheKeys.PRODUCT_BY_ID}*"
        product_keys = redis_client.keys(product_pattern)
        
        if product_keys:
            redis_client.delete(*product_keys)
        
        if current_app.debug:
            print(f"🗑️  Product cache invalidated successfully ({len(product_keys)} individual product keys)")
    except Exception as e:
        # Follow repo's error handling pattern
        print(f"Error invalidating product cache: {e}")

def invalidate_user_cache(user_id: int):
    """
    Invalidate user-specific cache entries
    
    Args:
        user_id: ID of the user whose cache should be invalidated
    """
    try:
        # Clear user-specific caches
        cache.delete(f"{CacheKeys.USER_ADDRESSES}_user_{user_id}")
        cache.delete(f"{CacheKeys.CART_TOTAL}_user_{user_id}")
        
        if current_app.debug:
            print(f"🗑️  User {user_id} cache invalidated successfully")
    except Exception as e:
        print(f"Error invalidating user cache: {e}")

def invalidate_sales_cache():
    """
    Invalidate sales and analytics cache using Redis pattern matching
    """
    try:
        # Use Redis pattern matching to clear all sales-related keys
        redis_client = cache.cache._write_client
        flask_cache_prefix = cache.cache._get_prefix()
        sales_keys = redis_client.keys(f"{flask_cache_prefix}{CacheKeys.ADMIN_SALES}*")
        analytics_keys = redis_client.keys(f"{flask_cache_prefix}{CacheKeys.SALES_ANALYTICS}*")
        
        all_keys = sales_keys + analytics_keys
        if all_keys:
            redis_client.delete(*all_keys)
        
        if current_app.debug:
            print(f"🗑️  Sales cache invalidated successfully ({len(all_keys)} keys)")
    except Exception as e:
        print(f"Error invalidating sales cache: {e}")

def invalidate_all_cache():
    """
    Nuclear option - clear all cache
    Use sparingly, mainly for testing or emergency situations
    """
    try:
        cache.clear()
        if current_app.debug:
            print("💥 ALL cache cleared")
    except Exception as e:
        print(f"Error clearing all cache: {e}")

def get_cache_stats():
    """
    Get cache statistics for monitoring (development helper)
    """
    try:
        if current_app.debug:
            redis_client = cache.cache._write_client
            info = redis_client.info()
            
            cache_info = {
                "cache_type": "Redis",
                "backend": "RedisCache",
                "default_timeout": cache.config.get('CACHE_DEFAULT_TIMEOUT', 'N/A'),
                "redis_version": info.get('redis_version', 'Unknown'),
                "used_memory_human": info.get('used_memory_human', 'Unknown'),
                "connected_clients": info.get('connected_clients', 'Unknown'),
                "total_keys": redis_client.dbsize()
            }
            
            return cache_info
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return {"error": str(e)}
