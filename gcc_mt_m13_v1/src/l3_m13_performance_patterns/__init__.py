"""
L3 M13.1: Multi-Tenant Performance Patterns

This module implements performance isolation for multi-tenant RAG systems using
Redis namespace patterns, performance tier enforcement, and scoped cache management.

Key Components:
- TenantCache: Redis namespace isolation wrapper
- PerformanceTierEnforcer: SLA enforcement with timeouts
- Per-tenant monitoring and metrics
"""

import hashlib
import json
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    "TenantCache",
    "PerformanceTier",
    "PerformanceTierEnforcer",
    "CacheMetrics",
    "QuotaExceededError",
    "TierViolationError",
    "generate_query_hash",
    "get_tenant_tier_config"
]


# ============================================================================
# EXCEPTIONS
# ============================================================================

class QuotaExceededError(Exception):
    """Raised when tenant exceeds their cache quota"""
    pass


class TierViolationError(Exception):
    """Raised when query exceeds tier SLA timeout"""
    pass


# ============================================================================
# PERFORMANCE TIER CONFIGURATION
# ============================================================================

class PerformanceTier(str, Enum):
    """Performance tier enumeration"""
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"


@dataclass
class TierConfig:
    """Configuration for a performance tier"""
    timeout_ms: int
    cache_ttl: int
    max_qps: int
    cache_quota_gb: float


TIER_CONFIGS = {
    PerformanceTier.PLATINUM: TierConfig(
        timeout_ms=200,
        cache_ttl=3600,  # 1 hour
        max_qps=1000,
        cache_quota_gb=40.0
    ),
    PerformanceTier.GOLD: TierConfig(
        timeout_ms=500,
        cache_ttl=1800,  # 30 minutes
        max_qps=500,
        cache_quota_gb=20.0
    ),
    PerformanceTier.SILVER: TierConfig(
        timeout_ms=1000,
        cache_ttl=900,  # 15 minutes
        max_qps=200,
        cache_quota_gb=10.0
    )
}


def get_tenant_tier_config(tier: str) -> TierConfig:
    """
    Get configuration for a performance tier.

    Args:
        tier: Performance tier name (platinum, gold, silver)

    Returns:
        TierConfig object with tier settings

    Raises:
        ValueError: If tier is invalid
    """
    try:
        tier_enum = PerformanceTier(tier.lower())
        return TIER_CONFIGS[tier_enum]
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid tier: {tier}")
        raise ValueError(f"Invalid tier: {tier}. Must be platinum, gold, or silver") from e


# ============================================================================
# CACHE METRICS
# ============================================================================

@dataclass
class CacheMetrics:
    """Cache performance metrics for a tenant"""
    tenant_id: str
    hits: int
    misses: int
    size_bytes: int
    size_gb: float
    key_count: int
    hit_rate: float
    evictions: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "hits": self.hits,
            "misses": self.misses,
            "size_bytes": self.size_bytes,
            "size_gb": round(self.size_gb, 2),
            "key_count": self.key_count,
            "hit_rate": round(self.hit_rate, 3),
            "evictions": self.evictions
        }


# ============================================================================
# TENANT CACHE - Core isolation wrapper
# ============================================================================

class TenantCache:
    """
    Tenant-scoped Redis cache with namespace isolation.

    Provides logical isolation on shared Redis infrastructure using
    namespace prefixes (cache:tenant_id:key).

    Features:
    - Namespace isolation (prevents cross-tenant cache collisions)
    - Tier-specific TTLs
    - Quota enforcement
    - Per-tenant metrics tracking
    """

    def __init__(
        self,
        tenant_id: str,
        tier: str,
        redis_client: Optional[Any] = None,
        offline: bool = False
    ):
        """
        Initialize tenant cache.

        Args:
            tenant_id: Unique tenant identifier
            tier: Performance tier (platinum, gold, silver)
            redis_client: Async Redis client (redis.asyncio.Redis)
            offline: If True, skip Redis operations (testing mode)
        """
        self.tenant_id = tenant_id
        self.tier = tier
        self.redis = redis_client
        self.offline = offline
        self.tier_config = get_tenant_tier_config(tier)
        self.prefix = f"cache:{tenant_id}:"

        # Metrics tracking
        self._hits = 0
        self._misses = 0

        logger.info(
            f"Initialized TenantCache for tenant={tenant_id}, tier={tier}, "
            f"ttl={self.tier_config.cache_ttl}s, quota={self.tier_config.cache_quota_gb}GB"
        )

    def _make_key(self, key: str) -> str:
        """
        Create namespaced key.

        Args:
            key: Un-namespaced key

        Returns:
            Namespaced key (cache:tenant_id:key)
        """
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if miss/offline
        """
        if self.offline or not self.redis:
            logger.warning(f"Cache offline - skip get for tenant={self.tenant_id}")
            self._misses += 1
            return None

        try:
            full_key = self._make_key(key)
            value = await self.redis.get(full_key)

            if value:
                self._hits += 1
                logger.debug(f"Cache HIT: {full_key}")
                return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                self._misses += 1
                logger.debug(f"Cache MISS: {full_key}")
                return None

        except Exception as e:
            logger.error(f"Cache get failed for tenant={self.tenant_id}: {e}")
            self._misses += 1
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with tier-specific TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override (defaults to tier TTL)

        Returns:
            True if successful, False otherwise

        Raises:
            QuotaExceededError: If tenant exceeds cache quota
        """
        if self.offline or not self.redis:
            logger.warning(f"Cache offline - skip set for tenant={self.tenant_id}")
            return False

        try:
            # Check quota before write
            metrics = await self.get_metrics()
            if metrics.size_gb > self.tier_config.cache_quota_gb * 0.9:
                msg = (
                    f"Tenant {self.tenant_id} at {metrics.size_gb:.1f}GB "
                    f"(quota: {self.tier_config.cache_quota_gb}GB)"
                )
                logger.error(msg)
                raise QuotaExceededError(msg)

            full_key = self._make_key(key)
            ttl = ttl or self.tier_config.cache_ttl

            await self.redis.setex(full_key, ttl, value)
            logger.debug(f"Cache SET: {full_key} (ttl={ttl}s)")
            return True

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"Cache set failed for tenant={self.tenant_id}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful
        """
        if self.offline or not self.redis:
            return False

        try:
            full_key = self._make_key(key)
            await self.redis.delete(full_key)
            logger.debug(f"Cache DELETE: {full_key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for tenant={self.tenant_id}: {e}")
            return False

    async def invalidate_tenant(self) -> int:
        """
        Invalidate all cache entries for this tenant.

        CRITICAL: Scoped to tenant namespace only - does NOT affect other tenants.

        Returns:
            Number of keys deleted
        """
        if self.offline or not self.redis:
            logger.warning(f"Cache offline - skip invalidate for tenant={self.tenant_id}")
            return 0

        try:
            pattern = f"{self.prefix}*"
            keys = []

            # Scan for all tenant keys
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} keys for tenant={self.tenant_id}")
                return deleted
            else:
                logger.info(f"No keys to invalidate for tenant={self.tenant_id}")
                return 0

        except Exception as e:
            logger.error(f"Cache invalidation failed for tenant={self.tenant_id}: {e}")
            return 0

    async def get_metrics(self) -> CacheMetrics:
        """
        Get cache metrics for this tenant.

        Returns:
            CacheMetrics object with performance data
        """
        if self.offline or not self.redis:
            return CacheMetrics(
                tenant_id=self.tenant_id,
                hits=self._hits,
                misses=self._misses,
                size_bytes=0,
                size_gb=0.0,
                key_count=0,
                hit_rate=0.0,
                evictions=0
            )

        try:
            pattern = f"{self.prefix}*"
            key_count = 0
            size_bytes = 0

            # Count keys and estimate size
            async for key in self.redis.scan_iter(match=pattern, count=100):
                key_count += 1
                # Estimate: get key memory usage
                try:
                    memory = await self.redis.memory_usage(key)
                    if memory:
                        size_bytes += memory
                except:
                    # Fallback: estimate 1KB per key
                    size_bytes += 1024

            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return CacheMetrics(
                tenant_id=self.tenant_id,
                hits=self._hits,
                misses=self._misses,
                size_bytes=size_bytes,
                size_gb=size_bytes / (1024**3),
                key_count=key_count,
                hit_rate=hit_rate,
                evictions=0  # Would need Redis INFO command for actual evictions
            )

        except Exception as e:
            logger.error(f"Failed to get metrics for tenant={self.tenant_id}: {e}")
            return CacheMetrics(
                tenant_id=self.tenant_id,
                hits=self._hits,
                misses=self._misses,
                size_bytes=0,
                size_gb=0.0,
                key_count=0,
                hit_rate=0.0,
                evictions=0
            )


# ============================================================================
# PERFORMANCE TIER ENFORCER
# ============================================================================

class PerformanceTierEnforcer:
    """
    Enforce performance tier SLAs through timeout and rate limiting.

    Features:
    - Hard timeouts per tier (Platinum 200ms, Gold 500ms, Silver 1s)
    - Query timeout violations tracking
    - Integration with monitoring
    """

    def __init__(self):
        """Initialize tier enforcer"""
        self._timeout_violations = {}
        logger.info("Initialized PerformanceTierEnforcer")

    async def enforce_timeout(
        self,
        tenant_id: str,
        tier: str,
        query_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute query with tier-specific timeout enforcement.

        Args:
            tenant_id: Tenant identifier
            tier: Performance tier
            query_func: Async function to execute
            *args, **kwargs: Arguments for query_func

        Returns:
            Query result

        Raises:
            TierViolationError: If query exceeds tier timeout
        """
        tier_config = get_tenant_tier_config(tier)
        timeout_sec = tier_config.timeout_ms / 1000.0

        try:
            logger.info(
                f"Executing query for tenant={tenant_id}, tier={tier}, "
                f"timeout={timeout_sec}s"
            )

            result = await asyncio.wait_for(
                query_func(*args, **kwargs),
                timeout=timeout_sec
            )

            return result

        except asyncio.TimeoutError as e:
            # Track violation
            self._timeout_violations[tenant_id] = self._timeout_violations.get(tenant_id, 0) + 1

            msg = (
                f"Query timeout for tenant={tenant_id}, tier={tier}, "
                f"timeout={timeout_sec}s exceeded"
            )
            logger.error(msg)
            raise TierViolationError(msg) from e

    def get_violations(self, tenant_id: str) -> int:
        """Get timeout violation count for tenant"""
        return self._timeout_violations.get(tenant_id, 0)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_query_hash(query: str, tenant_id: str) -> str:
    """
    Generate deterministic hash for query caching.

    Args:
        query: Query text
        tenant_id: Tenant identifier (included in hash for isolation)

    Returns:
        Hash string (first 16 chars of SHA256)
    """
    combined = f"{tenant_id}:{query}"
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


async def execute_cached_query(
    query: str,
    tenant_id: str,
    tier: str,
    redis_client: Optional[Any],
    query_executor: Callable,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Execute query with caching and tier enforcement.

    This is a complete example showing cache-aside pattern with
    performance tier enforcement.

    Args:
        query: Query text
        tenant_id: Tenant identifier
        tier: Performance tier
        redis_client: Redis client
        query_executor: Async function that executes the actual query
        offline: Skip Redis operations if True

    Returns:
        Dict containing query result and metadata
    """
    # Initialize components
    cache = TenantCache(tenant_id, tier, redis_client, offline=offline)
    enforcer = PerformanceTierEnforcer()

    # Generate cache key
    cache_key = generate_query_hash(query, tenant_id)

    # Try cache first
    cached_result = await cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for tenant={tenant_id}, query_hash={cache_key}")
        return {
            "result": json.loads(cached_result),
            "source": "cache",
            "tenant_id": tenant_id,
            "tier": tier,
            "cached": True
        }

    # Cache miss - execute query with timeout enforcement
    logger.info(f"Cache miss for tenant={tenant_id}, query_hash={cache_key}")

    try:
        result = await enforcer.enforce_timeout(
            tenant_id,
            tier,
            query_executor,
            query
        )

        # Cache the result
        await cache.set(cache_key, json.dumps(result))

        return {
            "result": result,
            "source": "query",
            "tenant_id": tenant_id,
            "tier": tier,
            "cached": False
        }

    except TierViolationError as e:
        logger.error(f"Tier violation: {e}")
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


# ============================================================================
# EXAMPLE QUERY EXECUTOR (for demonstration)
# ============================================================================

async def mock_vector_query(query: str) -> Dict[str, Any]:
    """
    Mock vector database query (for testing/demonstration).

    In production, this would call Pinecone/Weaviate/Qdrant.

    Args:
        query: Query text

    Returns:
        Mock query result
    """
    # Simulate vector DB latency
    await asyncio.sleep(0.1)

    return {
        "query": query,
        "results": [
            {"doc_id": "doc1", "score": 0.95, "text": "Sample result 1"},
            {"doc_id": "doc2", "score": 0.87, "text": "Sample result 2"}
        ],
        "latency_ms": 100
    }
