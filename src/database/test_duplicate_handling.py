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

def test_duplicate_handling():
    """Test the duplicate handling logic"""
    csv_file_path = '/Users/daltonallen/Documents/projects/00-active/gov-contract/data/historical-opportnity-database/FY2015_archived_opportunities.csv'
    
    print(f"Testing duplicate handling with {csv_file_path}...")
    
    # Database connection
    db_params = {
        'host': os.getenv('supabase_url', 'db.urilshgkjcbwatvkjgda.supabase.co'),
        'port': os.getenv('supabase_port', '6543'),
        'database': os.getenv('supbase_database', 'postgres'),
        'user': os.getenv('supbaabase_username', 'postgres'),
        'password': os.getenv('supabase_pswd')
    }
    
    engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    # Read a small sample
    df = pd.read_csv(
        csv_file_path, 
        encoding='latin-1',
        quoting=1,
        escapechar='\\',
        on_bad_lines='skip',
        engine='python',
        nrows=20  # Read 20 rows for testing
    )
    
    print(f"  Read {len(df)} rows from CSV")
    
    # Clean column names
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    # Column mapping
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
    df['fiscal_year'] = 2015
    
    # Get existing notice_ids
    with engine.connect() as conn:
        existing_notice_ids = set()
        result = conn.execute(text("SELECT notice_id FROM archived_opportunities WHERE notice_id IS NOT NULL"))
        for row in result:
            existing_notice_ids.add(row[0])
    
    print(f"  Found {len(existing_notice_ids)} existing notice_ids in database")
    
    # Check which records would be duplicates
    if 'notice_id' in df.columns:
        original_count = len(df)
        duplicates = df[df['notice_id'].isin(existing_notice_ids)]
        new_records = df[~df['notice_id'].isin(existing_notice_ids)]
        
        print(f"  Original records: {original_count}")
        print(f"  Duplicate records: {len(duplicates)}")
        print(f"  New records: {len(new_records)}")
        
        if len(duplicates) > 0:
            print(f"  Sample duplicate notice_ids: {list(duplicates['notice_id'].head(3))}")
        
        if len(new_records) > 0:
            print(f"  Sample new notice_ids: {list(new_records['notice_id'].head(3))}")
    
    print("  ✓ Duplicate handling test completed")

if __name__ == "__main__":
    test_duplicate_handling() 