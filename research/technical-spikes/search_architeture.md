# Search Architecture and Performance Optimization for Government Contract Aggregation Platform

Optimizing search architecture for millions of government contracts requires careful consideration of search engines, faceting strategies, real-time indexing, and performance optimization. This comprehensive analysis provides specific technical recommendations aligned with your platform's phased rollout from federal to state and local contracts.

## Search engine selection shapes your entire architecture

Based on extensive benchmarking and cost analysis, **Typesense emerges as the optimal choice** for government contract search, offering 80% of the functionality at 20% of the cost compared to premium alternatives. For a platform handling 5 million contracts with 5 million monthly searches, Typesense costs $300-800/month versus Elasticsearch's $2,000-5,000/month or Algolia's $4,500+/month.

Typesense's key advantages include a lightweight single binary deployment, real-time indexing without complex configuration, and proven scale serving 10B+ searches monthly on Typesense Cloud. The platform handles 3 million products at 250 concurrent searches/second on an 8-vCPU 3-node cluster, with sub-50ms query latency optimized for instant search experiences.

For government-specific requirements, Typesense offers SOC2 compliance, full code transparency for security audits, and deployment flexibility on government-approved infrastructure. While it lacks FedRAMP authorization (available with Elasticsearch on AWS GovCloud), its open-source nature allows complete on-premises deployment for sensitive data.

## NAICS hierarchical filtering requires sophisticated faceting

Government contracts demand complex hierarchical filtering across the 6-digit NAICS classification system with its 20 sectors, 99 subsectors, and 1,012 national industries. The optimal implementation uses a path hierarchy approach, storing NAICS codes as paths like "23/237/2371/23711/237110" for efficient querying.

```json
{
  "mappings": {
    "properties": {
      "naics_sector": {"type": "keyword"},
      "naics_subsector": {"type": "keyword"}, 
      "naics_industry_group": {"type": "keyword"},
      "naics_path": {
        "type": "text",
        "analyzer": "path_hierarchy"
      }
    }
  }
}
```

Multi-select faceting presents unique challenges since standard aggregations don't properly handle counts for unselected options. The solution employs filter aggregations that exclude each facet's own filter when calculating counts, maintaining accurate numbers across complex filter combinations. Performance optimization involves caching facet counts based on result set size—large sets (>50,000 results) cache for 24 hours while small sets (<500 results) skip caching entirely.

Geographic faceting leverages multi-level indexing for both place of performance and vendor location, supporting distance-based queries and hierarchical state/county/city filtering. Contract value ranges use predefined buckets aligned with federal procurement thresholds: micro purchases (<$25K), small purchases ($25K-250K), and large contracts (>$250K).

## Real-time indexing demands robust Kafka integration

The event-driven architecture follows a Producer → Kafka Topic → Consumer → Search Index pipeline, enabling horizontal scalability and loose coupling. For high-throughput scenarios handling thousands of updates per second, configure Kafka consumers with optimized fetch parameters:

```properties
fetch.min.bytes=1048576  # 1MB minimum
max.partition.fetch.bytes=10485760  # 10MB per partition
max.poll.records=1000  # Process up to 1000 records per poll
```

**Partial updates prove most efficient** for government contracts where documents are typically large (>10KB) with frequent status changes. However, Elasticsearch internally still performs full reindexing due to its immutable segment architecture. The decision between partial and full updates depends on document size and change frequency—use partial updates for large documents with small field changes, full reindexing for small documents or multiple simultaneous field changes.

Index consistency requires careful management of out-of-order messages. Using Kafka record offsets as external document versions prevents data corruption during high-concurrency bulk operations. Implement idempotent indexing through content-based document IDs or composite keys combining contract ID, version, and timestamp.

Optimal batch sizing starts at 1,000 documents per bulk request, with performance typically plateauing around 2,000-5,000 documents. Keep bulk requests under 10-20MB to avoid memory pressure. For government contract data with mixed update patterns, configure different commit intervals: 1-second intervals for critical contract awards, 5-second intervals for high-volume status updates, and manual commits for batch processing.

## Performance at scale requires multi-layer optimization

Sharding strategy fundamentally impacts search performance. Target 10-50GB per shard with a maximum of 200M documents, using time-based sharding by fiscal year for government contracts. This approach aligns with natural query patterns and simplifies data lifecycle management. Configure at least one replica per primary shard for fault tolerance, with cross-cluster replication for disaster recovery.

Redis caching dramatically improves response times through a multi-tier approach. Implement cache-aside patterns for query results, using MD5 hashes of query parameters as cache keys. Popular queries (>10 hits) receive extended TTLs of 2 hours versus 1 hour for standard queries. Facet counts cache separately with 30-minute TTLs, while cache invalidation follows both time-based and event-based patterns.

```python
def get_cache_key(self, query, filters, page, size):
    cache_data = {
        'query': query,
        'filters': sorted(filters.items()) if filters else [],
        'page': page,
        'size': size
    }
    return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
```

Query optimization leverages custom scoring functions that boost recent contracts, prioritize IDIQ vehicles, and factor in vendor performance ratings. Multi-field searches weight contract titles 3x, descriptions 2x, and vendor names 1.5x. Government-specific analyzers handle agency acronyms and procurement terminology through comprehensive synonym mapping.

Connection pooling manages concurrent load through round-robin load balancing across search nodes, with circuit breakers preventing cascade failures. Token bucket rate limiting enforces 10 requests per second with burst capacity of 100, protecting the search cluster during traffic spikes.

## Practical implementation roadmap

**Phase 1 - Federal Contracts (1M records)**: Deploy a 3-node Typesense cluster with 32GB RAM per node. Implement basic faceting for agencies, NAICS codes, and contract values. Configure Kafka with 3 partitions for real-time updates. Enable Redis caching for popular queries with 1-hour TTLs.

**Phase 2 - State Contracts (5M records)**: Scale to 6 nodes with increased RAM (64GB per node). Add geographic faceting and multi-level NAICS hierarchies. Increase Kafka partitions to 12 for higher throughput. Implement sophisticated caching with query popularity tracking and cache warming.

**Phase 3 - Local Contracts (50M+ records)**: Expand to 12+ nodes with NVMe SSDs. Consider Elasticsearch for advanced analytics requirements. Implement time-based index rollover and data lifecycle policies. Deploy dedicated Kafka clusters for each data source. Add CDN edge caching for static facet data.

**Configuration template for production deployment**:

```json
{
  "search": {
    "nodes": 6,
    "memory_per_node": "64GB",
    "shard_size": "20GB",
    "replicas": 1
  },
  "kafka": {
    "partitions": 12,
    "batch_size": 2000,
    "commit_interval": "5s"
  },
  "redis": {
    "cache_ttl": "3600s",
    "popular_query_ttl": "7200s",
    "connection_pool": 20
  },
  "performance": {
    "concurrent_searches": 1000,
    "target_latency": "<100ms",
    "indexing_throughput": "10000 docs/sec"
  }
}
```

This architecture scales efficiently from thousands to millions of contracts while maintaining sub-second search performance. The modular design allows incremental optimization as data volumes grow, with clear upgrade paths at each phase. Most importantly, it balances performance, cost, and operational complexity for sustainable long-term operation.