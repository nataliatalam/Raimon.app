-- Calendar Events table for Google Calendar integration
-- Used for AI training on user's schedule patterns

CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Google Calendar identifiers
    google_event_id TEXT NOT NULL,
    google_calendar_id TEXT NOT NULL DEFAULT 'primary',

    -- Event details
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,

    -- Timing
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN DEFAULT FALSE,
    timezone TEXT,

    -- Recurrence
    recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT,  -- RRULE string
    recurring_event_id TEXT,  -- Parent event ID for recurring instances

    -- Event metadata
    event_type TEXT,  -- 'meeting', 'focus_time', 'personal', 'travel', etc.
    attendees_count INTEGER DEFAULT 0,
    is_organizer BOOLEAN DEFAULT TRUE,
    status TEXT DEFAULT 'confirmed',  -- 'confirmed', 'tentative', 'cancelled'
    visibility TEXT DEFAULT 'default',  -- 'default', 'public', 'private'

    -- AI training metadata
    color_id TEXT,
    busy_status TEXT DEFAULT 'busy',  -- 'busy', 'free'

    -- Sync metadata
    etag TEXT,  -- For incremental sync
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint to prevent duplicates
    UNIQUE(user_id, google_event_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_end_time ON calendar_events(end_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_time ON calendar_events(user_id, start_time, end_time);

-- Google OAuth tokens storage
CREATE TABLE IF NOT EXISTS google_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    expires_at TIMESTAMPTZ NOT NULL,
    scope TEXT,

    -- Sync state
    calendar_sync_token TEXT,  -- For incremental sync
    last_synced_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_google_oauth_user_id ON google_oauth_tokens(user_id);

-- AI Calendar Insights table (for AI to learn scheduling patterns)
CREATE TABLE IF NOT EXISTS calendar_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Time patterns
    insight_type TEXT NOT NULL,  -- 'peak_hours', 'meeting_heavy_days', 'focus_blocks', 'overbooked_risk'
    insight_data JSONB NOT NULL,

    -- Validity
    valid_from DATE NOT NULL,
    valid_until DATE,
    confidence_score FLOAT DEFAULT 0.0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_insights_user_id ON calendar_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_insights_type ON calendar_insights(insight_type);

-- Enable RLS
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_insights ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own calendar events" ON calendar_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own calendar events" ON calendar_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own calendar events" ON calendar_events
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own calendar events" ON calendar_events
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own oauth tokens" ON google_oauth_tokens
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own oauth tokens" ON google_oauth_tokens
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own calendar insights" ON calendar_insights
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own calendar insights" ON calendar_insights
    FOR ALL USING (auth.uid() = user_id);
