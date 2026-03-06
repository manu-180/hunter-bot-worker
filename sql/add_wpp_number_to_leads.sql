-- ============================================================
-- Migration: Add wpp_number column to leads table
-- ============================================================
-- Purpose: Store the WhatsApp number extracted from the lead's
-- website during scraping. Used by the Hunter Bot to send a
-- WhatsApp follow-up message immediately after the email is sent.
--
-- Run this in the Supabase SQL Editor once.
-- ============================================================

ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS wpp_number TEXT DEFAULT NULL;

COMMENT ON COLUMN leads.wpp_number IS
  'WhatsApp contact number extracted from the lead''s website. '
  'Used to send a follow-up WPP message after the outreach email is delivered.';
