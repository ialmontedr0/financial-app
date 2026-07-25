"""Custom Prometheus metrics for FIP business and performance monitoring."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

transactions_total = Counter(
    "fip_transactions_total",
    "Total number of transactions created",
    ["type", "status"],
)

users_total = Counter(
    "fip_users_total",
    "Total number of registered users",
)

active_users = Gauge(
    "fip_active_users",
    "Number of active users in the last 24h",
)

import_jobs_total = Counter(
    "fip_import_jobs_total",
    "Total number of import jobs",
    ["status", "file_type"],
)

request_duration_seconds = Histogram(
    "fip_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

db_query_duration_seconds = Histogram(
    "fip_db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

cache_hit_ratio = Gauge(
    "fip_cache_hit_ratio",
    "Redis cache hit ratio",
    ["cache_name"],
)

db_pool_size = Gauge(
    "fip_db_pool_size",
    "Current database connection pool size",
)

db_pool_available = Gauge(
    "fip_db_pool_available",
    "Available database connections in pool",
)

arq_queue_depth = Gauge(
    "fip_arq_queue_depth",
    "Arq background job queue depth",
    ["queue"],
)
