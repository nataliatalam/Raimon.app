# Entity Relationship Diagram

## Core Relationships

```
users (1) ──── (M) projects
users (1) ──── (M) tasks
users (1) ──── (1) user_preferences
users (1) ──── (M) daily_check_ins
users (1) ──── (M) work_sessions
users (1) ──── (M) user_states
users (1) ──── (M) notifications
users (1) ──── (M) reminders
users (1) ──── (M) streaks
users (1) ──── (M) user_achievements
users (1) ──── (M) integrations
users (1) ──── (M) ai_learning_data

projects (1) ──── (1) project_details
projects (1) ──── (M) tasks
projects (1) ──── (M) project_insights

tasks (1) ──── (M) work_sessions
tasks (1) ──── (M) task_time_predictions
tasks (1) ──── (M) stuck_pattern_detections
tasks (1) ──── (M) task_dependencies (as task_id)
tasks (1) ──── (M) task_dependencies (as depends_on_task_id)
tasks (1) ──── (1) tasks (as parent_task_id, self-referential)

achievements (1) ──── (M) user_achievements

user_states (M) ──── (1) tasks (as current_task_id)
```

## Key Indexes

### Performance Optimization
- All foreign keys are indexed
- Timestamp fields (created_at, updated_at, started_at, completed_at) are indexed
- Status and priority fields are indexed for filtering
- Email fields are indexed for authentication
- Composite unique constraints on user-date relationships

### Common Query Patterns
1. Get user's active projects: `user_id + status`
2. Get today's tasks: `user_id + deadline + status`
3. Get recent work sessions: `user_id + start_time`
4. Get current user state: `user_id + ended_at IS NULL`
5. Get unread notifications: `user_id + read = false`

## Data Integrity Rules

### Cascading Deletes
- When user deleted → all related data deleted (CASCADE)
- When project deleted → tasks deleted (CASCADE)
- When task deleted → work_sessions keep reference (SET NULL)
- When achievement deleted → user_achievements deleted (CASCADE)

### Unique Constraints
- users.email (unique)
- user_preferences.user_id (one per user)
- daily_check_ins (user_id, date) - one check-in per day
- productivity_metrics (user_id, date) - one record per day
- session_contexts (user_id, session_date) - one context per day
- integrations (user_id, integration_type) - one per integration type

### Check Constraints
- energy_level: 1-10
- sleep_quality: 1-10
- productivity_rating: 1-5

## JSONB Fields Structure

### user_preferences.energy_patterns
```json
{
  "peak_hours": ["9-11", "14-16"],
  "low_energy_hours": ["13-14"],
  "energy_curve": {
    "morning": 8,
    "afternoon": 6,
    "evening": 4
  }
}
```

### user_preferences.work_style
```json
{
  "preferred_work_hours": "9am-5pm",
  "break_preference": "pomodoro",
  "deep_work_preference": "morning",
  "interruption_tolerance": "low"
}
```

### user_preferences.notification_settings
```json
{
  "email": {
    "task_reminders": true,
    "daily_summary": true,
    "weekly_report": true
  },
  "push": {
    "break_reminders": true,
    "stuck_alerts": true,
    "achievement_unlocked": true
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  }
}
```

### project_details.stakeholders
```json
[
  {
    "name": "Sarah Johnson",
    "role": "Product Manager",
    "email": "sarah@company.com",
    "avatar_url": "https://..."
  }
]
```

### project_details.resources
```json
[
  {
    "type": "document",
    "title": "Design Brief",
    "url": "https://docs.example.com/brief",
    "added_at": "2026-01-20T10:00:00Z"
  },
  {
    "type": "link",
    "title": "Competitor Analysis",
    "url": "https://..."
  }
]
```

### ai_learning_data.data (various structures by agent_type)

**user_profile agent:**
```json
{
  "work_patterns": {
    "most_productive_time": "morning",
    "average_focus_duration": 45,
    "break_frequency": "every_hour"
  },
  "task_preferences": {
    "preferred_task_types": ["design", "coding"],
    "avoided_task_types": ["meetings"]
  }
}
```

**time_learning agent:**
```json
{
  "task_type": "design_mockup",
  "historical_durations": [90, 95, 88, 105],
  "average_duration": 95,
  "factors_impact": {
    "energy_level": 0.2,
    "time_of_day": 0.15,
    "interruptions": 0.25
  }
}
```

### stuck_pattern_detections.suggested_actions
```json
[
  {
    "action": "take_break",
    "reason": "Mental fatigue detected",
    "priority": 1,
    "estimated_benefit": 0.8
  },
  {
    "action": "split_task",
    "reason": "Task complexity too high",
    "priority": 2,
    "estimated_benefit": 0.6
  }
]
```

### task_time_predictions.factors
```json
{
  "task_complexity": 0.7,
  "user_experience_level": 0.8,
  "time_of_day_factor": 0.9,
  "recent_performance": 0.85,
  "similar_tasks_avg": 95
}
```

### project_insights.data
```json
{
  "completion_probability": 0.85,
  "projected_completion_date": "2026-03-12",
  "risk_factors": [
    {
      "type": "resource_constraint",
      "severity": "medium",
      "description": "Designer availability limited next week"
    }
  ],
  "optimization_suggestions": [
    "Move low-priority tasks to next sprint",
    "Allocate more time for code review"
  ]
}
```

## Migration Strategy

### Phase 1: Core Tables
1. users
2. user_preferences
3. projects
4. tasks

### Phase 2: Activity Tracking
1. daily_check_ins
2. work_sessions
3. user_states

### Phase 3: AI & Learning
1. ai_learning_data
2. task_time_predictions
3. stuck_pattern_detections
4. project_insights

### Phase 4: Gamification
1. streaks
2. achievements
3. user_achievements
4. microtasks

### Phase 5: Supporting Features
1. notifications
2. reminders
3. integrations
4. audit_logs

## Backup & Archival Strategy

### Hot Data (Active Tables)
- users, projects, tasks (active)
- work_sessions (last 90 days)
- notifications (last 30 days)
- user_states (current)

### Warm Data (Archived)
- completed projects (>6 months old)
- work_sessions (90-365 days old)
- notifications (30-90 days old)

### Cold Data (Historical)
- projects (>1 year old)
- work_sessions (>1 year old)
- audit_logs (>6 months old)
