import duckdb
import pandas as pd

# Configure pandas to display all columns cleanly
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)

DB_PATH = "data/warehouse.duckdb"

def run_analysis():
    con = duckdb.connect(DB_PATH)

    print("\n" + "=" * 80)
    print("1. CYCLE TIME DISTRIBUTION (HOURS)")
    print("=" * 80)
    # Measures the 25th, 50th (median), 75th, and 90th percentile turnaround time
    q1 = """
    SELECT 
        r.repository_name,
        COUNT(*) AS merged_prs_count,
        ROUND(QUANTILE_CONT(cycle_time_hours, 0.25), 2) AS p25_hrs,
        ROUND(QUANTILE_CONT(cycle_time_hours, 0.50), 2) AS p50_median_hrs,
        ROUND(QUANTILE_CONT(cycle_time_hours, 0.75), 2) AS p75_hrs,
        ROUND(QUANTILE_CONT(cycle_time_hours, 0.90), 2) AS p90_hrs
    FROM fact_pull_requests f
    JOIN dim_repositories r ON f.repository_id = r.repository_id
    WHERE f.is_merged = TRUE
    GROUP BY r.repository_name;
    """
    print(con.execute(q1).df())

    print("\n" + "=" * 80)
    print("2. CONTRIBUTOR CONCENTRATION (TOP 5 MERGED PR AUTHORS)")
    print("=" * 80)
    # Measures team centralization: are contributions diversified or concentrated in a few core authors?
    q2 = """
    WITH author_merge_counts AS (
        SELECT 
            r.repository_name,
            a.author_username,
            COUNT(*) AS merged_prs,
            SUM(COUNT(*)) OVER (PARTITION BY r.repository_name) AS repo_total_merged
        FROM fact_pull_requests f
        JOIN dim_authors a ON f.author_id = a.author_id
        JOIN dim_repositories r ON f.repository_id = r.repository_id
        WHERE f.is_merged = TRUE
        GROUP BY r.repository_name, a.author_username
    ),
    ranked_authors AS (
        SELECT 
            repository_name,
            author_username,
            merged_prs,
            ROUND(merged_prs * 100.0 / repo_total_merged, 2) AS pct_of_repo_merges,
            SUM(merged_prs) OVER (
                PARTITION BY repository_name 
                ORDER BY merged_prs DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS cumulative_prs,
            repo_total_merged
        FROM author_merge_counts
    )
    SELECT 
        repository_name,
        author_username,
        merged_prs,
        pct_of_repo_merges,
        ROUND(cumulative_prs * 100.0 / repo_total_merged, 2) AS cumulative_pct
    FROM ranked_authors
    QUALIFY ROW_NUMBER() OVER (PARTITION BY repository_name ORDER BY merged_prs DESC) <= 5;
    """
    print(con.execute(q2).df())

    print("\n" + "=" * 80)
    print("3. INTAKE & VELOCITY BY DAY OF WEEK")
    print("=" * 80)
    # Checks if PR turnaround slows down on weekends or specific weekdays
    q3 = """
    SELECT 
        r.repository_name,
        DAYNAME(f.created_at) AS day_opened,
        COUNT(*) AS prs_opened,
        COUNT(f.merged_at) AS prs_merged,
        ROUND(MEDIAN(f.cycle_time_hours), 2) AS median_cycle_hrs
    FROM fact_pull_requests f
    JOIN dim_repositories r ON f.repository_id = r.repository_id
    GROUP BY r.repository_name, DAYNAME(f.created_at), EXTRACT(DOW FROM f.created_at)
    ORDER BY r.repository_name, EXTRACT(DOW FROM f.created_at);
    """
    print(con.execute(q3).df())

    con.close()

if __name__ == "__main__":
    run_analysis()