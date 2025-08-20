from functools import wraps
from flask import jsonify
import inspect

def cached_response(cache_key_func, ttl=600, debug_name=None):
    """
    Decorator for caching GET endpoint responses
    
    Args:
        cache_key_func: Function that generates cache key from endpoint args
        ttl: Time to live in seconds (default 600)
        debug_name: Name for debug messages (optional)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache_manager from global scope
            cache_manager = None
            frame = inspect.currentframe()
            try:
                # Look for cache_manager in caller's globals
                caller_globals = frame.f_back.f_globals
                cache_manager = caller_globals.get('cache_manager')
            finally:
                del frame
            
            if not cache_manager:
                # If no cache manager, just execute function normally
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_data = cache_manager.get_data(cache_key)
            if cached_data:
                if debug_name:
                    print(f"{debug_name} found in cache")
                # Assuming the cached data is already in the right format
                if isinstance(cached_data, dict) and len(cached_data) == 1:
                    # Single item response like {"product": data}
                    return jsonify(cached_data)
                else:
                    # Multiple items response, need to determine wrapper key
                    wrapper_key = list(cached_data.keys())[0] if isinstance(cached_data, dict) else 'data'
                    return jsonify({wrapper_key: cached_data})
            
            # Execute original function
            result = func(*args, **kwargs)
            
            # Cache the result if it's successful
            if hasattr(result, 'status_code') and result.status_code == 200:
                try:
                    # Extract data from JSON response to cache
                    result_data = result.get_json()
                    if result_data:
                        cache_manager.store_data(cache_key, result_data, ttl)
                except:
                    pass  # If we can't cache, just continue
            
            return result
        return wrapper
    return decorator

def invalidate_cache(*cache_keys_funcs):
    """
    Decorator for invalidating cache after endpoint execution
    
    Args:
        cache_keys_funcs: Functions that generate cache keys to invalidate
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute original function first
            result = func(*args, **kwargs)
            
            # Get cache_manager from global scope
            cache_manager = None
            frame = inspect.currentframe()
            try:
                # Look for cache_manager in caller's globals
                caller_globals = frame.f_back.f_globals
                cache_manager = caller_globals.get('cache_manager')
            finally:
                del frame
            
            if cache_manager:
                # Invalidate specified cache keys
                for cache_key_func in cache_keys_funcs:
                    try:
                        cache_key = cache_key_func(*args, **kwargs)
                        cache_manager.delete_data(cache_key)
                    except Exception as e:
                        # Continue if cache invalidation fails
                        print(f"Cache invalidation failed for key: {e}")
            
            return result
        return wrapper
    return decorator

# Common cache key generators for products
def product_cache_key(*args, **kwargs):
    """Generate cache key for individual product"""
    # Look for product_id in kwargs or args
    product_id = kwargs.get('product_id')
    if not product_id and len(args) >= 2:  # current_user, product_id
        product_id = args[1]
    return f"product_{product_id}"

def all_products_cache_key(*args, **kwargs):
    """Generate cache key for all products"""
    return "all_products"

def product_id_from_request(*args, **kwargs):
    """Extract product_id from request data for cache invalidation"""
    from flask import request
    data = request.get_json() or {}
    product_id = data.get('product_id')
    return f"product_{product_id}" if product_id else "product_none"
