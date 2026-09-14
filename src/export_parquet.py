import duckdb
from pathlib import Path

DB_PATH = "data/warehouse.duckdb"
EXPORT_DIR = Path("data/export")

def export_marts_to_parquet():
    """
    Exports dimensional star schema tables from DuckDB into columnar Parquet files.
    Serves as the decoupled data mart layer for the dashboard.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH, read_only=True)
    
    tables = ["dim_repositories", "dim_authors", "fact_pull_requests"]
    
    print("\n--- Exporting Star Schema to Parquet ---")
    for table in tables:
        out_path = EXPORT_DIR / f"{table}.parquet"
        
        # DuckDB native Parquet export with Snappy compression
        con.execute(f"COPY {table} TO '{out_path.as_posix()}' (FORMAT PARQUET, COMPRESSION SNAPPY);")
        
        file_size_kb = round(out_path.stat().st_size / 1024, 2)
        print(f"Exported '{table}' -> {out_path} ({file_size_kb} KB)")
        
    con.close()

if __name__ == "__main__":
    export_marts_to_parquet()