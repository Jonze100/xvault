-- =============================================================================
-- Migration 002: Add risk_score to treasury_snapshots
-- Run in Supabase SQL Editor after 001_initial_schema.sql
-- =============================================================================

-- Add risk_score column (silently ignored if column already exists)
ALTER TABLE treasury_snapshots
  ADD COLUMN IF NOT EXISTS risk_score integer DEFAULT 0;

-- Make treasury_id nullable so Portfolio Agent can insert without
-- requiring a parent treasury record to exist first.
ALTER TABLE treasury_snapshots
  ALTER COLUMN treasury_id DROP NOT NULL;
