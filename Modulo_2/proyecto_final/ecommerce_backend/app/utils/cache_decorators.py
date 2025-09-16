from functools import wraps
from flask import request, current_app
from flask_jwt_extended import get_jwt_identity
from app.extensions import cache
from app.utils.exceptions import AppError

def cached_response(timeout=300, key_prefix=None, include_user=False):
    """
    Cache decorator that follows the repo's error handling pattern
    
    Args:
        timeout: Cache TTL in seconds
        key_prefix: Custom prefix for cache key
        include_user: Include user_id in cache key for user-specific caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Build cache key
                cache_key = key_prefix or f"{func.__module__}.{func.__name__}"
                
                # Add URL parameters to key
                if request.args:
                    cache_key += f"_args_{hash(frozenset(request.args.items()))}"
                
                # Add user ID if requested
                if include_user:
                    try:
                        user_id = get_jwt_identity()
                        if user_id:
                            cache_key += f"_user_{user_id}"
                    except:
                        pass  # No JWT context, continue without user
                
                # Add function arguments to key
                if args or kwargs:
                    cache_key += f"_params_{hash((args, frozenset(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    # Print cache hit info in development
                    if current_app.debug:
                        print(f"🚀 CACHE HIT: {func.__name__} (key: {cache_key[:50]}...)")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                
                # Print cache miss info in development
                if current_app.debug:
                    print(f"💾 CACHE MISS: {func.__name__} - Cached for {timeout}s (key: {cache_key[:50]}...)")
                
                return result
                
            except Exception as e:
                # Follow repo's error handling pattern
                print(f"Cache error in {func.__name__}: {e}")
                # Fallback to executing function without cache
                if current_app.debug:
                    print(f"⚠️  CACHE ERROR: {func.__name__} - Falling back to direct execution")
                return func(*args, **kwargs)
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """
    Invalidate cache entries matching a pattern using Redis
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Invalidate cache after successful operation using Redis pattern matching
                redis_client = cache.cache._write_client
                keys_to_delete = redis_client.keys(f"{pattern}*")
                if keys_to_delete:
                    redis_client.delete(*keys_to_delete)
                
                if current_app.debug:
                    print(f"🗑️  CACHE INVALIDATED: Pattern '{pattern}' ({len(keys_to_delete)} keys) after {func.__name__}")
                return result
            except Exception:
                # Don't invalidate cache if operation failed
                raise
        return wrapper
    return decorator
