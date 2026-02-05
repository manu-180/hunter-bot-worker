-- ============================================
-- LeadSniper Database Schema for Supabase
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- LEADS TABLE
-- ============================================
-- Stores all scraped domains and their contact information
CREATE TABLE IF NOT EXISTS leads (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Domain information
    domain TEXT NOT NULL UNIQUE,
    
    -- Extracted data
    email TEXT,
    meta_title TEXT,
    
    -- Status tracking
    -- Possible values: pending, scraping, scraped, queued_for_send, sending, sent, failed
    status TEXT NOT NULL DEFAULT 'pending',
    
    -- Error tracking
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scraped_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ
);

-- ============================================
-- INDEXES
-- ============================================
-- Index for fetching pending domains (most common query)
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

-- Index for fetching domains ready to send emails
CREATE INDEX IF NOT EXISTS idx_leads_queued_for_send ON leads(status) 
    WHERE status = 'queued_for_send';

-- Index for fetching pending domains
CREATE INDEX IF NOT EXISTS idx_leads_pending ON leads(status) 
    WHERE status = 'pending';

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================
-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to call the function on update
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (Optional - for Supabase)
-- ============================================
-- Enable RLS on leads table
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all for authenticated users" ON leads
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================
-- Uncomment to insert test data
/*
INSERT INTO leads (domain, status) VALUES
    ('example-company.com', 'pending'),
    ('another-business.io', 'pending'),
    ('tech-startup.co', 'pending');
*/
