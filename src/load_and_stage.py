import duckdb

DB_PATH = "data/warehouse.duckdb"

def initialize_database():
    con = duckdb.connect(DB_PATH)
    return con

def stage_pull_requests(con):
    print("\n--- Staging Pull Requests into DuckDB ---")
    
    staging_query = """
    CREATE OR REPLACE TABLE stg_pull_requests AS
    WITH raw_duckdb AS (
        SELECT 'duckdb' AS repository_name, *
        FROM read_json_auto('data/raw/raw_duckdb_prs.json')
    ),
    raw_polars AS (
        SELECT 'polars' AS repository_name, *
        FROM read_json_auto('data/raw/raw_polars_prs.json')
    ),
    combined_raw AS (
        SELECT * FROM raw_duckdb
        UNION ALL BY NAME
        SELECT * FROM raw_polars
    )
    SELECT
        id AS pr_id,
        number AS pr_number,
        repository_name,
        state AS pr_state,
        title AS pr_title,
        
        -- Nested user object
        user.login AS author_username,
        user.id AS author_user_id,
        
        -- Already parsed as TIMESTAMP by read_json_auto
        created_at,
        updated_at,
        closed_at,
        merged_at,
        
        -- Derived binary flag
        CASE WHEN merged_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_merged,
        
        -- Cycle time calculation in hours directly between timestamps
        ROUND(date_diff('second', created_at, merged_at) / 3600.0, 2) AS cycle_time_hours

    FROM combined_raw;
    """
    
    con.execute(staging_query)
    
    # Inspect summary metrics
    result = con.execute("""
        SELECT 
            repository_name, 
            COUNT(*) AS total_prs,
            COUNT(merged_at) AS merged_prs,
            ROUND(AVG(cycle_time_hours), 2) AS avg_cycle_time_hours,
            ROUND(MEDIAN(cycle_time_hours), 2) AS median_cycle_time_hours
        FROM stg_pull_requests
        GROUP BY repository_name;
    """).df()
    
    print(result)

if __name__ == "__main__":
    con = initialize_database()
    stage_pull_requests(con)
    con.close()