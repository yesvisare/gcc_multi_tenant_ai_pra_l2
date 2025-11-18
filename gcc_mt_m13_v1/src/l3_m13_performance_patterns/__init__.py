"""
L3 M13.1: Multi-Tenant Performance Patterns

This module implements tenant-scoped caching with Redis namespace isolation
and performance tier enforcement for multi-tenant RAG systems.

Key capabilities:
- Tenant-scoped Redis caching with namespace isolation
- Performance tier enforcement (Platinum/Gold/Silver SLAs)
- Query timeout mechanisms per tier
- Scoped cache invalidation
- Hot tenant detection and monitoring
"""

import hashlib
import json
import logging
import time
from typing import Optional, Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

__all__ = [
    "TenantCache",
    "PerformanceTier",
    "RateLimitedQuery",
    "calculate_cache_hit_rate",
    "detect_hot_tenants"
]


class TenantCache:
    """
    Tenant-scoped Redis cache with namespace isolation.

    Each tenant gets a unique cache namespace (cache:tenant_id:*) ensuring:
    - Zero cross-tenant cache pollution
    - Tenant-scoped eviction (A's eviction doesn't affect B)
    - Surgical cache invalidation (clear only affected tenant)
    - Per-tenant monitoring and chargeback

    Performance tier integration:
    - Platinum: 1-hour TTL, strict timeout
    - Gold: 30-min TTL, moderate timeout
    - Silver: 15-min TTL, loose timeout
    """

    def __init__(
        self,
        tenant_id: str,
        tier: str,
        redis_client: Optional[Any] = None,
        default_ttl: int = 3600,
        quota_gb: float = 10.0
    ):
        """
        Initialize tenant-scoped cache.

        Args:
            tenant_id: Unique tenant identifier (UUID)
            tier: Performance tier ('platinum', 'gold', 'silver')
            redis_client: Async Redis connection (optional for offline mode)
            default_ttl: Default TTL in seconds (overridden by tier config)
            quota_gb: Cache quota in GB for this tenant
        """
        self.tenant_id = tenant_id
        self.tier = tier
        self.redis = redis_client
        self.quota_gb = quota_gb

        # Namespace prefix for all this tenant's cache keys
        # Example: cache:tenant_abc123:
        self.prefix = f"cache:{tenant_id}:"

        # Performance tier configuration
        # Platinum gets longer TTL (fewer misses) and stricter timeout
        self.tier_config = {
            'platinum': {'ttl': 3600, 'timeout_ms': 200},
            'gold': {'ttl': 1800, 'timeout_ms': 500},
            'silver': {'ttl': 900, 'timeout_ms': 1000}
        }

        # Get tier-specific settings
        self.ttl = self.tier_config.get(tier, {}).get('ttl', default_ttl)
        self.timeout_ms = self.tier_config.get(tier, {}).get('timeout_ms', 1000)

        logger.info(f"Initialized TenantCache for {tenant_id}, tier={tier}, ttl={self.ttl}s")

    def _make_key(self, key: str) -> str:
        """
        Create namespaced cache key.

        Args:
            key: User-provided cache key (query hash, document ID, etc.)

        Returns:
            Full Redis key with tenant namespace

        Example:
            Input: "query_abc123"
            Output: "cache:tenant_abc123:query_abc123"
        """
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from tenant-scoped cache.

        Args:
            key: Cache key (without namespace prefix)

        Returns:
            Cached value (deserialized from JSON) or None if miss

        Monitoring:
            - Increments cache_hits or cache_misses counter
            - Tags with tenant_id and tier for per-tenant tracking
        """
        if self.redis is None:
            logger.warning("⚠️ Redis not configured - cache disabled")
            return None

        full_key = self._make_key(key)

        try:
            # Async Redis get with namespace isolation
            # Even if another tenant has same key, different namespace prevents collision
            value = await self.redis.get(full_key)

            if value is not None:
                logger.debug(f"Cache HIT for {self.tenant_id}: {key}")
                # Deserialize JSON value
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS for {self.tenant_id}: {key}")
                return None

        except Exception as e:
            # Redis errors should not crash queries
            # Log error, return None (fallback to source)
            logger.error(f"Error reading cache for {self.tenant_id}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store value in tenant-scoped cache.

        Args:
            key: Cache key (without namespace prefix)
            value: Value to cache (will be JSON-serialized)
            ttl: Time-to-live in seconds (defaults to tier-specific TTL)

        Returns:
            True if set succeeded, False otherwise

        Tier-specific TTL ensures:
            - Platinum tenants: Long TTL (1 hour) = fewer backend queries
            - Silver tenants: Short TTL (15 min) = less memory consumed
        """
        if self.redis is None:
            logger.warning("⚠️ Redis not configured - cache disabled")
            return False

        full_key = self._make_key(key)
        ttl = ttl or self.ttl  # Use tier-specific TTL if not provided

        try:
            # Check quota before writing
            current_size = await self.get_cache_size()
            if current_size['size_gb'] > self.quota_gb * 0.9:
                logger.warning(f"Tenant {self.tenant_id} near cache quota ({self.quota_gb}GB)")
                # Could reject write here to enforce quota

            # Serialize value to JSON
            serialized = json.dumps(value)

            # Store with TTL (Redis SETEX command)
            # Key automatically expires after TTL seconds
            await self.redis.setex(full_key, ttl, serialized)

            logger.debug(f"Cache SET for {self.tenant_id}: {key}, ttl={ttl}s")
            return True

        except Exception as e:
            logger.error(f"Error setting cache for {self.tenant_id}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete specific cache entry for this tenant.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        if self.redis is None:
            return False

        full_key = self._make_key(key)

        try:
            result = await self.redis.delete(full_key)
            return result > 0  # Redis returns number of keys deleted

        except Exception as e:
            logger.error(f"Error deleting cache key for {self.tenant_id}: {e}")
            return False

    async def invalidate_tenant(self) -> int:
        """
        Clear ALL cache entries for this tenant.

        Use cases:
            - Tenant updates document corpus (need fresh embeddings)
            - Tenant changes configuration (need re-computed results)
            - Tenant requests cache clear via API

        Returns:
            Number of keys deleted

        CRITICAL: This only affects THIS tenant's namespace.
                  Other tenants' cache remains intact.
        """
        if self.redis is None:
            return 0

        # Pattern matches all keys in this tenant's namespace
        pattern = f"{self.prefix}*"

        try:
            # Get all keys matching pattern
            # SCAN is cursor-based, doesn't block Redis
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                # Delete all matched keys in single command
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} keys for {self.tenant_id}")
                return deleted
            else:
                return 0

        except Exception as e:
            logger.error(f"Error invalidating cache for {self.tenant_id}: {e}")
            return 0

    async def get_cache_size(self) -> Dict[str, Any]:
        """
        Calculate cache size for this tenant.

        Returns:
            Dict with:
                - num_keys: Number of cache entries
                - size_bytes: Approximate memory used (sum of value sizes)
                - size_mb: Memory in MB
                - size_gb: Memory in GB

        Used for:
            - Hot tenant detection (>30% of total cache)
            - Chargeback billing (charge per GB cached)
            - Capacity planning (predict when Redis will fill)
        """
        if self.redis is None:
            return {'tenant_id': self.tenant_id, 'num_keys': 0, 'size_bytes': 0, 'size_mb': 0, 'size_gb': 0}

        pattern = f"{self.prefix}*"

        try:
            num_keys = 0
            total_size = 0

            # Iterate through all tenant keys
            async for key in self.redis.scan_iter(match=pattern, count=100):
                num_keys += 1

                # Get value size (STRLEN command for byte count)
                size = await self.redis.strlen(key)
                total_size += size

            return {
                'tenant_id': self.tenant_id,
                'num_keys': num_keys,
                'size_bytes': total_size,
                'size_mb': round(total_size / (1024 * 1024), 2),
                'size_gb': round(total_size / (1024 * 1024 * 1024), 4)
            }

        except Exception as e:
            logger.error(f"Error calculating cache size for {self.tenant_id}: {e}")
            return {'tenant_id': self.tenant_id, 'num_keys': 0, 'size_bytes': 0, 'size_mb': 0, 'size_gb': 0}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics for this tenant.

        Returns:
            Dict with:
                - hit_rate: Cache hit rate (0.0 to 1.0)
                - num_keys: Number of cached entries
                - size_mb: Memory used in MB
                - ttl: Tier-specific TTL setting
                - tier: Performance tier

        Used for:
            - Per-tenant performance reports
            - Identifying tenants needing optimization
            - Capacity planning and forecasting
        """
        size_info = await self.get_cache_size()

        return {
            'tenant_id': self.tenant_id,
            'tier': self.tier,
            'ttl_seconds': self.ttl,
            'timeout_ms': self.timeout_ms,
            'num_keys': size_info['num_keys'],
            'size_mb': size_info['size_mb'],
            'size_gb': size_info['size_gb'],
            'quota_gb': self.quota_gb,
            'note': 'Query Prometheus for actual hit rate over time window'
        }


class PerformanceTier:
    """
    Performance tier management with SLA enforcement.

    Manages:
    - Tier definitions (Platinum/Gold/Silver)
    - Timeout enforcement per tier
    - Tenant tier lookup from database
    """

    TIERS = {
        'platinum': {
            'timeout_ms': 200,
            'cache_ttl': 3600,
            'qps_limit': 1000,
            'price_per_month': 15000  # ₹15K/month
        },
        'gold': {
            'timeout_ms': 500,
            'cache_ttl': 1800,
            'qps_limit': 500,
            'price_per_month': 8000  # ₹8K/month
        },
        'silver': {
            'timeout_ms': 1000,
            'cache_ttl': 900,
            'qps_limit': 200,
            'price_per_month': 5000  # ₹5K/month
        }
    }

    @classmethod
    def get_tenant_config(cls, tier: str) -> Dict[str, Any]:
        """
        Get configuration for a performance tier.

        Args:
            tier: Tier name ('platinum', 'gold', 'silver')

        Returns:
            Dict with tier configuration
        """
        return cls.TIERS.get(tier.lower(), cls.TIERS['silver'])

    @classmethod
    def get_timeout_seconds(cls, tier: str) -> float:
        """
        Get timeout in seconds for a tier.

        Args:
            tier: Tier name

        Returns:
            Timeout in seconds (200ms -> 0.2, 500ms -> 0.5, etc.)
        """
        config = cls.get_tenant_config(tier)
        return config['timeout_ms'] / 1000.0

    @classmethod
    async def enforce_sla(cls, tier: str, query_func, *args, **kwargs):
        """
        Execute query with tier-specific timeout enforcement.

        Args:
            tier: Performance tier
            query_func: Async function to execute
            *args, **kwargs: Arguments for query_func

        Returns:
            Query result

        Raises:
            asyncio.TimeoutError: If query exceeds tier SLA
        """
        timeout = cls.get_timeout_seconds(tier)

        try:
            result = await asyncio.wait_for(
                query_func(*args, **kwargs),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Query timeout for tier {tier} (>{timeout}s)")
            raise


class RateLimitedQuery:
    """
    Per-tenant rate limiting to prevent resource monopolization.

    Prevents hot tenants from saturating platform resources.
    """

    def __init__(self):
        """Initialize rate limiters for each tier."""
        # Note: In production, use aiolimiter or similar
        # Here we show the concept
        self.limiters = {
            'platinum': {'max_qps': 1000, 'current_qps': 0},
            'gold': {'max_qps': 500, 'current_qps': 0},
            'silver': {'max_qps': 200, 'current_qps': 0}
        }
        self.last_reset = time.time()

    async def check_rate_limit(self, tenant_id: str, tier: str) -> bool:
        """
        Check if tenant is within rate limit.

        Args:
            tenant_id: Tenant identifier
            tier: Performance tier

        Returns:
            True if within limit, False if exceeded
        """
        # Reset counters every second
        now = time.time()
        if now - self.last_reset >= 1.0:
            for limiter in self.limiters.values():
                limiter['current_qps'] = 0
            self.last_reset = now

        limiter = self.limiters.get(tier.lower())
        if limiter is None:
            return True

        if limiter['current_qps'] >= limiter['max_qps']:
            logger.warning(f"Rate limit exceeded for {tenant_id} (tier={tier})")
            return False

        limiter['current_qps'] += 1
        return True


def calculate_cache_hit_rate(hits: int, misses: int) -> float:
    """
    Calculate cache hit rate.

    Args:
        hits: Number of cache hits
        misses: Number of cache misses

    Returns:
        Hit rate as float (0.0 to 1.0)
    """
    total = hits + misses
    if total == 0:
        return 0.0
    return hits / total


def detect_hot_tenants(
    tenant_sizes: Dict[str, float],
    threshold_percent: float = 30.0
) -> List[str]:
    """
    Detect tenants consuming excessive cache resources.

    Args:
        tenant_sizes: Dict mapping tenant_id to cache size (GB)
        threshold_percent: Threshold for hot tenant (default 30%)

    Returns:
        List of tenant IDs exceeding threshold
    """
    total_size = sum(tenant_sizes.values())
    if total_size == 0:
        return []

    hot_tenants = []
    for tenant_id, size in tenant_sizes.items():
        percent = (size / total_size) * 100
        if percent >= threshold_percent:
            hot_tenants.append(tenant_id)
            logger.warning(f"Hot tenant detected: {tenant_id} using {percent:.1f}% of cache")

    return hot_tenants


def hash_query(query: str) -> str:
    """
    Generate consistent hash for query string.

    Args:
        query: Query string

    Returns:
        Hash string (hex digest)
    """
    return hashlib.sha256(query.encode()).hexdigest()[:16]
