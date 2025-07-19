# Government Contract Opportunities Database (Supabase)

This setup creates a Supabase PostgreSQL database for storing historical government contract opportunities data.

## Prerequisites

1. Supabase project with PostgreSQL database
2. Python 3.7+ with pip
3. Supabase database password

## Setup Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Database Schema
```bash
# Connect to your Supabase database using the SQL Editor in Supabase Dashboard
# Or use psql with your connection string:
psql "postgresql://postgres:[YOUR-PASSWORD]@db.urlshgkjcbwatvkjgda.supabase.co:5432/postgres"

# Run the SQL script to create tables
\i create_database.sql
```

### 3. Update Database Password
Edit the `password` field in `load_data.py` with your actual Supabase database password:
```python
db_params = {
    'host': 'db.urlshgkjcbwatvkjgda.supabase.co',
    'port': '6453',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'YOUR-ACTUAL-PASSWORD'  # Replace with your Supabase password
}
```

### 4. Load Data
```bash
python load_data.py
```

## Database Schema

The `archived_opportunities` table contains:
- Contract opportunity details (title, solicitation number, department)
- Contact information (primary/secondary contacts)
- Award information (amount, awardee, date)
- Location data (place of performance, organization location)
- Dates (posted, archive, response deadline)
- Classification codes (NAICS, FPDS)

## Key Features

- Automatic data type conversion (dates, currency, booleans)
- Fiscal year extraction from filenames
- Batch loading with progress tracking
- Comprehensive indexing for query performance
- Error handling for malformed data

## Querying Examples

```sql
-- Top 10 largest awards by fiscal year
SELECT fiscal_year, award_amount, title, awardee 
FROM archived_opportunities 
WHERE award_amount IS NOT NULL 
ORDER BY award_amount DESC 
LIMIT 10;

-- Opportunities by department
SELECT department_agency, COUNT(*) as opportunity_count
FROM archived_opportunities
GROUP BY department_agency
ORDER BY opportunity_count DESC;

-- Recent opportunities (last 30 days from archive date)
SELECT title, department_agency, posted_date, award_amount
FROM archived_opportunities
WHERE archive_date >= CURRENT_DATE - INTERVAL '30 days';
```