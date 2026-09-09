import argparse
import time
from src.extract import fetch_pull_requests, save_raw_json
from src.load_and_stage import initialize_database, stage_pull_requests
from src.transform import run_transformations
from src.run_analytics import run_analysis

def run_pipeline(pages: int):
    start_time = time.time()
    print("=" * 60)
    print("STARTING DATA PIPELINE: GitHub Engineering Metrics")
    print("=" * 60)

    # 1. EXTRACT
    print("\n[1/4] EXTRACTING DATA FROM GITHUB API...")
    duckdb_data = fetch_pull_requests(owner="duckdb", repo="duckdb", max_pages=pages)
    save_raw_json(duckdb_data, "raw_duckdb_prs.json")

    polars_data = fetch_pull_requests(owner="pola-rs", repo="polars", max_pages=pages)
    save_raw_json(polars_data, "raw_polars_prs.json")

    # 2. STAGE
    print("\n[2/4] STAGING RAW PAYLOADS INTO DUCKDB...")
    con = initialize_database()
    stage_pull_requests(con)
    con.close()

    # 3. TRANSFORM (STAR SCHEMA)
    print("\n[3/4] RUNNING DIMENSIONAL TRANSFORMATIONS...")
    run_transformations()

    # 4. REPORT / ANALYTICS
    print("\n[4/4] GENERATING ANALYTICAL METRICS...")
    run_analysis()

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GitHub Metrics ELT Pipeline.")
    parser.add_argument(
        "--pages",
        type=int,
        default=2,
        help="Number of pages to pull per repository (default: 2)"
    )
    args = parser.parse_args()

    run_pipeline(pages=args.pages)