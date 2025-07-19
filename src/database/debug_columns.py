#!/usr/bin/env python3
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_csv_columns():
    """Debug CSV column parsing"""
    csv_file = '/Users/daltonallen/Documents/projects/00-active/gov-contract/data/historical-opportnity-database/FY2015_archived_opportunities.csv'
    
    print("Testing CSV parsing...")
    
    # Try reading with different options
    try:
        df = pd.read_csv(
            csv_file, 
            low_memory=False, 
            encoding='latin-1',
            quoting=3,  # QUOTE_NONE - disable quote parsing
            escapechar='\\',  # Handle escaped characters
            on_bad_lines='skip',  # Skip problematic lines
            nrows=5  # Only read first 5 rows for testing
        )
        
        print("Original columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}: '{col}'")
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('"', '')
        
        print("\nCleaned columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}: '{col}'")
        
        # Test column mapping
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
        
        # Check which columns exist in the CSV
        print("\nChecking column mapping:")
        for csv_col, db_col in column_mapping.items():
            if csv_col in df.columns:
                print(f"  ✓ '{csv_col}' -> '{db_col}'")
            else:
                print(f"  ✗ '{csv_col}' -> '{db_col}' (NOT FOUND)")
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        print("\nFinal columns after mapping:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}: '{col}'")
        
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Sample data:")
        print(df.head(2))
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_csv_columns() 