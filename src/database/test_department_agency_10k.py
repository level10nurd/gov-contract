#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def create_test_table(engine):
    """Create a test table with first 10k records"""
    print("Creating test table with first 10,000 records...")
    
    with engine.connect() as conn:
        # Create test table structure
        conn.execute(text("""
            DROP TABLE IF EXISTS test_archived_opportunities_10k;
            
            CREATE TABLE test_archived_opportunities_10k AS 
            SELECT * FROM archived_opportunities 
            LIMIT 10000;
            
            -- Add index for faster queries
            CREATE INDEX idx_test_department_agency ON test_archived_opportunities_10k(department_agency);
        """))
        conn.commit()
        print("✓ Test table created with 10,000 records")

def extract_unique_agencies_test(engine):
    """Extract unique department agencies from test table"""
    print("Extracting unique department agencies from test table...")
    
    query = """
    SELECT DISTINCT 
        department_agency,
        cgac as agency_code,
        COUNT(*) as contract_count
    FROM test_archived_opportunities_10k 
    WHERE department_agency IS NOT NULL 
      AND department_agency != ''
      AND TRIM(department_agency) != ''
    GROUP BY department_agency, cgac
    ORDER BY contract_count DESC, department_agency;
    """
    
    df = pd.read_sql(query, engine)
    
    # Clean up agency names
    df['agency_name'] = df['department_agency'].str.strip()
    
    # Handle cases where same agency name has different codes
    df_grouped = df.groupby('agency_name').agg({
        'agency_code': lambda x: x.value_counts().index[0] if len(x.value_counts()) > 0 else None,
        'contract_count': 'sum'
    }).reset_index()
    
    print(f"✓ Found {len(df_grouped)} unique department agencies in test data")
    print("\nTop 10 agencies by contract count:")
    print(df_grouped.head(10)[['agency_name', 'contract_count']].to_string(index=False))
    
    return df_grouped

def create_test_department_agency_table(engine):
    """Create test department_agency table"""
    print("\nCreating test department_agency table...")
    
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS test_department_agency;
            
            CREATE TABLE test_department_agency (
                id SERIAL PRIMARY KEY,
                agency_name TEXT UNIQUE NOT NULL,
                agency_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_test_department_agency_name ON test_department_agency(agency_name);
            CREATE INDEX idx_test_department_agency_code ON test_department_agency(agency_code);
        """))
        conn.commit()
        print("✓ Test department_agency table created")

def load_agencies_to_test_table(engine, agencies_df):
    """Load unique agencies to test department_agency table"""
    print(f"Loading {len(agencies_df)} agencies to test table...")
    
    # Insert data
    agencies_df[['agency_name', 'agency_code']].to_sql(
        'test_department_agency', 
        engine, 
        if_exists='append', 
        index=False,
        method='multi'
    )
    print(f"✓ Successfully loaded {len(agencies_df)} agencies")

def test_foreign_key_update(engine):
    """Test updating foreign keys with progress monitoring"""
    print("\nTesting foreign key updates with progress monitoring...")
    
    with engine.connect() as conn:
        # Add foreign key column
        conn.execute(text("ALTER TABLE test_archived_opportunities_10k ADD COLUMN department_agency_id INTEGER"))
        conn.commit()
        print("✓ Added department_agency_id column")
        
        # Get total count for progress tracking
        result = conn.execute(text("SELECT COUNT(*) FROM test_archived_opportunities_10k WHERE department_agency IS NOT NULL"))
        total_records = result.scalar()
        print(f"Total records to update: {total_records}")
        
        # Update in chunks for progress monitoring
        chunk_size = 1000
        updated_total = 0
        
        start_time = time.time()
        
        for offset in range(0, total_records, chunk_size):
            chunk_start = time.time()
            
            # Update chunk
            update_query = """
            UPDATE test_archived_opportunities_10k 
            SET department_agency_id = da.id
            FROM test_department_agency da
            WHERE TRIM(test_archived_opportunities_10k.department_agency) = da.agency_name
              AND test_archived_opportunities_10k.id IN (
                  SELECT id FROM test_archived_opportunities_10k 
                  WHERE department_agency IS NOT NULL 
                  ORDER BY id 
                  LIMIT :chunk_size OFFSET :offset
              )
            """
            
            result = conn.execute(text(update_query), {
                'chunk_size': chunk_size,
                'offset': offset
            })
            updated_count = result.rowcount
            updated_total += updated_count
            
            chunk_time = time.time() - chunk_start
            elapsed_time = time.time() - start_time
            
            progress = (offset + chunk_size) / total_records * 100
            estimated_total_time = elapsed_time / (progress / 100) if progress > 0 else 0
            remaining_time = estimated_total_time - elapsed_time
            
            print(f"  Chunk {offset//chunk_size + 1}: Updated {updated_count} records in {chunk_time:.2f}s")
            print(f"  Progress: {progress:.1f}% | Elapsed: {elapsed_time:.1f}s | Est. remaining: {remaining_time:.1f}s")
            
            conn.commit()
            
            if offset + chunk_size >= total_records:
                break
        
        total_time = time.time() - start_time
        print(f"\n✓ Updated {updated_total} records in {total_time:.2f} seconds")
        print(f"Average: {updated_total/total_time:.1f} records/second")

def verify_results(engine):
    """Verify the results of the test"""
    print("\nVerifying results...")
    
    with engine.connect() as conn:
        # Check how many records got foreign keys
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(department_agency_id) as records_with_fk,
                COUNT(CASE WHEN department_agency IS NOT NULL AND department_agency_id IS NULL THEN 1 END) as unmatched
            FROM test_archived_opportunities_10k
        """))
        
        stats = result.fetchone()
        print(f"Total records: {stats[0]}")
        print(f"Records with foreign key: {stats[1]}")
        print(f"Unmatched records: {stats[2]}")
        
        if stats[2] > 0:
            print("\nSample unmatched agency names:")
            unmatched = conn.execute(text("""
                SELECT DISTINCT department_agency, COUNT(*) as count
                FROM test_archived_opportunities_10k 
                WHERE department_agency IS NOT NULL 
                  AND department_agency_id IS NULL
                GROUP BY department_agency
                ORDER BY count DESC
                LIMIT 5
            """))
            
            for row in unmatched:
                print(f"  '{row[0]}' ({row[1]} records)")

def cleanup_test_tables(engine):
    """Clean up test tables"""
    print("\nCleaning up test tables...")
    
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS test_archived_opportunities_10k;
            DROP TABLE IF EXISTS test_department_agency;
        """))
        conn.commit()
        print("✓ Test tables cleaned up")

def main():
    # Database connection parameters
    db_params = {
        'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
        'port': os.getenv('supabase_port', '5432'),
        'database': os.getenv('supbase_database', 'postgres'),
        'user': os.getenv('supbaabase_username', 'postgres'),
        'password': os.getenv('supabase_pswd')
    }
    
    # Create SQLAlchemy engine
    engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    try:
        print("=== TESTING DEPARTMENT AGENCY SETUP ON 10K RECORDS ===\n")
        
        # Step 1: Create test table
        create_test_table(engine)
        
        # Step 2: Extract unique agencies
        agencies_df = extract_unique_agencies_test(engine)
        
        # Step 3: Create test department_agency table
        create_test_department_agency_table(engine)
        
        # Step 4: Load agencies
        load_agencies_to_test_table(engine, agencies_df)
        
        # Step 5: Test foreign key updates with progress
        test_foreign_key_update(engine)
        
        # Step 6: Verify results
        verify_results(engine)
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===")
        print("Review the results above. If everything looks good,")
        print("you can run the full script on all records.")
        
        # Ask if user wants to clean up
        cleanup = input("\nClean up test tables? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_tables(engine)
        else:
            print("Test tables preserved for further inspection.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()