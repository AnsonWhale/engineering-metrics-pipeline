import os
import time
import requests
from dotenv import load_dotenv
import json
from pathlib import Path

# Load variables from .env into Python's environment
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

# Prepare HTTP headers
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"
else:
    print("Warning: No GITHUB_TOKEN found. Operating under strict 60 requests/hr limit.")


def fetch_pull_requests(owner: str, repo: str, max_pages: int = 3):
    """
    Pulls recent pull requests for a given repository.
    Handles pagination and logs rate-limit telemetry.
    """
    endpoint = f"{BASE_URL}/repos/{owner}/{repo}/pulls"
    all_prs = []
    
    for page in range(1, max_pages + 1):
        # Query parameters
        params = {
            "state": "all",       # Retrieve both open and closed/merged PRs
            "per_page": 50,       # Max allowed is 100
            "page": page,
            "sort": "created",
            "direction": "desc"   # Most recent first
        }
        
        print(f"Fetching {owner}/{repo} PRs - Page {page}...")
        response = requests.get(endpoint, headers=HEADERS, params=params)
        
        # Check HTTP Status Code: 200 means "OK / Success"
        if response.status_code == 403 or response.status_code == 429:
            print("Rate limit reached! Waiting or stopping...")
            break
        elif response.status_code != 200:
            print(f"Failed request: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        
        # If GitHub returns an empty list, we have reached the last page
        if not data:
            print(f"No more data found. Stopped at page {page}.")
            break
            
        all_prs.extend(data)
        
        # Inspect GitHub's telemetry headers
        remaining_calls = response.headers.get("X-RateLimit-Remaining")
        reset_timestamp = response.headers.get("X-RateLimit-Reset")
        print(f"  -> Retrieved {len(data)} PRs. API Quota Remaining: {remaining_calls}")
        
        # Polite delay to prevent spamming the server
        time.sleep(0.5)
        
    return all_prs


def save_raw_json(data: list, filename: str):
    """
    Saves raw API payloads to the data/raw/ landing zone.
    Preserves auditability without modifying source structure.
    """
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved {len(data)} raw records to {file_path}")
    return file_path

if __name__ == "__main__":
    # 1. Fetch DuckDB pull requests (3 pages = 150 PRs)
    duckdb_data = fetch_pull_requests(owner="duckdb", repo="duckdb", max_pages=3)
    save_raw_json(duckdb_data, "raw_duckdb_prs.json")
    
    # 2. Fetch Polars pull requests (3 pages = 150 PRs)
    polars_data = fetch_pull_requests(owner="pola-rs", repo="polars", max_pages=3)
    save_raw_json(polars_data, "raw_polars_prs.json")