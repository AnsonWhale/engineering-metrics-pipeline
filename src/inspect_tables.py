import duckdb

con = duckdb.connect("data/warehouse.duckdb")

tables = ["dim_repositories", "dim_authors", "fact_pull_requests"]

for table in tables:
    print(f"\n{'='*25} {table.upper()} {'='*25}")
    
    print("\n[Schema / Column Types]:")
    print(con.execute(f"DESCRIBE {table};").df()[["column_name", "column_type", "null", "key"]])
    
    print("\n[Sample Rows (First 3)]:")
    print(con.execute(f"SELECT * FROM {table} LIMIT 3;").df())

con.close()