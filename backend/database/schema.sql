-- Raimon Database Schema
-- Run this in your Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR_PROJECT/sql

-- ============================================
-- USERS & PREFERENCES
-- ============================================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- User preferences
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    energy_patterns JSONB DEFAULT '{}',
    work_style JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PROJECTS
-- ============================================

CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'completed')),
    priority INTEGER DEFAULT 0,
    color TEXT,
    icon TEXT,
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project details (goals, stakeholders, resources, etc.)
CREATE TABLE IF NOT EXISTS public.project_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID UNIQUE REFERENCES public.projects(id) ON DELETE CASCADE,
    goals JSONB DEFAULT '[]',
    stakeholders JSONB DEFAULT '[]',
    resources JSONB DEFAULT '[]',
    milestones JSONB DEFAULT '[]',
    deadline TIMESTAMPTZ,
    people JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TASKS
-- ============================================

CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'paused', 'on_break', 'blocked', 'completed')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    estimated_duration INTEGER, -- in minutes
    actual_duration INTEGER, -- in minutes
    deadline TIMESTAMPTZ,
    tags TEXT[] DEFAULT '{}',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task dependencies
CREATE TABLE IF NOT EXISTS public.task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, depends_on_task_id)
);

-- ============================================
-- WORK SESSIONS & STATE TRACKING
-- ============================================

-- Work sessions (time tracking)
CREATE TABLE IF NOT EXISTS public.work_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    energy_before INTEGER CHECK (energy_before BETWEEN 1 AND 10),
    energy_after INTEGER CHECK (energy_after BETWEEN 1 AND 10),
    interruptions INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily check-ins
CREATE TABLE IF NOT EXISTS public.daily_check_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    mood TEXT,
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),
    blockers JSONB DEFAULT '[]',
    focus_areas JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- User states (current working state)
CREATE TABLE IF NOT EXISTS public.user_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'idle',
    current_task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    energy_level INTEGER,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session contexts (for context continuity)
CREATE TABLE IF NOT EXISTS public.session_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    context_data JSONB DEFAULT '{}',
    last_task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, session_date)
);

-- ============================================
-- AI & LEARNING
-- ============================================

-- AI learning data
CREATE TABLE IF NOT EXISTS public.ai_learning_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    agent_type TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task time predictions
CREATE TABLE IF NOT EXISTS public.task_time_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    predicted_duration INTEGER,
    actual_duration INTEGER,
    accuracy FLOAT,
    factors JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stuck pattern detections
CREATE TABLE IF NOT EXISTS public.stuck_pattern_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    pattern_type TEXT,
    description TEXT,
    severity TEXT DEFAULT 'medium',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    suggested_actions JSONB DEFAULT '[]',
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project insights
CREATE TABLE IF NOT EXISTS public.project_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    insight_type TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- GAMIFICATION
-- ============================================

-- Streaks
CREATE TABLE IF NOT EXISTS public.streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    streak_type TEXT NOT NULL,
    current_count INTEGER DEFAULT 0,
    longest_count INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, streak_type)
);

-- Achievements (definitions)
CREATE TABLE IF NOT EXISTS public.achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT,
    points INTEGER DEFAULT 0,
    requirements JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User achievements (earned)
CREATE TABLE IF NOT EXISTS public.user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES public.achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- ============================================
-- NOTIFICATIONS & REMINDERS
-- ============================================

-- Notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reminders
CREATE TABLE IF NOT EXISTS public.reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    message TEXT,
    remind_at TIMESTAMPTZ NOT NULL,
    frequency TEXT DEFAULT 'once',
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INTEGRATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS public.integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    integration_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    credentials JSONB DEFAULT '{}', -- encrypted in production
    settings JSONB DEFAULT '{}',
    connected_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, integration_type)
);

-- ============================================
-- INDEXES
-- ============================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Projects
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_user_status ON public.projects(user_id, status);

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON public.tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON public.tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON public.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON public.tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON public.tasks(deadline);

-- Work sessions
CREATE INDEX IF NOT EXISTS idx_work_sessions_user_id ON public.work_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_task_id ON public.work_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_start_time ON public.work_sessions(start_time);

-- Daily check-ins
CREATE INDEX IF NOT EXISTS idx_daily_check_ins_user_date ON public.daily_check_ins(user_id, date);

-- Notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(user_id, read);

-- AI learning data
CREATE INDEX IF NOT EXISTS idx_ai_learning_user_agent ON public.ai_learning_data(user_id, agent_type);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.work_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_check_ins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_learning_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_time_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stuck_pattern_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integrations ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can only access their own data

CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can manage own preferences" ON public.user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own projects" ON public.projects
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own project details" ON public.project_details
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects WHERE id = project_id AND user_id = auth.uid())
    );

CREATE POLICY "Users can manage own tasks" ON public.tasks
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own task dependencies" ON public.task_dependencies
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.tasks WHERE id = task_id AND user_id = auth.uid())
    );

CREATE POLICY "Users can manage own work sessions" ON public.work_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own check-ins" ON public.daily_check_ins
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own states" ON public.user_states
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own session contexts" ON public.session_contexts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own AI data" ON public.ai_learning_data
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own time predictions" ON public.task_time_predictions
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.tasks WHERE id = task_id AND user_id = auth.uid())
    );

CREATE POLICY "Users can manage own stuck patterns" ON public.stuck_pattern_detections
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own project insights" ON public.project_insights
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.projects WHERE id = project_id AND user_id = auth.uid())
    );

CREATE POLICY "Users can manage own streaks" ON public.streaks
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Anyone can view achievements" ON public.achievements
    FOR SELECT USING (true);

CREATE POLICY "Users can manage own earned achievements" ON public.user_achievements
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own notifications" ON public.notifications
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own reminders" ON public.reminders
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own integrations" ON public.integrations
    FOR ALL USING (auth.uid() = user_id);

-- ============================================
-- TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_project_details_updated_at
    BEFORE UPDATE ON public.project_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_daily_check_ins_updated_at
    BEFORE UPDATE ON public.daily_check_ins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_session_contexts_updated_at
    BEFORE UPDATE ON public.session_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_streaks_updated_at
    BEFORE UPDATE ON public.streaks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_reminders_updated_at
    BEFORE UPDATE ON public.reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_integrations_updated_at
    BEFORE UPDATE ON public.integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- AUTO-CREATE USER PROFILE ON SIGNUP
-- ============================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'name');

    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- SEED DATA (Optional)
-- ============================================

-- Insert some default achievements
INSERT INTO public.achievements (name, description, icon, category, points) VALUES
    ('First Task', 'Complete your first task', '🎯', 'beginner', 10),
    ('Week Warrior', 'Check in 7 days in a row', '🔥', 'streak', 50),
    ('Focus Master', 'Complete 4 hours of focus time in one day', '🧘', 'focus', 75),
    ('Project Pioneer', 'Create your first project', '🚀', 'beginner', 15),
    ('Task Crusher', 'Complete 10 tasks', '💪', 'productivity', 30),
    ('Century Club', 'Complete 100 tasks', '🏆', 'productivity', 200),
    ('Early Bird', 'Complete a task before 9 AM', '🌅', 'time', 25),
    ('Night Owl', 'Complete a task after 10 PM', '🦉', 'time', 25),
    ('Consistency King', 'Maintain a 30-day check-in streak', '👑', 'streak', 150)
ON CONFLICT DO NOTHING;

-- ============================================
-- DONE!
-- ============================================
SELECT 'Schema created successfully!' as status;
