-- Create table for archived opportunities (Supabase)
CREATE TABLE archived_opportunities (
    id SERIAL PRIMARY KEY,
    notice_id TEXT,
    title TEXT,
    solicitation_number TEXT,
    department_agency TEXT,
    cgac TEXT,
    sub_tier TEXT,
    fpds_code TEXT,
    office TEXT,
    aac_code TEXT,
    posted_date DATE,
    type TEXT,
    base_type TEXT,
    archive_type TEXT,
    archive_date DATE,
    set_aside_code TEXT,
    set_aside TEXT,
    response_deadline TIMESTAMP,
    naics_code TEXT,
    classification_code TEXT,
    pop_street_address TEXT,
    pop_city TEXT,
    pop_state TEXT,
    pop_zip TEXT,
    pop_country TEXT,
    active BOOLEAN,
    award_number TEXT,
    award_date DATE,
    award_amount DECIMAL(15,2),
    awardee TEXT,
    primary_contact_title TEXT,
    primary_contact_fullname TEXT,
    primary_contact_email TEXT,
    primary_contact_phone TEXT,
    primary_contact_fax TEXT,
    secondary_contact_title TEXT,
    secondary_contact_fullname TEXT,
    secondary_contact_email TEXT,
    secondary_contact_phone TEXT,
    secondary_contact_fax TEXT,
    organization_type TEXT,
    state TEXT,
    city TEXT,
    zip_code TEXT,
    country_code TEXT,
    additional_info_link TEXT,
    link TEXT,
    description TEXT,
    fiscal_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_notice_id ON archived_opportunities(notice_id);
CREATE INDEX idx_posted_date ON archived_opportunities(posted_date);
CREATE INDEX idx_department_agency ON archived_opportunities(department_agency);
CREATE INDEX idx_naics_code ON archived_opportunities(naics_code);
CREATE INDEX idx_fiscal_year ON archived_opportunities(fiscal_year);
CREATE INDEX idx_award_amount ON archived_opportunities(award_amount);

-- Add unique constraint on notice_id
ALTER TABLE archived_opportunities ADD CONSTRAINT unique_notice_id UNIQUE (notice_id);