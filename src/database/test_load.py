#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_load_small_sample():
    """Test loading a small sample of data"""
    csv_file_path = '/Users/daltonallen/Documents/projects/00-active/gov-contract/data/historical-opportnity-database/FY2015_archived_opportunities.csv'
    
    print(f"Testing load with {csv_file_path}...")
    
    # Try reading with proper quote handling
    try:
        df = pd.read_csv(
            csv_file_path, 
            low_memory=False, 
            encoding='latin-1',
            quoting=1,  # QUOTE_ALL - handle quoted fields properly
            escapechar='\\',  # Handle escaped characters
            on_bad_lines='skip',  # Skip problematic lines
            nrows=10  # Only read first 10 rows for testing
        )
        
        print(f"  Successfully read {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        
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
        df['fiscal_year'] = 2015
        
        # Clean data types - only if columns exist
        if 'award_amount' in df.columns:
            df['award_amount'] = df['award_amount'].apply(lambda x: None if pd.isna(x) or x == '' else float(str(x).replace('$', '').replace(',', '')) if str(x).replace('$', '').replace(',', '').replace('.', '').isdigit() else None)
        if 'active' in df.columns:
            df['active'] = df['active'].apply(lambda x: True if str(x).lower() in ['true', 'yes', '1', 'y'] else False if str(x).lower() in ['false', 'no', '0', 'n'] else None)
        
        # Convert date columns
        date_columns = ['posted_date', 'archive_date', 'award_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if 'response_deadline' in df.columns:
            df['response_deadline'] = pd.to_datetime(df['response_deadline'], errors='coerce')
        
        print(f"  Final columns: {list(df.columns)}")
        print(f"  Sample data:")
        print(df[['notice_id', 'title', 'award_amount', 'fiscal_year']].head(3))
        
        # Test database connection and load
        db_params = {
            'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
            'port': os.getenv('supabase_port', '5432'),
            'database': os.getenv('supbase_database', 'postgres'),
            'user': os.getenv('supbaabase_username', 'postgres'),
            'password': os.getenv('supabase_pswd')
        }
        
        engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
        
        # Load to database
        df.to_sql('archived_opportunities', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print(f"  ✓ Successfully loaded {len(df)} records to database")
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

if __name__ == "__main__":
    test_load_small_sample() 