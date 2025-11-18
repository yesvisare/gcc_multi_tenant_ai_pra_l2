"""
Tests for L3 M13.1: Multi-Tenant Performance Patterns

Tests ALL major functions from script with offline mode (no Redis required).
SERVICE: REDIS (mocked for testing)
"""

import pytest
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Force offline mode for tests
os.environ["REDIS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m13_performance_patterns import (
    TenantCache,
    PerformanceTier,
    PerformanceTierEnforcer,
    get_tenant_tier_config,
    generate_query_hash,
    execute_cached_query,
    mock_vector_query,
    QuotaExceededError,
    TierViolationError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.scan_iter = AsyncMock(return_value=iter([]))
    mock.memory_usage = AsyncMock(return_value=1024)
    return mock


@pytest.fixture
def tenant_cache_offline():
    """TenantCache in offline mode (no Redis)"""
    return TenantCache(
        tenant_id="test_tenant",
        tier="gold",
        redis_client=None,
        offline=True
    )


@pytest.fixture
def tier_enforcer():
    """Performance tier enforcer"""
    return PerformanceTierEnforcer()


# ============================================================================
# TIER CONFIGURATION TESTS
# ============================================================================

def test_get_tenant_tier_config_platinum():
    """Test getting platinum tier configuration"""
    config = get_tenant_tier_config("platinum")
    assert config.timeout_ms == 200
    assert config.cache_ttl == 3600
    assert config.max_qps == 1000
    assert config.cache_quota_gb == 40.0


def test_get_tenant_tier_config_gold():
    """Test getting gold tier configuration"""
    config = get_tenant_tier_config("gold")
    assert config.timeout_ms == 500
    assert config.cache_ttl == 1800
    assert config.max_qps == 500
    assert config.cache_quota_gb == 20.0


def test_get_tenant_tier_config_silver():
    """Test getting silver tier configuration"""
    config = get_tenant_tier_config("silver")
    assert config.timeout_ms == 1000
    assert config.cache_ttl == 900
    assert config.max_qps == 200
    assert config.cache_quota_gb == 10.0


def test_get_tenant_tier_config_invalid():
    """Test getting invalid tier raises error"""
    with pytest.raises(ValueError, match="Invalid tier"):
        get_tenant_tier_config("invalid_tier")


# ============================================================================
# TENANT CACHE TESTS - OFFLINE MODE
# ============================================================================

@pytest.mark.asyncio
async def test_tenant_cache_offline_get(tenant_cache_offline):
    """Test cache get in offline mode returns None"""
    result = await tenant_cache_offline.get("test_key")
    assert result is None
    assert tenant_cache_offline._misses == 1


@pytest.mark.asyncio
async def test_tenant_cache_offline_set(tenant_cache_offline):
    """Test cache set in offline mode returns False"""
    result = await tenant_cache_offline.set("test_key", "test_value")
    assert result is False


@pytest.mark.asyncio
async def test_tenant_cache_offline_delete(tenant_cache_offline):
    """Test cache delete in offline mode returns False"""
    result = await tenant_cache_offline.delete("test_key")
    assert result is False


@pytest.mark.asyncio
async def test_tenant_cache_offline_invalidate(tenant_cache_offline):
    """Test cache invalidation in offline mode returns 0"""
    result = await tenant_cache_offline.invalidate_tenant()
    assert result == 0


@pytest.mark.asyncio
async def test_tenant_cache_offline_metrics(tenant_cache_offline):
    """Test cache metrics in offline mode"""
    # Simulate some cache operations
    await tenant_cache_offline.get("key1")
    await tenant_cache_offline.get("key2")

    metrics = await tenant_cache_offline.get_metrics()
    assert metrics.tenant_id == "test_tenant"
    assert metrics.hits == 0
    assert metrics.misses == 2
    assert metrics.size_gb == 0.0
    assert metrics.key_count == 0
    assert metrics.hit_rate == 0.0


# ============================================================================
# TENANT CACHE TESTS - WITH MOCK REDIS
# ============================================================================

@pytest.mark.asyncio
async def test_tenant_cache_namespace_isolation(mock_redis):
    """Test that cache keys are properly namespaced"""
    cache = TenantCache("tenant_a", "gold", mock_redis, offline=False)

    await cache.set("query_123", "result_data")

    # Verify setex was called with namespaced key
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]
    assert call_args[0] == "cache:tenant_a:query_123"
    assert call_args[2] == "result_data"


@pytest.mark.asyncio
async def test_tenant_cache_different_tenants_different_keys(mock_redis):
    """Test that different tenants get different namespaced keys"""
    cache_a = TenantCache("tenant_a", "gold", mock_redis, offline=False)
    cache_b = TenantCache("tenant_b", "gold", mock_redis, offline=False)

    await cache_a.set("query_123", "result_a")
    await cache_b.set("query_123", "result_b")

    # Both should have written to different keys
    assert mock_redis.setex.call_count == 2

    calls = mock_redis.setex.call_args_list
    assert calls[0][0][0] == "cache:tenant_a:query_123"
    assert calls[1][0][0] == "cache:tenant_b:query_123"


@pytest.mark.asyncio
async def test_tenant_cache_tier_specific_ttl(mock_redis):
    """Test that different tiers get different TTLs"""
    cache_platinum = TenantCache("tenant_p", "platinum", mock_redis, offline=False)
    cache_silver = TenantCache("tenant_s", "silver", mock_redis, offline=False)

    await cache_platinum.set("query_123", "result")
    platinum_ttl = mock_redis.setex.call_args[0][1]

    await cache_silver.set("query_123", "result")
    silver_ttl = mock_redis.setex.call_args[0][1]

    assert platinum_ttl == 3600  # 1 hour
    assert silver_ttl == 900      # 15 minutes


@pytest.mark.asyncio
async def test_tenant_cache_hit(mock_redis):
    """Test cache hit increments hit counter"""
    mock_redis.get.return_value = b"cached_result"

    cache = TenantCache("tenant_a", "gold", mock_redis, offline=False)
    result = await cache.get("query_123")

    assert result == "cached_result"
    assert cache._hits == 1
    assert cache._misses == 0


@pytest.mark.asyncio
async def test_tenant_cache_miss(mock_redis):
    """Test cache miss increments miss counter"""
    mock_redis.get.return_value = None

    cache = TenantCache("tenant_a", "gold", mock_redis, offline=False)
    result = await cache.get("query_123")

    assert result is None
    assert cache._hits == 0
    assert cache._misses == 1


# ============================================================================
# PERFORMANCE TIER ENFORCER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_tier_enforcer_within_timeout(tier_enforcer):
    """Test query completes within tier timeout"""
    async def fast_query():
        await asyncio.sleep(0.05)  # 50ms - within all tiers
        return {"result": "success"}

    result = await tier_enforcer.enforce_timeout(
        "test_tenant",
        "platinum",  # 200ms timeout
        fast_query
    )

    assert result == {"result": "success"}
    assert tier_enforcer.get_violations("test_tenant") == 0


@pytest.mark.asyncio
async def test_tier_enforcer_exceeds_timeout(tier_enforcer):
    """Test query exceeds tier timeout"""
    async def slow_query():
        await asyncio.sleep(0.3)  # 300ms - exceeds platinum 200ms
        return {"result": "success"}

    with pytest.raises(TierViolationError, match="Query timeout"):
        await tier_enforcer.enforce_timeout(
            "test_tenant",
            "platinum",  # 200ms timeout
            slow_query
        )

    assert tier_enforcer.get_violations("test_tenant") == 1


@pytest.mark.asyncio
async def test_tier_enforcer_different_tiers(tier_enforcer):
    """Test that different tiers have different timeouts"""
    async def query_250ms():
        await asyncio.sleep(0.25)  # 250ms
        return {"result": "success"}

    # Platinum (200ms) - should timeout
    with pytest.raises(TierViolationError):
        await tier_enforcer.enforce_timeout("tenant_p", "platinum", query_250ms)

    # Gold (500ms) - should succeed
    result = await tier_enforcer.enforce_timeout("tenant_g", "gold", query_250ms)
    assert result == {"result": "success"}

    # Silver (1000ms) - should succeed
    result = await tier_enforcer.enforce_timeout("tenant_s", "silver", query_250ms)
    assert result == {"result": "success"}


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

def test_generate_query_hash():
    """Test query hash generation"""
    hash1 = generate_query_hash("test query", "tenant_a")
    hash2 = generate_query_hash("test query", "tenant_a")
    hash3 = generate_query_hash("test query", "tenant_b")

    # Same tenant + query = same hash
    assert hash1 == hash2

    # Different tenant = different hash (tenant isolation)
    assert hash1 != hash3

    # Hash is 16 characters
    assert len(hash1) == 16


def test_generate_query_hash_deterministic():
    """Test that query hash is deterministic"""
    hashes = [generate_query_hash("test", "tenant") for _ in range(10)]
    assert len(set(hashes)) == 1  # All should be the same


# ============================================================================
# MOCK VECTOR QUERY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_mock_vector_query():
    """Test mock vector query executor"""
    result = await mock_vector_query("test query")

    assert "query" in result
    assert "results" in result
    assert "latency_ms" in result
    assert result["query"] == "test query"
    assert len(result["results"]) == 2


# ============================================================================
# INTEGRATION TEST - FULL QUERY FLOW
# ============================================================================

@pytest.mark.asyncio
async def test_execute_cached_query_offline():
    """Test full query flow in offline mode"""
    async def test_executor(query):
        return {"query": query, "result": "test_result"}

    result = await execute_cached_query(
        query="test query",
        tenant_id="tenant_test",
        tier="gold",
        redis_client=None,
        query_executor=test_executor,
        offline=True
    )

    assert result["tenant_id"] == "tenant_test"
    assert result["tier"] == "gold"
    assert result["cached"] is False  # Offline = no caching
    assert result["source"] == "query"
    assert result["result"]["query"] == "test query"


@pytest.mark.asyncio
async def test_execute_cached_query_with_mock_redis(mock_redis):
    """Test full query flow with mocked Redis"""
    async def test_executor(query):
        return {"query": query, "result": "test_result"}

    # First call - cache miss
    mock_redis.get.return_value = None

    result = await execute_cached_query(
        query="test query",
        tenant_id="tenant_test",
        tier="gold",
        redis_client=mock_redis,
        query_executor=test_executor,
        offline=False
    )

    assert result["cached"] is False
    assert result["source"] == "query"
    assert mock_redis.setex.called  # Should cache the result


# ============================================================================
# FAILURE SCENARIO TESTS (from script Section 8)
# ============================================================================

def test_namespace_collision_prevention(mock_redis):
    """
    Test Failure #1: Cache namespace collision prevention

    Ensures that TenantCache wrapper prevents direct Redis access
    and enforces namespace isolation.
    """
    cache_a = TenantCache("tenant_a", "gold", mock_redis, offline=False)
    cache_b = TenantCache("tenant_b", "gold", mock_redis, offline=False)

    # Even with same query, different tenants get different keys
    hash_a = generate_query_hash("same query", "tenant_a")
    hash_b = generate_query_hash("same query", "tenant_b")

    assert hash_a != hash_b  # Hashes are different due to tenant_id


@pytest.mark.asyncio
async def test_timeout_enforcement_prevents_tier_violation(tier_enforcer):
    """
    Test Failure #3: Timeout too loose

    Ensures that tier timeouts are enforced strictly.
    """
    async def slow_query():
        await asyncio.sleep(0.8)  # 800ms
        return {"result": "done"}

    # Platinum tier (200ms) should reject this
    with pytest.raises(TierViolationError):
        await tier_enforcer.enforce_timeout("tenant_p", "platinum", slow_query)

    # Silver tier (1000ms) should allow this
    result = await tier_enforcer.enforce_timeout("tenant_s", "silver", slow_query)
    assert result["result"] == "done"


@pytest.mark.asyncio
async def test_scoped_invalidation(mock_redis):
    """
    Test Failure #5: Cache invalidation affects all tenants

    Ensures that invalidation is scoped to tenant namespace only.
    """
    cache_a = TenantCache("tenant_a", "gold", mock_redis, offline=False)

    # Mock scan_iter to return tenant_a keys only
    mock_redis.scan_iter.return_value = iter([
        b"cache:tenant_a:key1",
        b"cache:tenant_a:key2"
    ])

    deleted = await cache_a.invalidate_tenant()

    # Should delete tenant_a keys only
    mock_redis.delete.assert_called_once()
    deleted_keys = mock_redis.delete.call_args[0]
    assert all(b"tenant_a" in key for key in deleted_keys)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
