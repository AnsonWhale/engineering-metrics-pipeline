import duckdb
from pathlib import Path

DB_PATH = "data/warehouse.duckdb"

def run_transformations():
    """Executes analytical SQL transformations to build dimensional marts."""
    print("\n--- Running Dimensional Modeling (Star Schema) ---")
    
    con = duckdb.connect(DB_PATH)
    
    sql_path = Path("sql/transform.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        transform_sql = f.read()
        
    # Execute the SQL script
    con.execute(transform_sql)
    
    # Validation check: Verify row counts in Fact and Dimension tables
    repo_count = con.execute("SELECT COUNT(*) FROM dim_repositories;").fetchone()[0]
    author_count = con.execute("SELECT COUNT(*) FROM dim_authors;").fetchone()[0]
    fact_count = con.execute("SELECT COUNT(*) FROM fact_pull_requests;").fetchone()[0]

    print(f"Created 'dim_repositories' with {repo_count} repositories.")
    print(f"Created 'dim_authors' with {author_count} unique contributors.")
    print(f"Created 'fact_pull_requests' with {fact_count} events.")
    
    con.close()

if __name__ == "__main__":
    run_transformations()