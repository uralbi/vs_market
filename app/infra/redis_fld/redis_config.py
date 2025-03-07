import redis.asyncio as redis
import asyncio

REDIS_URL = "redis://localhost:6377"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_redis_eviction_policy():
    """Fetch the current Redis eviction policy."""
    policy = await redis_client.config_get("maxmemory-policy")
    return policy.get("maxmemory-policy", "noeviction") 

async def set_eviction_policy(policy: str):
    """Set Redis maxmemory-policy dynamically."""
    try:
        await redis_client.config_set("maxmemory-policy", policy)
        print(f"Redis eviction policy set to: {policy}")
    except Exception as e:
        print(f"Failed to set eviction policy: {e}")
