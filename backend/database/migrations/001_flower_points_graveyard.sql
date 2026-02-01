-- Migration: Flower Points & Graveyard System
-- Run this in your Supabase SQL Editor

-- ============================================
-- FLOWER POINTS SYSTEM
-- ============================================

-- User flower points balance
CREATE TABLE IF NOT EXISTS public.user_flower_points (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    balance INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Flower point transactions history
CREATE TABLE IF NOT EXISTS public.flower_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('earned', 'spent')),
    reason TEXT NOT NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- GRAVEYARD SYSTEM
-- ============================================

-- Graveyard metadata for archived projects
CREATE TABLE IF NOT EXISTS public.graveyard_meta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    epitaph TEXT,
    expiry_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

-- Flowers placed on graves
CREATE TABLE IF NOT EXISTS public.graveyard_flowers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graveyard_meta_id UUID REFERENCES public.graveyard_meta(id) ON DELETE CASCADE,
    flower_id TEXT NOT NULL,
    flower_name TEXT NOT NULL,
    flower_emoji TEXT NOT NULL,
    cost INTEGER NOT NULL,
    days_added INTEGER NOT NULL,
    placed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PROJECT FILES
-- ============================================

-- Files attached to projects
CREATE TABLE IF NOT EXISTS public.project_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_flower_transactions_user_id ON public.flower_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_flower_transactions_project_id ON public.flower_transactions(project_id);
CREATE INDEX IF NOT EXISTS idx_graveyard_meta_user_id ON public.graveyard_meta(user_id);
CREATE INDEX IF NOT EXISTS idx_graveyard_meta_project_id ON public.graveyard_meta(project_id);
CREATE INDEX IF NOT EXISTS idx_graveyard_flowers_meta_id ON public.graveyard_flowers(graveyard_meta_id);
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON public.project_files(project_id);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE public.user_flower_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flower_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.graveyard_meta ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.graveyard_flowers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_files ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage own flower points" ON public.user_flower_points
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own flower transactions" ON public.flower_transactions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own graveyard meta" ON public.graveyard_meta
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own graveyard flowers" ON public.graveyard_flowers
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.graveyard_meta WHERE id = graveyard_meta_id AND user_id = auth.uid())
    );

CREATE POLICY "Users can manage own project files" ON public.project_files
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects WHERE id = project_id AND user_id = auth.uid())
    );

-- ============================================
-- TRIGGERS
-- ============================================

CREATE TRIGGER update_user_flower_points_updated_at
    BEFORE UPDATE ON public.user_flower_points
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_graveyard_meta_updated_at
    BEFORE UPDATE ON public.graveyard_meta
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- AUTO-CREATE FLOWER POINTS ON USER CREATION
-- ============================================

-- Update the handle_new_user function to also create flower points
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'name');

    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id);

    INSERT INTO public.user_flower_points (user_id, balance)
    VALUES (NEW.id, 30);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- DONE!
-- ============================================
SELECT 'Flower points and graveyard tables created successfully!' as status;
