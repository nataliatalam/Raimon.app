# Raimon AI Agent System - End-to-End Demo Runbook

## Overview
This runbook demonstrates the complete Raimon AI productivity agent system upgrade from MVP to full end-to-end workflow. The system now handles the entire user journey: onboarding → project creation → app open → daily check-in → task selection → focus → completion → stuck interventions → day finish → insights → gamification updates.

## Prerequisites
1. **Database Setup**: Execute the SQL in `backend/agent_mvp/database_schema.sql` in Supabase
2. **Environment**: Python 3.8+, all dependencies installed
3. **API Access**: Valid authentication tokens for testing
4. **Test Data**: Sample user with projects and tasks

## System Architecture
- **15 Specialized Agents**: 8 deterministic + 7 bounded LLM-based
- **Event-Driven Orchestration**: LangGraph workflow with 5 main event types
- **Comprehensive Storage**: 8 new database tables with RLS policies
- **Gamification System**: XP, levels, streaks with deterministic rules
- **Bounded AI**: JSON-validated LLM outputs with deterministic fallbacks

## Demo Scenario
**User Persona**: Sarah, a product manager with high energy, focused on work projects, 2 hours available for deep work.

---

## Phase 1: User Onboarding & Profile Building

### 1.1 User Registration
```bash
# User signs up through frontend
POST /api/auth/signup
{
  "email": "sarah@example.com",
  "password": "securepass123"
}
```

### 1.2 Initial Profile Analysis
The system automatically analyzes user's first interactions:
- **user_profile_agent**: Learns energy patterns, focus preferences
- **project_profile_agent**: Normalizes project data with optional AI suggestions
- **time_learning_agent**: Begins tracking time patterns

---

## Phase 2: App Open & Context Continuity

### 2.1 App Launch Event
```bash
POST /api/agent/app-open
Authorization: Bearer <user_token>
{
  "user_id": "sarah-user-id",
  "timestamp": "2024-01-15T09:00:00Z"
}
```

**System Response:**
```json
{
  "success": true,
  "data": {
    "event_type": "APP_OPEN",
    "resumed_session": false,
    "welcome_message": "Good morning, Sarah! Ready to tackle your priorities?",
    "gamification_status": {
      "level": 3,
      "current_streak": 5,
      "xp_today": 0
    }
  }
}
```

**Agents Triggered:**
- `context_continuity_agent`: Checks for active session to resume
- `events`: Logs APP_OPEN event

---

## Phase 3: Daily Check-In & Task Selection

### 3.1 Daily Check-In Submission
```bash
POST /api/agent/checkin
Authorization: Bearer <user_token>
{
  "user_id": "sarah-user-id",
  "energy_level": 8,
  "focus_areas": ["work", "product"],
  "time_available": 120,
  "current_context": "home_office",
  "timestamp": "2024-01-15T09:05:00Z"
}
```

**System Processing:**
1. `state_adapter_agent`: Converts check-in to task constraints
2. `priority_engine_agent`: Scores all available tasks
3. `do_selector`: Deterministically selects optimal task
4. `coach`: Generates personalized coaching message

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "event_type": "CHECKIN_SUBMITTED",
    "selected_task": {
      "id": "task-456",
      "title": "Design system architecture for Q1 feature",
      "priority": "high",
      "estimated_duration": 90,
      "project": "Product Roadmap"
    },
    "selection_reason": "High-priority task matching your 'work' focus with 90min duration fitting your 2-hour window",
    "coaching_message": "This architecture work will unblock the entire team. Break it into 25min focused sessions with 5min breaks.",
    "gamification_potential": "+25 XP on completion"
  }
}
```

---

## Phase 4: Task Execution & Focus Chamber

### 4.1 Start Task Session
```bash
POST /api/agent/do-action
Authorization: Bearer <user_token>
{
  "user_id": "sarah-user-id",
  "action": "start",
  "task_id": "task-456",
  "timestamp": "2024-01-15T09:10:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "event_type": "DO_ACTION",
    "action": "start",
    "focus_timer_started": true,
    "estimated_completion": "2024-01-15T10:40:00Z"
  }
}
```

### 4.2 Stuck Detection (Simulated)
After 45 minutes of no progress updates, the system detects potential stuck state:

**Automatic Trigger:**
- `stuck_pattern_agent`: Analyzes inactivity patterns
- Generates microtasks for unsticking

```json
{
  "event_type": "STUCK_DETECTED",
  "microtasks": [
    "Take 2 minutes to write down your current blocker",
    "Break the architecture into 3 smaller components",
    "Sketch a quick diagram of the data flow"
  ],
  "intervention_type": "microtask_breakdown"
}
```

---

## Phase 5: Task Completion & Session End

### 5.1 Complete Task
```bash
POST /api/agent/do-action
Authorization: Bearer <user_token>
{
  "user_id": "sarah-user-id",
  "action": "complete",
  "task_id": "task-456",
  "actual_duration": 95,
  "timestamp": "2024-01-15T10:45:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "event_type": "DO_ACTION",
    "action": "complete",
    "xp_gained": 25,
    "new_level": 3,
    "streak_extended": true,
    "completion_message": "Excellent work on the architecture! This will accelerate the entire Q1 timeline."
  }
}
```

---

## Phase 6: Day End & Insights Generation

### 6.1 End of Day Processing
```bash
POST /api/agent/day-end
Authorization: Bearer <user_token>
{
  "user_id": "sarah-user-id",
  "timestamp": "2024-01-15T17:30:00Z"
}
```

**System Processing:**
1. `project_insight_agent`: Analyzes completed work patterns
2. `motivation_agent`: Generates personalized motivation message
3. `gamification_rules`: Updates XP and streak
4. `time_learning_agent`: Updates time patterns

**Response:**
```json
{
  "success": true,
  "data": {
    "event_type": "DAY_END",
    "insights": [
      {
        "type": "productivity_pattern",
        "title": "Peak Performance Window",
        "description": "You completed 95% of your deep work before noon. Consider scheduling high-priority tasks earlier."
      },
      {
        "type": "project_progress",
        "title": "Product Roadmap Momentum",
        "description": "Completed 3 of 5 Q1 architecture tasks. On track for 80% completion by end of month."
      }
    ],
    "motivation_message": "Sarah, you're building momentum! Your focused sessions are creating real impact. Keep channeling that morning energy! 🌅",
    "gamification_update": {
      "xp_gained_today": 45,
      "new_total_xp": 320,
      "level": 3,
      "streak": 6,
      "longest_streak": 6
    },
    "tomorrow_preview": "Based on your patterns, tomorrow could be great for continuing the product roadmap work."
  }
}
```

---

## Phase 7: Insights & Analytics Access

### 7.1 Get Today's Insights
```bash
GET /api/agent/insights?date=2024-01-15
Authorization: Bearer <user_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-15",
    "insights": [...], // Same as day-end response
    "motivation": "Sarah, you're building momentum! ...",
    "gamification_summary": {
      "xp_earned": 45,
      "tasks_completed": 2,
      "focus_sessions": 1,
      "stuck_interventions": 1
    }
  }
}
```

---

## Testing the System

### Run the Test Suite
```bash
cd backend
python -m pytest tests_agent_mvp/ -v
```

### Manual API Testing
Use tools like Postman or curl to test each endpoint with the sequences above.

### Monitoring & Debugging
- Check Opik traces for LLM calls and agent executions
- Review agent_events table for event logging
- Monitor gamification_state and xp_ledger for XP updates

---

## Key System Guarantees Demonstrated

### Deterministic Selection
- Task selection uses fixed scoring algorithm (no randomness)
- Gamification XP follows deterministic rules
- Fallbacks ensure system works even if LLM fails

### Bounded AI Usage
- LLM outputs validated against JSON schemas
- Length limits on all generated content
- Deterministic fallbacks for validation failures

### Event-Driven Architecture
- All user actions trigger structured events
- State transitions are explicit and logged
- System maintains consistency across sessions

### Comprehensive User Journey
- From app open to day end, all phases covered
- Context continuity between sessions
- Progressive profile learning over time

---

## Performance Expectations

- **Response Time**: <2 seconds for deterministic operations, <5 seconds for LLM calls
- **Availability**: 99.9% uptime with graceful degradation
- **Data Consistency**: ACID compliance via Supabase
- **Scalability**: Supports 1000+ concurrent users

## Troubleshooting

### Common Issues
1. **LLM Validation Failures**: Check Opik traces, system falls back to deterministic responses
2. **Database Connection Issues**: Verify Supabase credentials and RLS policies
3. **Event Processing Delays**: Check LangGraph orchestration logs
4. **XP Calculation Errors**: Verify gamification_rules logic and storage operations

### Debug Commands
```bash
# Check recent events
SELECT * FROM agent_events WHERE user_id = 'sarah-user-id' ORDER BY timestamp DESC LIMIT 10;

# Verify gamification state
SELECT * FROM gamification_state WHERE user_id = 'sarah-user-id';

# Check active session
SELECT * FROM active_do WHERE user_id = 'sarah-user-id';
```

This runbook demonstrates the complete transformation from MVP to comprehensive productivity agent system, with all 15 agents working together in a robust, event-driven architecture.