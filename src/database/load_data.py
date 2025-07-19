#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_currency_value(value):
    """Clean currency values and convert to float"""
    if pd.isna(value) or value == '':
        return None
    
    # Remove currency symbols, commas, and whitespace
    cleaned = re.sub(r'[$,\s]', '', str(value))
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def clean_date_value(value):
    """Clean date values"""
    if pd.isna(value) or value == '':
        return None
    return value

def clean_boolean_value(value):
    """Convert string boolean values to actual booleans"""
    if pd.isna(value) or value == '':
        return None
    
    if str(value).lower() in ['true', 'yes', '1', 'y']:
        return True
    elif str(value).lower() in ['false', 'no', '0', 'n']:
        return False
    else:
        return None

def extract_fiscal_year(filename):
    """Extract fiscal year from filename"""
    match = re.search(r'FY(\d{4})', filename)
    return int(match.group(1)) if match else None

def load_csv_to_postgres(csv_file_path, engine, fiscal_year):
    """Load a single CSV file to PostgreSQL"""
    print(f"Loading {csv_file_path}...")
    
    # Try different encodings to handle malformed CSV files
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None
    
    for encoding in encodings:
        try:
            # Try with more robust CSV parsing options
            df = pd.read_csv(
                csv_file_path, 
                encoding=encoding,
                quoting=1,  # QUOTE_ALL - handle quoted fields properly
                escapechar='\\',  # Handle escaped characters
                on_bad_lines='skip',  # Skip problematic lines
                engine='python'  # Use Python engine for better error handling
            )
            print(f"  Successfully read with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  Failed with {encoding} encoding: {str(e)}")
            continue
    
    if df is None:
        print(f"  Error: Could not read file with any encoding")
        return
    
    # If the file is very large and has issues, try reading in chunks
    if len(df) == 0:
        print(f"  Trying chunked reading approach...")
        try:
            # Read file in chunks to handle malformed data
            chunk_size = 10000
            chunks = []
            
            for encoding in encodings:
                try:
                    chunk_reader = pd.read_csv(
                        csv_file_path,
                        encoding=encoding,
                        quoting=1,
                        escapechar='\\',
                        on_bad_lines='skip',
                        engine='python',
                        chunksize=chunk_size
                    )
                    
                    for chunk in chunk_reader:
                        if len(chunk) > 0:
                            chunks.append(chunk)
                    
                    if chunks:
                        df = pd.concat(chunks, ignore_index=True)
                        print(f"  Successfully read {len(df)} rows using chunked approach with {encoding} encoding")
                        break
                        
                except Exception as e:
                    print(f"  Chunked approach failed with {encoding} encoding: {str(e)}")
                    continue
            
            if df is None or len(df) == 0:
                print(f"  Error: Could not read file even with chunked approach")
                return
                
        except Exception as e:
            print(f"  Error with chunked reading: {str(e)}")
            return
    
    # Clean column names by removing quotes and extra whitespace
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    # Clean column names to match database schema
    column_mapping = {
        'NoticeId': 'notice_id',
        'Title': 'title',
        'Sol#': 'solicitation_number',
        'Department/Ind.Agency': 'department_agency',
        'CGAC': 'cgac',
        'Sub-Tier': 'sub_tier',
        'FPDS Code': 'fpds_code',
        'Office': 'office',
        'AAC Code': 'aac_code',
        'PostedDate': 'posted_date',
        'Type': 'type',
        'BaseType': 'base_type',
        'ArchiveType': 'archive_type',
        'ArchiveDate': 'archive_date',
        'SetASideCode': 'set_aside_code',
        'SetASide': 'set_aside',
        'ResponseDeadLine': 'response_deadline',
        'NaicsCode': 'naics_code',
        'ClassificationCode': 'classification_code',
        'PopStreetAddress': 'pop_street_address',
        'PopCity': 'pop_city',
        'PopState': 'pop_state',
        'PopZip': 'pop_zip',
        'PopCountry': 'pop_country',
        'Active': 'active',
        'AwardNumber': 'award_number',
        'AwardDate': 'award_date',
        'Award$': 'award_amount',
        'Awardee': 'awardee',
        'PrimaryContactTitle': 'primary_contact_title',
        'PrimaryContactFullname': 'primary_contact_fullname',
        'PrimaryContactEmail': 'primary_contact_email',
        'PrimaryContactPhone': 'primary_contact_phone',
        'PrimaryContactFax': 'primary_contact_fax',
        'SecondaryContactTitle': 'secondary_contact_title',
        'SecondaryContactFullname': 'secondary_contact_fullname',
        'SecondaryContactEmail': 'secondary_contact_email',
        'SecondaryContactPhone': 'secondary_contact_phone',
        'SecondaryContactFax': 'secondary_contact_fax',
        'OrganizationType': 'organization_type',
        'State': 'state',
        'City': 'city',
        'ZipCode': 'zip_code',
        'CountryCode': 'country_code',
        'AdditionalInfoLink': 'additional_info_link',
        'Link': 'link',
        'Description': 'description'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Add fiscal year column
    df['fiscal_year'] = fiscal_year
    
    # Clean data types - only if columns exist
    if 'award_amount' in df.columns:
        df['award_amount'] = df['award_amount'].apply(clean_currency_value)
    if 'active' in df.columns:
        df['active'] = df['active'].apply(clean_boolean_value)
    
    # Convert date columns
    date_columns = ['posted_date', 'archive_date', 'award_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'response_deadline' in df.columns:
        df['response_deadline'] = pd.to_datetime(df['response_deadline'], errors='coerce')
    
    # Load to database with duplicate handling
    try:
        # First, try to add the unique constraint if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'unique_notice_id'
                    ) THEN
                        ALTER TABLE archived_opportunities ADD CONSTRAINT unique_notice_id UNIQUE (notice_id);
                    END IF;
                END $$;
            """))
            conn.commit()
        
        # Get existing notice_ids to avoid duplicates
        with engine.connect() as conn:
            existing_notice_ids = set()
            result = conn.execute(text("SELECT notice_id FROM archived_opportunities WHERE notice_id IS NOT NULL"))
            for row in result:
                existing_notice_ids.add(row[0])
        
        # Filter out records that already exist
        if 'notice_id' in df.columns:
            original_count = len(df)
            df = df[~df['notice_id'].isin(existing_notice_ids)]
            skipped_count = original_count - len(df)
            if skipped_count > 0:
                print(f"  Skipped {skipped_count} existing records")
        
        # Load to database
        if len(df) > 0:
            df.to_sql('archived_opportunities', engine, if_exists='append', index=False, method='multi', chunksize=1000)
            print(f"Loaded {len(df)} new records from {csv_file_path}")
        else:
            print(f"No new records to load from {csv_file_path}")
        
    except Exception as e:
        print(f"Error during database load: {str(e)}")
        # Fallback to regular insert if the constraint method fails
        df.to_sql('archived_opportunities', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print(f"Loaded {len(df)} records using fallback method")

def main():
    # Supabase database connection parameters from environment
    db_params = {
        'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
        'port': os.getenv('supabase_port', '5432'),
        'database': os.getenv('supbase_database', 'postgres'),
        'user': os.getenv('supbaabase_username', 'postgres'),
        'password': os.getenv('supabase_pswd')
    }
    
    # Create SQLAlchemy engine for Supabase
    engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    # Directory containing CSV files
    data_dir = '/Users/daltonallen/Documents/projects/00-active/gov-contract/data/historical-opportnity-database'
    
    # Get all CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    csv_files.sort()
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    for csv_file in csv_files:
        csv_path = os.path.join(data_dir, csv_file)
        fiscal_year = extract_fiscal_year(csv_file)
        
        try:
            load_csv_to_postgres(csv_path, engine, fiscal_year)
        except Exception as e:
            print(f"Error loading {csv_file}: {str(e)}")
            continue
    
    print("Data loading completed!")

if __name__ == "__main__":
    main()