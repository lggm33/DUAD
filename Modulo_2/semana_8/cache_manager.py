"""Basic connection example.
"""

import redis
import json

class CacheManager:
    def __init__(self, host, port, password, *args, **kwargs):
        self.redis_client = redis.Redis(
            host=host,
            port=int(port) if port else 6379,
            decode_responses=True,
            username="default",  # Required for Redis Cloud
            password=password,
            *args,
            **kwargs,
        )
        connection_status = self.redis_client.ping()
        if connection_status:
            print("✅ Redis connection created successfully")
        else:
            print("❌ Redis connection failed")
            raise Exception("Redis connection failed")

    def store_data(self, key, value, time_to_live=None):
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if time_to_live is None:
                self.redis_client.set(key, value)
            else:
                self.redis_client.setex(key, time_to_live, value)
        except redis.RedisError as error:
            print(f"An error ocurred while storing data in Redis: {error}")
        except (TypeError, ValueError) as error:
            print(f"An error ocurred while serializing data for Redis: {error}")

    def check_key(self, key):
        try:
            key_exists = self.redis_client.exists(key)
            if key_exists:
                ttl = self.redis_client.ttl(key)
                return True, ttl

            return False, None
        except redis.RedisError as error:
            print(f"An error ocurred while checking a key in Redis: {error}")
            return False, None

    def get_data(self, key):
        try:
            output = self.redis_client.get(key)
            if output is not None:
                # Try to deserialize JSON, fall back to original string if it fails
                try:
                    return json.loads(output)
                except (json.JSONDecodeError, TypeError):
                    return output  # Return as string if not valid JSON
            else:
                return None
        except redis.RedisError as error:
            print(f"An error ocurred while retrieving data from Redis: {error}")
            return None

    def delete_data(self, key):
        try:
            output = self.redis_client.delete(key)
            return output == 1
        except redis.RedisError as error:
            print(f"An error ocurred while deleting data from Redis: {error}")
            return False

    def delete_data_with_pattern(self, pattern):
        try:
            # Iterar sobre las claves que coinciden con el patrón
            for key in self.redis_client.scan_iter(match=pattern):
                self.delete_data(key)
        except redis.RedisError as error:
            print(f"An error ocurred while deleting data from Redis: {error}")