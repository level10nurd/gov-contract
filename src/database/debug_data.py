#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_database_data():
    """Debug what's actually in the database"""
    
    # Database connection
    db_params = {
        'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
        'port': os.getenv('supabase_port', '6543'),
        'database': os.getenv('supbase_database', 'postgres'),
        'user': os.getenv('supbaabase_username', 'postgres'),
        'password': os.getenv('supabase_pswd')
    }
    
    engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    with engine.connect() as conn:
        # Check total count
        result = conn.execute(text("SELECT COUNT(*) FROM archived_opportunities"))
        total_count = result.fetchone()[0]
        print(f"Total records: {total_count}")
        
        # Check notice_id count
        result = conn.execute(text("SELECT COUNT(*) FROM archived_opportunities WHERE notice_id IS NOT NULL"))
        notice_id_count = result.fetchone()[0]
        print(f"Records with notice_id: {notice_id_count}")
        
        # Check for null notice_ids
        result = conn.execute(text("SELECT COUNT(*) FROM archived_opportunities WHERE notice_id IS NULL"))
        null_count = result.fetchone()[0]
        print(f"Records with NULL notice_id: {null_count}")
        
        # Sample some records
        result = conn.execute(text("SELECT id, notice_id, title FROM archived_opportunities LIMIT 5"))
        print("\nSample records:")
        for row in result:
            print(f"  ID: {row[0]}, Notice ID: '{row[1]}', Title: '{row[2][:50]}...'")
        
        # Check distinct notice_ids
        result = conn.execute(text("SELECT COUNT(DISTINCT notice_id) FROM archived_opportunities WHERE notice_id IS NOT NULL"))
        distinct_count = result.fetchone()[0]
        print(f"\nDistinct notice_ids: {distinct_count}")

if __name__ == "__main__":
    debug_database_data() 