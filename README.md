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
```

Key Findings
Review Velocity: Polars exhibits significantly faster PR turnaround (median cycle time of ~5.5 hours, 25th percentile of 1.4 hours) compared to DuckDB (median ~27.4 hours, 25th percentile 14.1 hours), reflecting differing CI test matrices and review workflows.

Contributor Centralization: Polars PR throughput is heavily concentrated, with the top 2 maintainers driving >51% of all merged PRs. DuckDB exhibits higher contributor diversification, with its top contributor accounting for 12.2% and work distributed across specialized maintainers.

Intake Dynamics: DuckDB PRs submitted on Fridays experience a steep review stall over weekends (median cycle time jumping to ~66 hours), whereas Polars maintains steady weekend turnaround.
