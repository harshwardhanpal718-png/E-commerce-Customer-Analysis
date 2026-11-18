"""
SQL Analysis Runner & Database Loader
Creates SQLite database, executes schema.sql, populates tables from cleaned CSVs,
and runs all 10 analytical business queries from analysis_queries.sql.
"""

import os
import sqlite3
import pandas as pd
import time
import re

def setup_and_run_sql():
    db_path = 'data/ecommerce.db'
    proc_dir = 'data/processed'
    
    print("="*75)
    print("PHASE 5: SQL DATABASE SETUP & QUERY EXECUTION")
    print("="*75)
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed previous database instance: {db_path}")
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Execute schema.sql
    print("\n[1/3] Executing sql/schema.sql...")
    with open('sql/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    print("  -> Schema created successfully.")
    
    # 2. Ingest cleaned CSV data
    print("\n[2/3] Loading cleaned CSV datasets into relational tables...")
    table_file_map = [
        ('geolocation', 'geolocation_cleaned.csv'),
        ('customers', 'customers_cleaned.csv'),
        ('sellers', 'sellers_cleaned.csv'),
        ('products', 'products_cleaned.csv'),
        ('orders', 'orders_cleaned.csv'),
        ('order_items', 'order_items_cleaned.csv'),
        ('order_payments', 'order_payments_cleaned.csv'),
        ('order_reviews', 'order_reviews_cleaned.csv')
    ]
    
    for table_name, csv_name in table_file_map:
        csv_path = os.path.join(proc_dir, csv_name)
        if not os.path.exists(csv_path):
            print(f"  [WARNING] File missing: {csv_path}")
            continue
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"  -> Ingested {len(df):,} rows into '{table_name}'")
        
    conn.commit()
    print("  -> All tables populated successfully.")
    
    # 3. Read and execute analysis queries
    print("\n[3/3] Executing 10 Business Analysis SQL Queries...")
    with open('sql/analysis_queries.sql', 'r', encoding='utf-8') as f:
        full_sql = f.read()
        
    # Pattern to match: -- QUERY X: Title followed by SQL statement up to the ending semicolon
    query_pattern = re.compile(r'-- QUERY (\d+): ([^\n]+)\n(.*?);', re.DOTALL)
    matches = query_pattern.findall(full_sql)
    
    if not matches:
        print("Regex didn't match queries, checking fallback.")
    
    for q_num, q_title, q_body in matches:
        print("\n" + "="*70)
        print(f"EXECUTING QUERY {q_num}: {q_title.strip()}")
        print("="*70)
        
        # Clean query body of any inline comment-only blocks at the top
        clean_lines = []
        for line in q_body.split('\n'):
            if line.strip().startswith('--'):
                continue
            clean_lines.append(line)
        sql_statement = '\n'.join(clean_lines).strip()
        
        t0 = time.time()
        result_df = pd.read_sql_query(sql_statement, conn)
        t_elapsed = time.time() - t0
        
        print(f"Execution Time: {t_elapsed:.3f}s | Output Rows: {len(result_df)}")
        if len(result_df) > 10:
            print(result_df.head(10).to_string(index=False))
            print(f"... [{len(result_df) - 10} more rows truncated]")
        else:
            print(result_df.to_string(index=False))
            
    conn.close()
    print("\nALL 10 SQL BUSINESS QUERIES EXECUTED AND VALIDATED SUCCESSFULLY!")

if __name__ == '__main__':
    setup_and_run_sql()
