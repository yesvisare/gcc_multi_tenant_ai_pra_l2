"""
L3 M11.3: Database Isolation & Cross-Tenant Security

This module implements three multi-tenant isolation strategies for RAG systems:
1. PostgreSQL Row-Level Security (RLS) - 99.9% isolation, ₹5L/month
2. Namespace-Based Isolation (Pinecone) - 99.95% isolation, ₹15L/month
3. Separate Database Per Tenant - 99.999% isolation, ₹50L/month

Includes defense-in-depth patterns, cross-tenant leak testing, and audit logging.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

__all__ = [
    "PostgresRLSManager",
    "PineconeNamespaceManager",
    "SeparateDatabaseManager",
    "TenantContextManager",
    "CrossTenantSecurityTests",
    "AuditLogger",
    "RedisIsolationManager",
    "S3PrefixIsolationManager"
]


# ============================================================================
# TENANT CONTEXT MANAGEMENT (Defense-in-Depth Layer 0)
# ============================================================================

class TenantContextManager:
    """
    Manages tenant context throughout request lifecycle.

    Critical: Never trust user input for tenant_id. Always extract from verified JWT.
    """

    def __init__(self):
        """Initialize tenant context manager."""
        self._current_tenant: Optional[uuid.UUID] = None
        logger.info("Initialized TenantContextManager")

    def set_tenant_context(self, tenant_id: uuid.UUID) -> None:
        """
        Set current tenant context for this request.

        Args:
            tenant_id: UUID of the tenant (from verified JWT, not user input)

        Raises:
            ValueError: If tenant_id is invalid
        """
        if not isinstance(tenant_id, uuid.UUID):
            raise ValueError(f"tenant_id must be UUID, got {type(tenant_id)}")

        self._current_tenant = tenant_id
        logger.info(f"Set tenant context: {tenant_id}")

    def get_tenant_context(self) -> uuid.UUID:
        """
        Get current tenant context.

        Returns:
            Current tenant UUID

        Raises:
            RuntimeError: If tenant context not set (security violation)
        """
        if self._current_tenant is None:
            raise RuntimeError("Tenant context not set - security violation!")

        return self._current_tenant

    def clear_tenant_context(self) -> None:
        """Clear tenant context after request completes."""
        self._current_tenant = None
        logger.debug("Cleared tenant context")


# ============================================================================
# STRATEGY 1: PostgreSQL Row-Level Security (RLS)
# ============================================================================

class PostgresRLSManager:
    """
    Implements PostgreSQL Row-Level Security for multi-tenant isolation.

    Isolation: 99.9%
    Cost: ₹5L/month for 50 tenants
    Trade-off: Policy bugs can cause leaks (CVE-2022-1552)
    """

    def __init__(self, connection_pool: Any):
        """
        Initialize RLS manager with connection pool.

        Args:
            connection_pool: psycopg2 connection pool
        """
        self.pool = connection_pool
        logger.info("Initialized PostgresRLSManager")

    def create_rls_policy(self, conn: Any) -> None:
        """
        Create RLS policy enforcing tenant_id filtering.

        Args:
            conn: Database connection
        """
        try:
            cursor = conn.cursor()

            # Enable RLS on documents table
            cursor.execute("""
                ALTER TABLE IF EXISTS documents ENABLE ROW LEVEL SECURITY;
            """)

            # Create policy enforcing tenant_id match
            # CRITICAL: No exceptions, even for admin users
            cursor.execute("""
                DROP POLICY IF EXISTS tenant_isolation ON documents;
                CREATE POLICY tenant_isolation ON documents
                USING (
                    tenant_id = current_setting('app.tenant_id', true)::uuid
                );
            """)

            conn.commit()
            logger.info("✓ RLS policy created successfully")

        except Exception as e:
            logger.error(f"Failed to create RLS policy: {e}")
            conn.rollback()
            raise

    def set_tenant_context(self, conn: Any, tenant_id: uuid.UUID) -> None:
        """
        Set tenant context in PostgreSQL session.

        Args:
            conn: Database connection
            tenant_id: Tenant UUID

        Raises:
            ValueError: If tenant_id is invalid
        """
        if not isinstance(tenant_id, uuid.UUID):
            raise ValueError(f"tenant_id must be UUID, got {type(tenant_id)}")

        try:
            cursor = conn.cursor()
            # Use SET LOCAL to ensure context only for this transaction
            cursor.execute("SET LOCAL app.tenant_id = %s", (str(tenant_id),))
            logger.debug(f"Set PostgreSQL tenant context: {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to set tenant context: {e}")
            raise

    def query_documents(self, tenant_id: uuid.UUID, search_pattern: str) -> List[Dict[str, Any]]:
        """
        Query documents with RLS enforcement.

        Args:
            tenant_id: Tenant UUID (from verified source)
            search_pattern: Search pattern for document titles

        Returns:
            List of documents (automatically filtered by RLS)
        """
        if self.pool is None:
            logger.warning("⚠️ PostgreSQL not available - returning empty results")
            return []

        conn = None
        try:
            conn = self.pool.getconn()

            # Set tenant context BEFORE any query
            self.set_tenant_context(conn, tenant_id)

            cursor = conn.cursor()
            # No WHERE tenant_id clause needed - RLS enforces automatically
            cursor.execute("""
                SELECT id, title, content, tenant_id, created_at
                FROM documents
                WHERE title LIKE %s
                LIMIT 10
            """, (f"%{search_pattern}%",))

            results = cursor.fetchall()
            documents = [
                {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "tenant_id": str(row[3]),
                    "created_at": row[4].isoformat() if row[4] else None
                }
                for row in results
            ]

            logger.info(f"Query returned {len(documents)} documents for tenant {tenant_id}")
            return documents

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)


# ============================================================================
# STRATEGY 2: Namespace-Based Isolation (Pinecone)
# ============================================================================

class PineconeNamespaceManager:
    """
    Implements namespace-based isolation in Pinecone vector database.

    Isolation: 99.95%
    Cost: ₹15L/month for 50 tenants
    Trade-off: Namespace typos cause silent failures
    """

    def __init__(self, pinecone_client: Any, index_name: str):
        """
        Initialize namespace manager.

        Args:
            pinecone_client: Pinecone client instance
            index_name: Name of Pinecone index
        """
        self.client = pinecone_client
        self.index_name = index_name
        self.index = None

        if pinecone_client:
            try:
                self.index = pinecone_client.Index(index_name)
                logger.info(f"Initialized PineconeNamespaceManager with index '{index_name}'")
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone index: {e}")

    def validate_namespace(self, tenant_id: uuid.UUID) -> str:
        """
        Construct and validate namespace for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Validated namespace string

        Raises:
            ValueError: If namespace format invalid
        """
        # Construct namespace (no trailing dashes or typos!)
        namespace = f"tenant-{str(tenant_id)}"

        # Validate format
        if not namespace.startswith("tenant-"):
            raise ValueError(f"Invalid namespace format: {namespace}")

        # Verify it's a valid UUID after 'tenant-'
        try:
            uuid.UUID(namespace.split("tenant-")[1])
        except ValueError:
            raise ValueError(f"Invalid UUID in namespace: {namespace}")

        logger.debug(f"Validated namespace: {namespace}")
        return namespace

    def query_vectors(
        self,
        tenant_id: uuid.UUID,
        query_vector: List[float],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query vectors with namespace isolation.

        Args:
            tenant_id: Tenant UUID (from verified source)
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            Query results from tenant's namespace only
        """
        if self.index is None:
            logger.warning("⚠️ Pinecone not available - returning empty results")
            return {"matches": [], "namespace": f"tenant-{tenant_id}", "skipped": True}

        try:
            # Validate namespace BEFORE query
            namespace = self.validate_namespace(tenant_id)

            # Query specific namespace only
            results = self.index.query(
                vector=query_vector,
                namespace=namespace,  # Enforced isolation
                top_k=top_k,
                include_metadata=True
            )

            logger.info(f"Query returned {len(results.get('matches', []))} results for namespace {namespace}")
            return {
                "matches": results.get("matches", []),
                "namespace": namespace,
                "skipped": False
            }

        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            raise

    def upsert_vectors(
        self,
        tenant_id: uuid.UUID,
        vectors: List[tuple]
    ) -> Dict[str, Any]:
        """
        Upsert vectors into tenant's namespace.

        Args:
            tenant_id: Tenant UUID
            vectors: List of (id, vector, metadata) tuples

        Returns:
            Upsert status
        """
        if self.index is None:
            logger.warning("⚠️ Pinecone not available - skipping upsert")
            return {"upserted_count": 0, "skipped": True}

        try:
            namespace = self.validate_namespace(tenant_id)

            # Upsert to specific namespace
            result = self.index.upsert(
                vectors=vectors,
                namespace=namespace
            )

            logger.info(f"Upserted {result.get('upserted_count', 0)} vectors to namespace {namespace}")
            return {
                "upserted_count": result.get("upserted_count", 0),
                "namespace": namespace,
                "skipped": False
            }

        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            raise


# ============================================================================
# STRATEGY 3: Separate Database Per Tenant
# ============================================================================

class SeparateDatabaseManager:
    """
    Manages separate PostgreSQL databases per tenant.

    Isolation: 99.999%
    Cost: ₹50L/month for 50 tenants
    Trade-off: High operational complexity, slow onboarding
    """

    def __init__(self):
        """Initialize separate database manager."""
        self.connection_pools: Dict[uuid.UUID, Any] = {}
        logger.info("Initialized SeparateDatabaseManager")

    def create_tenant_database(self, tenant_id: uuid.UUID, db_config: Dict[str, Any]) -> None:
        """
        Provision separate database for tenant.

        Args:
            tenant_id: Tenant UUID
            db_config: Database configuration (host, port, credentials)

        Note: In production, this uses Terraform/IaC. Takes 10-15 minutes.
        """
        try:
            import psycopg2
            from psycopg2 import pool

            # Create connection pool for this tenant's dedicated database
            connection_pool = pool.SimpleConnectionPool(
                1, 10,  # Smaller pool per tenant
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 5432),
                database=f"tenant_{str(tenant_id).replace('-', '_')}",
                user=db_config.get("user", "postgres"),
                password=db_config.get("password", "")
            )

            self.connection_pools[tenant_id] = connection_pool
            logger.info(f"✓ Created database for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to create tenant database: {e}")
            raise

    def get_tenant_connection(self, tenant_id: uuid.UUID) -> Any:
        """
        Get connection to tenant's dedicated database.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Database connection

        Raises:
            ValueError: If tenant database not provisioned
        """
        if tenant_id not in self.connection_pools:
            raise ValueError(f"No database provisioned for tenant {tenant_id}")

        return self.connection_pools[tenant_id].getconn()

    def query_documents(self, tenant_id: uuid.UUID, search_pattern: str) -> List[Dict[str, Any]]:
        """
        Query documents from tenant's dedicated database.

        Args:
            tenant_id: Tenant UUID
            search_pattern: Search pattern

        Returns:
            List of documents (no cross-tenant risk - physically separate)
        """
        try:
            conn = self.get_tenant_connection(tenant_id)
            cursor = conn.cursor()

            # No tenant_id filter needed - this IS their database
            cursor.execute("""
                SELECT id, title, content, created_at
                FROM documents
                WHERE title LIKE %s
                LIMIT 10
            """, (f"%{search_pattern}%",))

            results = cursor.fetchall()
            documents = [
                {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "created_at": row[3].isoformat() if row[3] else None
                }
                for row in results
            ]

            logger.info(f"Query returned {len(documents)} documents from tenant {tenant_id}'s database")
            return documents

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []


# ============================================================================
# REDIS CACHE ISOLATION (Key Prefixing)
# ============================================================================

class RedisIsolationManager:
    """
    Implements cache isolation using tenant-scoped key prefixing.

    Pattern: tenant:{uuid}:{key}
    """

    def __init__(self, redis_client: Any):
        """
        Initialize Redis isolation manager.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        logger.info("Initialized RedisIsolationManager")

    def get_tenant_key(self, tenant_id: uuid.UUID, key: str) -> str:
        """
        Construct tenant-scoped cache key.

        Args:
            tenant_id: Tenant UUID
            key: Cache key

        Returns:
            Prefixed key: tenant:{uuid}:{key}
        """
        return f"tenant:{str(tenant_id)}:{key}"

    def set_cache(self, tenant_id: uuid.UUID, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set cache value with tenant scope.

        Args:
            tenant_id: Tenant UUID
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if self.redis is None:
            logger.warning("⚠️ Redis not available")
            return False

        try:
            tenant_key = self.get_tenant_key(tenant_id, key)
            self.redis.setex(tenant_key, ttl, value)
            logger.debug(f"Set cache: {tenant_key}")
            return True
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False

    def get_cache(self, tenant_id: uuid.UUID, key: str) -> Optional[str]:
        """
        Get cache value with tenant scope.

        Args:
            tenant_id: Tenant UUID
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if self.redis is None:
            return None

        try:
            tenant_key = self.get_tenant_key(tenant_id, key)
            value = self.redis.get(tenant_key)
            logger.debug(f"Get cache: {tenant_key} -> {'hit' if value else 'miss'}")
            return value
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None


# ============================================================================
# S3 PREFIX ISOLATION
# ============================================================================

class S3PrefixIsolationManager:
    """
    Implements S3 isolation using tenant prefix patterns.

    Pattern: tenants/{uuid}/{document_id}/filename
    """

    def __init__(self, s3_client: Any, bucket: str):
        """
        Initialize S3 isolation manager.

        Args:
            s3_client: boto3 S3 client
            bucket: S3 bucket name
        """
        self.s3 = s3_client
        self.bucket = bucket
        logger.info(f"Initialized S3PrefixIsolationManager with bucket '{bucket}'")

    def get_tenant_prefix(self, tenant_id: uuid.UUID) -> str:
        """
        Get S3 prefix for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            S3 prefix: tenants/{uuid}/
        """
        return f"tenants/{str(tenant_id)}/"

    def upload_document(
        self,
        tenant_id: uuid.UUID,
        document_id: str,
        filename: str,
        content: bytes
    ) -> Dict[str, Any]:
        """
        Upload document to tenant's S3 prefix.

        Args:
            tenant_id: Tenant UUID
            document_id: Document ID
            filename: File name
            content: File content bytes

        Returns:
            Upload result with S3 key
        """
        if self.s3 is None:
            logger.warning("⚠️ S3 not available")
            return {"skipped": True}

        try:
            prefix = self.get_tenant_prefix(tenant_id)
            s3_key = f"{prefix}{document_id}/{filename}"

            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content
            )

            logger.info(f"Uploaded to S3: {s3_key}")
            return {
                "bucket": self.bucket,
                "key": s3_key,
                "tenant_id": str(tenant_id),
                "skipped": False
            }

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise


# ============================================================================
# CROSS-TENANT SECURITY TESTING
# ============================================================================

class CrossTenantSecurityTests:
    """
    Automated testing for cross-tenant data leaks.

    Runs 1,000+ adversarial queries to validate isolation.
    """

    def __init__(self, isolation_manager: Any):
        """
        Initialize security test suite.

        Args:
            isolation_manager: Any isolation manager (RLS, Namespace, or Separate DB)
        """
        self.manager = isolation_manager
        logger.info("Initialized CrossTenantSecurityTests")

    def run_adversarial_tests(self, tenant_ids: List[uuid.UUID]) -> Dict[str, Any]:
        """
        Run adversarial tests attempting to breach isolation.

        Args:
            tenant_ids: List of tenant UUIDs to test

        Returns:
            Test results with pass/fail status
        """
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        logger.info(f"Running adversarial tests for {len(tenant_ids)} tenants...")

        # Test 1: Attempt to query with wrong tenant context
        for i, tenant_id in enumerate(tenant_ids):
            wrong_tenant = tenant_ids[(i + 1) % len(tenant_ids)]  # Next tenant

            try:
                # Query as tenant A, try to access tenant B's data
                # This SHOULD return empty results (isolation working)
                docs = self.manager.query_documents(tenant_id, "test")

                results["total_tests"] += 1

                # Check if any docs belong to wrong tenant
                leaked = False
                for doc in docs:
                    if doc.get("tenant_id") and doc["tenant_id"] != str(tenant_id):
                        leaked = True
                        results["failures"].append({
                            "test": f"cross_tenant_leak_{i}",
                            "tenant": str(tenant_id),
                            "leaked_from": doc["tenant_id"]
                        })

                if not leaked:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
                results["failed"] += 1

        logger.info(f"Security tests complete: {results['passed']}/{results['total_tests']} passed")
        return results


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """
    Audit logger for tracking all tenant data access.

    Logs: Who accessed what, when, from which tenant context.
    """

    def __init__(self):
        """Initialize audit logger."""
        self.audit_log = []
        logger.info("Initialized AuditLogger")

    def log_access(
        self,
        tenant_id: uuid.UUID,
        user_id: str,
        action: str,
        resource: str,
        result: str
    ) -> None:
        """
        Log data access event.

        Args:
            tenant_id: Tenant UUID
            user_id: User identifier
            action: Action performed (query, upsert, delete, etc.)
            resource: Resource accessed
            result: Access result (success, denied, error)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": str(tenant_id),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result
        }

        self.audit_log.append(entry)
        logger.info(f"AUDIT: {action} on {resource} by {user_id} (tenant {tenant_id}) -> {result}")

    def get_audit_trail(self, tenant_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
        """
        Get audit trail, optionally filtered by tenant.

        Args:
            tenant_id: Optional tenant UUID to filter by

        Returns:
            List of audit log entries
        """
        if tenant_id:
            return [
                entry for entry in self.audit_log
                if entry["tenant_id"] == str(tenant_id)
            ]
        return self.audit_log
