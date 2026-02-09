-- Fix RLS policies for Supabase Auth
-- Run this in your Supabase SQL Editor

-- ============================================
-- FIX USERS TABLE RLS POLICIES
-- ============================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;

-- Recreate policies with INSERT support
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- IMPORTANT: Allow users to insert their own profile
-- This is needed if the trigger doesn't fire or for manual profile creation
CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- ============================================
-- SERVICE ROLE BYPASS (for backend operations)
-- ============================================

-- Allow service role to bypass RLS for all operations
-- This is critical for backend operations using the service role key
CREATE POLICY "Service role can manage all users" ON public.users
    FOR ALL USING (
        current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    );

-- ============================================
-- DONE!
-- ============================================
SELECT 'RLS policies fixed!' as status;
