-- Agent MVP Tables Migration
-- Creates tables needed for the agent orchestration system

-- =====================================================
-- 1. active_do - Current active task/session for user
-- =====================================================
CREATE TABLE IF NOT EXISTS active_do (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task JSONB NOT NULL,
    selection_reason TEXT,
    coaching_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- RLS for active_do
ALTER TABLE active_do ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own active_do"
    ON active_do FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own active_do"
    ON active_do FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own active_do"
    ON active_do FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own active_do"
    ON active_do FOR DELETE
    USING (auth.uid() = user_id);


-- =====================================================
-- 2. session_state - User session state persistence
-- =====================================================
CREATE TABLE IF NOT EXISTS session_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- RLS for session_state
ALTER TABLE session_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own session_state"
    ON session_state FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own session_state"
    ON session_state FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own session_state"
    ON session_state FOR UPDATE
    USING (auth.uid() = user_id);


-- =====================================================
-- 3. stuck_episodes - Stuck detection history
-- =====================================================
CREATE TABLE IF NOT EXISTS stuck_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    session_id UUID REFERENCES work_sessions(id) ON DELETE SET NULL,
    stuck_reason TEXT,
    time_stuck INTEGER,  -- minutes
    intervention_type TEXT,  -- break, microtask, alt_task, coach
    microtasks JSONB,
    resolved_at TIMESTAMPTZ,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS for stuck_episodes
ALTER TABLE stuck_episodes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own stuck_episodes"
    ON stuck_episodes FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own stuck_episodes"
    ON stuck_episodes FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- =====================================================
-- 4. time_models - Time pattern learning data
-- =====================================================
CREATE TABLE IF NOT EXISTS time_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    patterns JSONB NOT NULL DEFAULT '{}',
    peak_hours INTEGER[] DEFAULT '{}',
    optimal_durations JSONB DEFAULT '{}',
    day_patterns JSONB DEFAULT '{}',
    time_efficiency FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- RLS for time_models
ALTER TABLE time_models ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own time_models"
    ON time_models FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert their own time_models"
    ON time_models FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own time_models"
    ON time_models FOR UPDATE
    USING (auth.uid() = user_id);


-- =====================================================
-- 5. insights - Generated insights storage
-- =====================================================
CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    insight_type TEXT DEFAULT 'daily',
    insights JSONB NOT NULL DEFAULT '[]',
    motivation TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS for insights
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own insights"
    ON insights FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own insights"
    ON insights FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- =====================================================
-- 6. gamification_state - User gamification data
-- =====================================================
CREATE TABLE IF NOT EXISTS gamification_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    freezes_remaining INTEGER DEFAULT 0,
    achievements JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- RLS for gamification_state
ALTER TABLE gamification_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own gamification_state"
    ON gamification_state FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert their own gamification_state"
    ON gamification_state FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own gamification_state"
    ON gamification_state FOR UPDATE
    USING (auth.uid() = user_id);


-- =====================================================
-- 7. xp_ledger - XP transaction history
-- =====================================================
CREATE TABLE IF NOT EXISTS xp_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- task_completed, streak_maintain, level_up, day_completed
    xp_gained INTEGER NOT NULL,
    total_xp_after INTEGER NOT NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS for xp_ledger
ALTER TABLE xp_ledger ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own xp_ledger"
    ON xp_ledger FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own xp_ledger"
    ON xp_ledger FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_xp_ledger_user_timestamp ON xp_ledger(user_id, timestamp DESC);


-- =====================================================
-- 8. agent_events - Event logging for agents
-- =====================================================
CREATE TABLE IF NOT EXISTS agent_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- APP_OPEN, CHECKIN_SUBMITTED, DO_NEXT, DO_ACTION, DAY_END
    event_data JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    result JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS for agent_events
ALTER TABLE agent_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own agent_events"
    ON agent_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own agent_events"
    ON agent_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_agent_events_user_type ON agent_events(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_agent_events_timestamp ON agent_events(timestamp DESC);


-- =====================================================
-- 9. ai_learning_data - AI learning data storage
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_learning_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,  -- user_profile, time_model, stuck_patterns, etc.
    data JSONB NOT NULL DEFAULT '{}',
    expires_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, agent_type)
);

-- RLS for ai_learning_data
ALTER TABLE ai_learning_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own ai_learning_data"
    ON ai_learning_data FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert their own ai_learning_data"
    ON ai_learning_data FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own ai_learning_data"
    ON ai_learning_data FOR UPDATE
    USING (auth.uid() = user_id);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_ai_learning_user_agent ON ai_learning_data(user_id, agent_type);


-- =====================================================
-- Service role policies for backend access
-- =====================================================

-- active_do
CREATE POLICY "Service role can manage active_do"
    ON active_do FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- session_state
CREATE POLICY "Service role can manage session_state"
    ON session_state FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- stuck_episodes
CREATE POLICY "Service role can manage stuck_episodes"
    ON stuck_episodes FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- time_models
CREATE POLICY "Service role can manage time_models"
    ON time_models FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- insights
CREATE POLICY "Service role can manage insights"
    ON insights FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- gamification_state
CREATE POLICY "Service role can manage gamification_state"
    ON gamification_state FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- xp_ledger
CREATE POLICY "Service role can manage xp_ledger"
    ON xp_ledger FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- agent_events
CREATE POLICY "Service role can manage agent_events"
    ON agent_events FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ai_learning_data
CREATE POLICY "Service role can manage ai_learning_data"
    ON ai_learning_data FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
