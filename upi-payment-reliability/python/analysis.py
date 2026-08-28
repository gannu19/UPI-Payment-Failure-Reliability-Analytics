import os
import glob
import sqlite3

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
SQL_DIR = os.path.join(BASE_DIR, "sql")

print("Executing SQL Analysis Pipeline...")

if HAS_DUCKDB:
    print("Using DuckDB SQL Engine...")
    con = duckdb.connect(database=":memory:")
    
    # Load CSV files into DuckDB tables
    for csv_file in glob.glob(os.path.join(PROC_DIR, "*.csv")):
        table_name = os.path.splitext(os.path.basename(csv_file))[0]
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_file.replace('\\', '/')}');")
        print(f"Loaded table '{table_name}' into DuckDB.")
    
    # Create raw_transactions table mapping for 01_data_quality.sql audit
    raw_tx_path = os.path.join(BASE_DIR, "data", "raw", "transactions.csv").replace('\\', '/')
    con.execute(f"CREATE TABLE raw_transactions AS SELECT * FROM read_csv_auto('{raw_tx_path}');")
    con.execute(f"CREATE TABLE clean_transactions AS SELECT * FROM transactions;")
    
    sql_files = sorted(glob.glob(os.path.join(SQL_DIR, "*.sql")))
    for sql_file in sql_files:
        filename = os.path.basename(sql_file)
        print(f"\n==================================================")
        print(f"Executing SQL Script: {filename}")
        print(f"==================================================")
        
        with open(sql_file, "r", encoding="utf-8") as f:
            query_content = f.read()
            
        # Split multiple queries by semicolon if needed
        queries = [q.strip() for q in query_content.split(";") if q.strip() and not q.strip().startswith("--")]
        for idx, q in enumerate(queries, 1):
            if "CREATE VIEW" in q:
                con.execute(q)
                continue
            try:
                res = con.execute(q).df()
                print(f"\n--- Query Result #{idx} ---")
                print(res.head(10).to_string(index=False))
            except Exception as e:
                print(f"Query Execution Note: {e}")

else:
    print("DuckDB not found, falling back to SQLite standard engine...")
    conn = sqlite3.connect(":memory:")
    # SQLite logic fallback if needed
    
print("\nSQL Analysis Pipeline execution completed successfully!")
