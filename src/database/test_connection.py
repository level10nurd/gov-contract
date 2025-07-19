#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection and table existence"""
    
    # Supabase database connection parameters from environment
    db_params = {
        'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
        'port': os.getenv('supabase_port', '5432'),
        'database': os.getenv('supbase_database', 'postgres'),
        'user': os.getenv('supbaabase_username', 'postgres'),
        'password': os.getenv('supabase_pswd')
    }
    
    print("Database connection parameters:")
    for key, value in db_params.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value)) if value else 'None'}")
        else:
            print(f"  {key}: {value}")
    
    try:
        # Create SQLAlchemy engine for Supabase
        engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
        
        # Test connection
        with engine.connect() as conn:
            print("\n✓ Database connection successful!")
            
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'archived_opportunities'
                );
            """))
            
            table_exists = result.fetchone()[0]
            print(f"✓ Table 'archived_opportunities' exists: {table_exists}")
            
            if table_exists:
                # Get table schema
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'archived_opportunities'
                    ORDER BY ordinal_position;
                """))
                
                print("\nTable schema:")
                for row in result:
                    print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                
                # Check current row count
                result = conn.execute(text("SELECT COUNT(*) FROM archived_opportunities;"))
                count = result.fetchone()[0]
                print(f"\nCurrent row count: {count}")
        
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")

if __name__ == "__main__":
    test_database_connection() 