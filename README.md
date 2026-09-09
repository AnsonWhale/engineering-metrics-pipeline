# GitHub Engineering Metrics ELT Pipeline

An automated, local ELT (Extract, Load, Transform) data pipeline tracking engineering velocity, code review latency, and contributor dynamics across major open-source repositories (`duckdb/duckdb` vs. `pola-rs/polars`).

## Architecture & Data Flow

```text
[ GitHub REST API ]
        │  (Extract via Python: Pagination, Rate-Limit Headers, Auth)
        ▼
[ Raw Landing Zone ]       --> data/raw/*.json (Immutable JSON snapshots)
        │  (DuckDB JSON parsing & schema staging)
        ▼
[ Local Warehouse ]         --> data/warehouse.duckdb
        │  (SQL Dimensional Modeling)
        ▼
[ Star Schema Marts ]       --> dim_repositories, dim_authors, fact_pull_requests
        │  (Analytical Queries: Quantiles, Window Functions)
        ▼
[ Engineering Insights ]    --> Cycle times, Contributor concentration, Intake velocity
