# Opik Tracing Documentation

This document outlines all endpoints and agent flows that are traced with Opik for observability.

---

## Overview

Raimon uses [Opik](https://www.comet.com/site/products/opik/) for tracing and observability across:
1. **Backend API Endpoints** - HTTP request/response tracking
2. **Agent Orchestrator** - Event-driven workflow tracking
3. **Individual Agents** - LLM calls and agent processing
4. **Storage Operations** - Database interactions

---

## Backend API Endpoints

### Dashboard Endpoints (`/api/dashboard`)

| Endpoint | Method | Opik Track Name | Description |
|----------|--------|-----------------|-------------|
| `/api/dashboard/summary` | GET | `dashboard_summary_endpoint` | Get dashboard summary, triggers `APP_OPEN` agent event |
| `/api/dashboard/today-tasks` | GET | `dashboard_today_tasks_endpoint` | Get all pending tasks for today |
| `/api/dashboard/done-for-today` | POST | `dashboard_done_for_today_endpoint` | End the day, triggers `DAY_END` agent event |

### User Endpoints (`/api/users`)

| Endpoint | Method | Opik Track Name | Description |
|----------|--------|-----------------|-------------|
| `/api/users/state/check-in` | POST | `daily_check_in_endpoint` | Daily check-in, triggers `CHECKIN_SUBMITTED` agent event |

### Task Endpoints (`/api/tasks`)

| Endpoint | Method | Opik Track Name | Description |
|----------|--------|-----------------|-------------|
| `/api/tasks/{id}/start` | POST | `task_start_endpoint` | Start a task, triggers `DO_ACTION(start)` agent event |
| `/api/tasks/{id}/pause` | POST | `task_pause_endpoint` | Pause a task, triggers `DO_ACTION(pause)` agent event |
| `/api/tasks/{id}/complete` | POST | `task_complete_endpoint` | Complete a task, triggers `DO_ACTION(complete)` agent event |
| `/api/tasks/{id}/break` | POST | `task_break_endpoint` | Take a break from task |
| `/api/tasks/{id}/intervention` | POST | `task_intervention_endpoint` | Report stuck, triggers `DO_ACTION(stuck)` agent event |

### Project Endpoints (`/api/projects`)

| Endpoint | Method | Opik Track Name | Description |
|----------|--------|-----------------|-------------|
| `/api/projects` | POST | `project_create_endpoint` | Create a new project |
| `/api/projects/{id}` | PUT | `project_update_endpoint` | Update project and sync tasks |

### Agent MVP Endpoints (`/api/agent-mvp`)

| Endpoint | Method | Opik Track Name | Description |
|----------|--------|-----------------|-------------|
| `/api/agent-mvp/smoke` | POST | `agent_mvp_smoke_test` | Smoke test for Opik tracing |
| `/api/agent-mvp/next-do` | POST | `agent_mvp_next_do_endpoint` | Get next recommended task |
| `/api/agent-mvp/app-open` | POST | `agent_mvp_app_open_endpoint` | Resume user context |
| `/api/agent-mvp/checkin` | POST | `agent_mvp_checkin_endpoint` | Process check-in via agent |
| `/api/agent-mvp/do-action` | POST | `agent_mvp_do_action_endpoint` | Handle task actions via agent |
| `/api/agent-mvp/day-end` | POST | `agent_mvp_day_end_endpoint` | Process day end via agent |
| `/api/agent-mvp/insights` | POST | `agent_mvp_insights_endpoint` | Generate project insights |
| `/api/agent-mvp/simulate` | POST | `agent_mvp_simulate_endpoint` | Simulate agent (no auth, for testing) |

---

## Agent Event Flow

### Event Types

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER ACTIONS                              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌───────────┐
   │ APP_OPEN│          │ CHECKIN  │         │ DO_ACTION │
   └────┬────┘          └────┬─────┘         └─────┬─────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌───────────────┐   ┌────────────────┐   ┌─────────────────┐
│ Dashboard     │   │ Daily Check-in │   │ Task Actions    │
│ Summary Load  │   │ Submission     │   │ start/complete/ │
│               │   │                │   │ pause/stuck     │
└───────────────┘   └────────────────┘   └─────────────────┘
                              │
                              ▼
                      ┌───────────┐
                      │ DAY_END   │
                      └─────┬─────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ "Done for     │
                    │  Today" click │
                    └───────────────┘
```

### Event Details

#### 1. `APP_OPEN`
- **Triggered by**: `GET /api/dashboard/summary`
- **Purpose**: Resume user context when app opens
- **Agent Handler**: `orchestrator_app_open`
- **Actions**:
  - Load previous session state
  - Resume context via `context_continuity_agent`
  - Return context hints
- **Output** (`response.data`):
  ```json
  {
    "event_type": "APP_OPEN",
    "context_resumption": {
      "previous_session": {...},
      "suggested_continuation": "Continue working on...",
      "context_hints": ["You were working on X", "You have 3 tasks due today"]
    }
  }
  ```

#### 2. `CHECKIN_SUBMITTED`
- **Triggered by**: `POST /api/users/state/check-in`
- **Purpose**: Process daily check-in and prepare for task selection
- **Agent Handler**: `orchestrator_checkin`
- **Actions**:
  - Log check-in event
  - Convert check-in to selection constraints
  - Prepare priority scoring
- **Output** (`response.data`):
  ```json
  {
    "event_type": "CHECKIN_SUBMITTED",
    "selection_constraints": {
      "max_minutes": 60,
      "mode": "balanced",
      "current_energy": 7,
      "prefer_priority": "high"
    }
  }
  ```

#### 3. `DO_NEXT`
- **Triggered by**: `POST /api/agent-mvp/next-do`
- **Purpose**: Select the next optimal task
- **Agent Handler**: `orchestrator_do_next`
- **Actions**:
  - Analyze user profile
  - Get task candidates
  - Score candidates with priority engine
  - Select optimal task
  - Generate coaching message
- **Output** (`response.data`):
  ```json
  {
    "event_type": "DO_NEXT",
    "active_do": {
      "task": {...},
      "selection_reason": "High priority + matches your energy level",
      "coaching_message": "Let's knock this out!"
    },
    "coach_message": {
      "title": "Ready to focus?",
      "message": "This task aligns with your current energy.",
      "next_step": "Open the design file"
    }
  }
  ```

#### 4. `DO_ACTION`
- **Triggered by**: Task action endpoints
- **Purpose**: Handle task lifecycle actions
- **Agent Handler**: `orchestrator_do_action`
- **Sub-actions**:

| Action | Trigger Endpoint | Agent Processing |
|--------|------------------|------------------|
| `start` | `/api/tasks/{id}/start` | Update session status |
| `pause` | `/api/tasks/{id}/pause` | Update session status |
| `complete` | `/api/tasks/{id}/complete` | Update gamification, generate motivation |
| `stuck` | `/api/tasks/{id}/intervention` | Detect stuck patterns, generate microtasks |

- **Output for `complete`** (`response.data`):
  ```json
  {
    "event_type": "DO_ACTION",
    "motivation_message": {
      "title": "Nice work!",
      "body": "You completed the task in 45 minutes. That's 10% faster than your average!",
      "cta": "Ready for the next one?"
    }
  }
  ```

- **Output for `stuck`** (`response.data`):
  ```json
  {
    "event_type": "DO_ACTION",
    "stuck_analysis": {
      "is_stuck": true,
      "stuck_reason": "Task seems too large",
      "microtasks": [...]
    },
    "microtasks": [
      {"description": "Break into 3 smaller parts", "estimated_minutes": 2},
      {"description": "Start with the easiest section", "estimated_minutes": 5},
      {"description": "Set a 15-minute timer and just begin", "estimated_minutes": 15}
    ]
  }
  ```

#### 5. `DAY_END`
- **Triggered by**: `POST /api/dashboard/done-for-today`
- **Purpose**: Process end of day and generate insights
- **Agent Handler**: `orchestrator_day_end`
- **Actions**:
  - Update gamification (day completed)
  - Generate project insights
  - Generate reflective motivation message
  - Save session insights
- **Output** (`response.data`):
  ```json
  {
    "event_type": "DAY_END",
    "day_insights": [
      {"title": "Productive morning", "description": "You completed 3 tasks before noon"},
      {"title": "Focus champion", "description": "Your average focus session was 45 minutes"}
    ],
    "motivation_message": {
      "title": "Day complete!",
      "body": "You accomplished a lot today. Rest well!",
      "cta": "See you tomorrow"
    }
  }
  ```

---

## Orchestrator Tracing

The orchestrator (`agent_mvp/orchestrator.py`) is the central hub that processes all events.

### Traced Methods

| Method | Opik Track Name | Description |
|--------|-----------------|-------------|
| `process_event()` | `orchestrator_process_event` | Main entry point for all events |
| `_handle_app_open()` | `orchestrator_app_open` | Handle APP_OPEN events |
| `_handle_checkin()` | `orchestrator_checkin` | Handle CHECKIN_SUBMITTED events |
| `_handle_do_next()` | `orchestrator_do_next` | Handle DO_NEXT events |
| `_handle_do_action()` | `orchestrator_do_action` | Handle DO_ACTION events |
| `_handle_day_end()` | `orchestrator_day_end` | Handle DAY_END events |

---

## Individual Agent Tracing

Each agent module has its own tracing:

### User Profile Agent
- **File**: `agent_mvp/user_profile_agent.py`
- **Purpose**: Analyze user patterns and preferences

### Priority Engine Agent
- **File**: `agent_mvp/priority_engine_agent.py`
- **Purpose**: Score and rank task candidates

### Do Selector Agent
- **File**: `agent_mvp/do_selector.py`
- **Purpose**: Select optimal task from scored candidates

### Coach Agent
- **File**: `agent_mvp/coach.py`
- **Purpose**: Generate coaching messages

### Stuck Pattern Agent
- **File**: `agent_mvp/stuck_pattern_agent.py`
- **Purpose**: Detect stuck patterns and suggest microtasks

### Motivation Agent
- **File**: `agent_mvp/motivation_agent.py`
- **Purpose**: Generate motivational messages

### Context Continuity Agent
- **File**: `agent_mvp/context_continuity_agent.py`
- **Purpose**: Resume user context on app open

### Project Insight Agent
- **File**: `agent_mvp/project_insight_agent.py`
- **Purpose**: Generate project progress insights

### Gamification Rules
- **File**: `agent_mvp/gamification_rules.py`
- **Purpose**: Update XP, streaks, and levels

---

## Storage Operation Tracing

Database operations in `agent_mvp/storage.py` are traced:

| Operation | Opik Track Name |
|-----------|-----------------|
| `save_active_do()` | `storage_save_active_do` |
| `get_active_do()` | `storage_get_active_do` |
| `save_session_state()` | `storage_save_session_state` |
| `get_session_state()` | `storage_get_session_state` |
| `save_stuck_episode()` | `storage_save_stuck_episode` |
| `get_recent_stuck_episodes()` | `storage_get_recent_stuck_episodes` |
| `save_time_patterns()` | `storage_save_time_patterns` |
| `get_time_patterns()` | `storage_get_time_patterns` |
| `save_session_insights()` | `storage_save_session_insights` |
| `get_recent_insights()` | `storage_get_recent_insights` |
| `save_gamification_state()` | `storage_save_gamification_state` |
| `get_gamification_state()` | `storage_get_gamification_state` |
| `save_xp_ledger_entry()` | `storage_save_xp_ledger_entry` |
| `get_xp_history()` | `storage_get_xp_history` |
| `log_agent_event()` | `storage_log_agent_event` |
| `get_agent_events()` | `storage_get_agent_events` |
| `get_user_sessions()` | `storage_get_user_sessions` |
| `get_user_tasks()` | `storage_get_user_tasks` |
| `get_user_checkins()` | `storage_get_user_checkins` |
| `get_task_candidates()` | `storage_get_task_candidates` |

---

## Complete User Flow Example

Here's a typical user session traced in Opik:

```
1. User opens app
   └── GET /api/dashboard/summary
       ├── [Opik] dashboard_summary_endpoint
       └── [Opik] orchestrator_process_event (APP_OPEN)
           ├── [Opik] orchestrator_app_open
           ├── [Opik] storage_get_session_state
           └── [Opik] storage_get_active_do

2. User completes daily check-in
   └── POST /api/users/state/check-in
       ├── [Opik] daily_check_in_endpoint
       └── [Opik] orchestrator_process_event (CHECKIN_SUBMITTED)
           └── [Opik] orchestrator_checkin

3. User starts a task
   └── POST /api/tasks/{id}/start
       ├── [Opik] task_start_endpoint
       └── [Opik] orchestrator_process_event (DO_ACTION:start)
           └── [Opik] orchestrator_do_action

4. User completes a task
   └── POST /api/tasks/{id}/complete
       ├── [Opik] task_complete_endpoint
       └── [Opik] orchestrator_process_event (DO_ACTION:complete)
           ├── [Opik] orchestrator_do_action
           ├── [Opik] storage_save_gamification_state
           └── [Opik] storage_save_xp_ledger_entry

5. User ends day
   └── POST /api/dashboard/done-for-today
       ├── [Opik] dashboard_done_for_today_endpoint
       └── [Opik] orchestrator_process_event (DAY_END)
           ├── [Opik] orchestrator_day_end
           ├── [Opik] storage_save_session_insights
           └── [Opik] storage_save_gamification_state
```

---

---

## Using Agent Outputs in Frontend

The agent outputs are returned in API responses and should be used by the frontend:

### 1. Check-in Response → Task Selection

```typescript
// After check-in, use agent_constraints for better task filtering
const response = await apiFetch('/api/users/state/check-in', {
  method: 'POST',
  body: { energy_level: 7, mood: 'good', focus_areas: ['work'] }
});

// agent_constraints can be used to filter/sort tasks
const constraints = response.data.agent_constraints;
// { max_minutes: 60, mode: "balanced", current_energy: 7 }
```

### 2. Task Complete → Show Motivation

```typescript
// When completing a task, show the motivation message
const response = await apiFetch(`/api/tasks/${taskId}/complete`, {
  method: 'POST',
  body: { notes: 'Done!' }
});

// Show motivation to user
if (response.data.agent_motivation) {
  showToast({
    title: response.data.agent_motivation.title,
    message: response.data.agent_motivation.body
  });
}
```

### 3. Stuck/Intervention → Show Microtasks

```typescript
// When user reports being stuck, show agent-generated microtasks
const response = await apiFetch(`/api/tasks/${taskId}/intervention`, {
  method: 'POST',
  body: { intervention_type: 'stuck', description: 'Not sure where to start' }
});

// Use agent microtasks if available, fallback to default suggestions
const suggestions = response.data.agent_microtasks || response.data.suggestions;
showStuckModal({ suggestions });
```

### 4. Day End → Show Insights & Motivation

```typescript
// When ending the day, display insights and motivation
const response = await apiFetch('/api/dashboard/done-for-today', {
  method: 'POST'
});

// Show day summary with insights
if (response.data.insights) {
  showDaySummary({
    insights: response.data.insights,
    motivation: response.data.motivation
  });
}
```

### 5. Dashboard Load → Context Resumption

```typescript
// On dashboard load, use context hints
const response = await apiFetch('/api/dashboard/summary');

// The APP_OPEN event is triggered automatically
// Context resumption happens server-side
// Future: could use context_resumption data to show "Continue where you left off"
```

---

## Viewing Traces in Opik

1. **Go to Opik Dashboard**: https://www.comet.com/opik
2. **Select your project**
3. **View traces** by:
   - Trace name (e.g., `dashboard_summary_endpoint`)
   - Time range
   - Status (success/error)

### Key Metrics to Monitor

- **Latency**: How long each operation takes
- **Error Rate**: Percentage of failed operations
- **LLM Token Usage**: Tokens consumed by Gemini calls
- **Agent Event Distribution**: Which events are triggered most

---

## Configuration

Opik is configured via environment variables:

```env
OPIK_API_KEY=your_opik_api_key
OPIK_PROJECT_NAME=raimon
OPIK_WORKSPACE=your_workspace
```

The Opik middleware is added in `main.py`:
```python
from opik_utils.middleware import OpikMiddleware

app.add_middleware(OpikMiddleware, ...)
```

---

## Testing Opik Integration

Use the smoke test endpoint:

```bash
curl -X POST http://localhost:8000/api/agent-mvp/smoke
```

This should:
1. Return `{"success": true, "message": "Opik smoke test passed", ...}`
2. Create a trace named `agent_mvp_smoke_test` in Opik dashboard
