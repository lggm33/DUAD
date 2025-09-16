"""Basic connection example.
"""

import redis
import dotenv
import os

dotenv.load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(
    host='redis-10069.c245.us-east-1-3.ec2.redns.redis-cloud.com',
    port=10069,
    decode_responses=True,
    username="default",
    password="dKYqOvVoVqMBwzXYkRsfTLvaey17sggU",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar

