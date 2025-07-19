-- Create department_agency lookup table
CREATE TABLE department_agency (
    id SERIAL PRIMARY KEY,
    agency_name TEXT UNIQUE NOT NULL,
    agency_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX idx_department_agency_name ON department_agency(agency_name);
CREATE INDEX idx_department_agency_code ON department_agency(agency_code);

-- Add foreign key constraint to archived_opportunities table
-- (Run this after populating the department_agency table)
-- ALTER TABLE archived_opportunities 
-- ADD COLUMN department_agency_id INTEGER,
-- ADD CONSTRAINT fk_department_agency 
-- FOREIGN KEY (department_agency_id) REFERENCES department_agency(id);

-- Create index on the foreign key
-- CREATE INDEX idx_archived_opportunities_department_agency_id ON archived_opportunities(department_agency_id);