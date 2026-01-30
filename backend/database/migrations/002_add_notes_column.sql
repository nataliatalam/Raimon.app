-- Migration: Add notes column to project_details
-- Run this in your Supabase SQL Editor

-- Add notes column to project_details table
ALTER TABLE public.project_details
ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================
-- DONE!
-- ============================================
SELECT 'Notes column added to project_details!' as status;
