-- 1. Create Dimension: Repositories
CREATE OR REPLACE TABLE dim_repositories AS
SELECT
    CASE 
        WHEN repository_name = 'duckdb' THEN 1
        WHEN repository_name = 'polars' THEN 2
    END AS repository_id,
    repository_name,
    CASE 
        WHEN repository_name = 'duckdb' THEN 'duckdb/duckdb'
        WHEN repository_name = 'polars' THEN 'pola-rs/polars'
    END AS full_name,
    MIN(created_at) AS tracked_since
FROM stg_pull_requests
GROUP BY repository_name;

-- 2. Create Dimension: Authors
CREATE OR REPLACE TABLE dim_authors AS
SELECT DISTINCT
    author_user_id AS author_id,
    author_username,
    MIN(created_at) AS first_seen_at
FROM stg_pull_requests
WHERE author_user_id IS NOT NULL
GROUP BY author_user_id, author_username;

-- 3. Create Fact: Pull Requests
CREATE OR REPLACE TABLE fact_pull_requests AS
SELECT
    f.pr_id,
    f.pr_number,
    r.repository_id,
    f.repository_name,
    f.author_user_id AS author_id,
    f.pr_state,
    f.pr_title,
    f.created_at,
    f.updated_at,
    f.closed_at,
    f.merged_at,
    f.is_merged,
    f.cycle_time_hours
FROM stg_pull_requests f
LEFT JOIN dim_repositories r 
    ON f.repository_name = r.repository_name;