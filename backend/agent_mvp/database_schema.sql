-- SQL for 8 new database tables to support full agent flow
-- Execute these in Supabase SQL editor in order

-- 1. active_do - Current active task/session
CREATE TABLE active_do (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task JSONB NOT NULL, -- Full task data
    selection_reason TEXT NOT NULL,
    coaching_message TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id)
);

-- 2. session_state - User session state persistence
CREATE TABLE session_state (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id)
);

-- 3. stuck_episodes - Stuck detection history
CREATE TABLE stuck_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL,
    session_id UUID,
    stuck_reason TEXT NOT NULL,
    time_stuck INTEGER NOT NULL, -- minutes
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    microtasks_used JSONB -- array of microtask descriptions
);

-- 4. time_models - Time pattern learning data
CREATE TABLE time_models (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    patterns JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id)
);

-- 5. insights - Generated insights storage
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    insights JSONB NOT NULL, -- array of insight objects
    motivation TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. gamification_state - User gamification data
CREATE TABLE gamification_state (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id)
);

-- 7. xp_ledger - XP transaction history
CREATE TABLE xp_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action TEXT NOT NULL, -- e.g., 'task_completed', 'session_completed'
    xp_gained INTEGER NOT NULL,
    total_xp_after INTEGER NOT NULL,
    metadata JSONB, -- additional context
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. agent_events - Event logging for agents
CREATE TABLE agent_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- NULL for system events
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_active_do_user_id ON active_do(user_id);
CREATE INDEX idx_session_state_user_id ON session_state(user_id);
CREATE INDEX idx_stuck_episodes_user_id ON stuck_episodes(user_id);
CREATE INDEX idx_stuck_episodes_detected_at ON stuck_episodes(detected_at);
CREATE INDEX idx_time_models_user_id ON time_models(user_id);
CREATE INDEX idx_insights_user_id ON insights(user_id);
CREATE INDEX idx_insights_date ON insights(date);
CREATE INDEX idx_gamification_state_user_id ON gamification_state(user_id);
CREATE INDEX idx_xp_ledger_user_id ON xp_ledger(user_id);
CREATE INDEX idx_xp_ledger_timestamp ON xp_ledger(timestamp);
CREATE INDEX idx_agent_events_user_id ON agent_events(user_id);
CREATE INDEX idx_agent_events_event_type ON agent_events(event_type);
CREATE INDEX idx_agent_events_timestamp ON agent_events(timestamp);

-- Row Level Security (RLS) policies
ALTER TABLE active_do ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE stuck_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE gamification_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE xp_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can access own active_do" ON active_do
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own session_state" ON session_state
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own stuck_episodes" ON stuck_episodes
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own time_models" ON time_models
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own insights" ON insights
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own gamification_state" ON gamification_state
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own xp_ledger" ON xp_ledger
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own agent_events" ON agent_events
    FOR ALL USING (auth.uid() = user_id);

-- Allow system events (user_id is NULL)
CREATE POLICY "System can log agent_events" ON agent_events
    FOR INSERT WITH CHECK (user_id IS NULL);