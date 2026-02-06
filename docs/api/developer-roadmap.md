# Developer Roadmap & Implementation Guide

This document outlines the thinking process for implementing the Raimon backend API. It serves as a guide for developers on what to build next, why, and how.

---

## Current State

### What's Built
- **Auth endpoints** (`/api/auth/*`) - signup, login, logout, refresh-token, forgot/reset password
- **User endpoints** (`/api/users/*`) - profile, preferences, onboarding, check-in, state

### What's Missing
Everything else from `api-endpoints.md`:
- Projects & Project Details
- Tasks & Task Actions
- Next Do system
- AI Agents integration
- Dashboard & Analytics
- Notifications & Reminders
- WebSocket events

---

## Implementation Order & Rationale

### Phase 1: Core Data Models (Do First)
**Why?** Everything else depends on projects and tasks existing.

#### 1.1 Projects Endpoints
```
GET    /api/projects
POST   /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id
POST   /api/projects/:id/archive
POST   /api/projects/:id/restore
GET    /api/projects/graveyard
```

**Implementation thinking:**
- Projects are the top-level container for all work
- Need soft-delete (archive) before hard-delete pattern
- Graveyard = list of archived projects (recoverable)
- Consider: Should deleting a project cascade to tasks? Yes, but maybe soft-delete first

**Database considerations:**
- `status` enum: `active`, `archived`, `completed`
- Index on `(user_id, status)` for fast filtering
- `archived_at` timestamp for graveyard sorting

**File to create:** `backend/routers/projects.py`

#### 1.2 Project Details Endpoints
```
PUT    /api/projects/:id/profile
PUT    /api/projects/:id/goals
PUT    /api/projects/:id/resources
PUT    /api/projects/:id/timeline
PUT    /api/projects/:id/stakeholders
```

**Implementation thinking:**
- These are all partial updates to the `project_details` table
- Could be one generic endpoint or separate for validation
- Separate endpoints = cleaner validation per section
- Consider: Use PATCH instead of PUT since these are partial updates?

**Decision:** Keep as PUT but make fields optional. Each endpoint updates its specific JSONB field.

#### 1.3 Tasks Endpoints
```
GET    /api/projects/:projectId/tasks
POST   /api/projects/:projectId/tasks
GET    /api/tasks/:id
PUT    /api/tasks/:id
DELETE /api/tasks/:id
PATCH  /api/tasks/:id/status
PATCH  /api/tasks/:id/priority
```

**Implementation thinking:**
- Tasks belong to projects but also to users (for cross-project queries)
- Need both `project_id` and `user_id` on tasks table
- Status flow: `todo` → `in_progress` → `completed` (or `blocked`)
- Priority: `low`, `medium`, `high`, `urgent`
- Support subtasks via `parent_task_id` self-reference

**Edge cases to handle:**
- What happens to subtasks when parent is deleted?
- Can a task be moved between projects?
- Task dependencies (task A blocks task B)

**File to create:** `backend/routers/tasks.py`

---

### Phase 2: Task Actions & Work Sessions
**Why?** Users need to interact with tasks beyond CRUD. This is core UX.

#### 2.1 Task Action Endpoints
```
POST   /api/tasks/:id/start
POST   /api/tasks/:id/pause
POST   /api/tasks/:id/complete
POST   /api/tasks/:id/break
POST   /api/tasks/:id/intervention
```

**Implementation thinking:**
- Starting a task creates a `work_session` record
- Pausing ends the current session, keeps task `in_progress`
- Completing ends session + marks task `completed`
- Break = pause + create break record (for break tracking)
- Intervention = when user reports being stuck/interrupted

**State machine:**
```
[todo] --start--> [in_progress] --pause--> [paused]
                       |                      |
                       +-------complete-------+
                       |
                       +--break--> [on_break] --resume--> [in_progress]
```

**Work session fields:**
- `task_id`, `user_id`, `start_time`, `end_time`
- `energy_before`, `energy_after` (for AI learning)
- `interruptions` count
- `notes`

**File to create:** `backend/routers/task_actions.py`

---

### Phase 3: Next Do System
**Why?** This is the core differentiator - AI-powered task recommendation.

```
GET  /api/next-do
POST /api/next-do/feedback
POST /api/next-do/skip
GET  /api/next-do/queue
POST /api/next-do/refresh
```

**Implementation thinking:**
- `GET /next-do` returns the single most important task to do right now
- Algorithm considers: priority, deadline, energy level, time of day, past patterns
- `feedback` = user rates the recommendation (good/bad/meh)
- `skip` = user declines this task, show next option
- `queue` = preview of upcoming recommended tasks
- `refresh` = force recalculation (after completing tasks, etc.)

**Algorithm design (v1 - simple):**
```python
def get_next_do(user_id):
    user_state = get_current_state(user_id)
    energy = user_state.energy_level or 5

    tasks = get_uncompleted_tasks(user_id)

    for task in tasks:
        task.score = calculate_score(task, energy)

    return sorted(tasks, by=score, desc=True)[0]

def calculate_score(task, energy):
    score = 0

    # Deadline urgency (0-40 points)
    if task.deadline:
        hours_until = (task.deadline - now()).hours
        if hours_until < 4: score += 40
        elif hours_until < 24: score += 30
        elif hours_until < 72: score += 20

    # Priority (0-30 points)
    priority_scores = {'urgent': 30, 'high': 20, 'medium': 10, 'low': 5}
    score += priority_scores.get(task.priority, 10)

    # Energy match (0-20 points)
    # High energy tasks when energy is high, low energy tasks when tired
    task_energy_required = estimate_energy_required(task)
    energy_match = 10 - abs(energy - task_energy_required)
    score += energy_match * 2

    # Time of day fit (0-10 points)
    # Some tasks better in morning (creative), some in afternoon (admin)

    return score
```

**Future AI enhancement:**
- Learn from user feedback to adjust scoring weights
- Personalized energy patterns
- Task type preferences by time of day

**File to create:** `backend/routers/next_do.py`

---

### Phase 4: Dashboard & Analytics
**Why?** Users need visibility into their progress. Builds motivation.

#### 4.1 Dashboard Endpoints
```
GET /api/dashboard/summary
GET /api/dashboard/current-task
GET /api/dashboard/today-tasks
GET /api/dashboard/greetings
```

**Implementation thinking:**
- `summary` = aggregated view (today's progress, streaks, current state)
- Heavy endpoint - consider caching or materialized views
- `greetings` = personalized message based on time, state, achievements
- This is mostly read-only aggregation of other data

**Performance consideration:**
- Cache dashboard summary for 1-5 minutes
- Or use Supabase realtime to invalidate on changes
- Pre-compute daily metrics at end of day

#### 4.2 Analytics Endpoints
```
GET /api/analytics/time-tracking
GET /api/analytics/productivity-metrics
GET /api/analytics/project-performance
GET /api/analytics/goal-progress
```

**Implementation thinking:**
- These query `work_sessions`, `daily_check_ins`, `tasks` tables
- Support date range filters: `?start_date=&end_date=`
- Return aggregated data, not raw records
- Consider background job to pre-compute daily/weekly metrics

**File to create:** `backend/routers/dashboard.py`, `backend/routers/analytics.py`

---

### Phase 5: AI Agents Integration
**Why?** This is the "smart" part of Raimon. Build after core data flows work.

#### 5.1 Approach Decision

**Option A: External AI Service**
- Agents run as separate microservices
- Backend just proxies requests
- Pros: Scalable, can use different models per agent
- Cons: More infra, latency, cost

**Option B: Embedded Logic**
- Agents are Python modules in this backend
- Use OpenAI/Anthropic API for LLM calls when needed
- Pros: Simpler, single deployment
- Cons: Scaling, all-or-nothing deploys

**Recommendation:** Start with Option B, extract to microservices later if needed.

#### 5.2 Agent Endpoints to Implement

**Priority Engine** (implement first - powers Next Do)
```
POST /api/agents/priority-engine/analyze
GET  /api/agents/priority-engine/recommendations
POST /api/agents/priority-engine/rerank-tasks
```

**Daily State Adapter** (implement second - personalizes experience)
```
POST /api/agents/state-adapter/check-in
GET  /api/agents/state-adapter/energy-assessment
GET  /api/agents/state-adapter/task-recommendations
```

**Stuck Pattern Agent** (implement third - helps when blocked)
```
POST /api/agents/stuck-pattern/detect
GET  /api/agents/stuck-pattern/analysis
POST /api/agents/stuck-pattern/suggest-solutions
```

**Time Learning Agent** (implement fourth - improves estimates)
```
POST /api/agents/time-learning/track
GET  /api/agents/time-learning/predictions
GET  /api/agents/time-learning/performance-insights
```

**Others** (later phases):
- User Profile Agent
- Project Insight Engine
- Streak & Motivation
- Context Continuity

**File to create:** `backend/routers/agents_management.py` for agent management endpoints

---

### Phase 6: Notifications & Reminders
**Why?** Keep users engaged, but not critical for MVP.

```
GET    /api/notifications
PUT    /api/notifications/:id/read
PUT    /api/notifications/read-all
DELETE /api/notifications/:id

GET    /api/reminders
POST   /api/reminders
PUT    /api/reminders/:id
DELETE /api/reminders/:id
```

**Implementation thinking:**
- Notifications are system-generated (achievements, reminders, insights)
- Reminders are user-created
- Need background job/cron for triggering time-based reminders
- Consider: Push notifications? Email? In-app only?

**File to create:** `backend/routers/notifications.py`, `backend/routers/reminders.py`

---

### Phase 7: WebSocket & Real-time
**Why?** Nice to have for live updates. Not blocking for MVP.

```
connect: /ws/user/:userId
events:
  - task.started
  - task.completed
  - state.changed
  - break.started
  - agent.insight
  - notification.new
```

**Implementation options:**
1. FastAPI WebSockets directly
2. Use Supabase Realtime (simpler, built-in)
3. External service (Pusher, Ably)

**Recommendation:** Use Supabase Realtime for v1. Frontend subscribes directly to Supabase channels. Backend doesn't need to manage WebSocket connections.

---

## Architecture Decisions

### API Response Format
All endpoints should return consistent format:
```json
{
  "success": true,
  "data": { ... },
  "message": "optional message"
}

// On error:
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

### Authentication Pattern
- Use Supabase Auth for user management
- Generate our own JWTs for API access (more control)
- Refresh tokens stored in HTTP-only cookies (security) or returned in response (mobile)

### Database Patterns
- **Soft delete:** Use `deleted_at` timestamp instead of actual deletes
- **Timestamps:** Every table has `created_at`, `updated_at`
- **User isolation:** RLS policies ensure users only see their data
- **JSONB for flexibility:** Use for preferences, metadata, agent data

### Error Handling
```python
# Create custom exceptions
class NotFoundError(HTTPException):
    def __init__(self, resource: str):
        super().__init__(status_code=404, detail=f"{resource} not found")

class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)
```

### File Structure (Target)
```
backend/
├── main.py
├── requirements.txt
├── .env
├── core/
│   ├── config.py
│   ├── security.py
│   ├── supabase.py
│   └── exceptions.py
├── models/
│   ├── auth.py
│   ├── user.py
│   ├── project.py
│   ├── task.py
│   └── common.py
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── projects.py
│   ├── tasks.py
│   ├── task_actions.py
│   ├── next_do.py
│   ├── dashboard.py
│   ├── analytics.py
│   ├── notifications.py
│   ├── reminders.py
│   └── agents/
│       ├── priority_engine.py
│       ├── state_adapter.py
│       ├── stuck_pattern.py
│       ├── time_learning.py
│       └── ...
├── services/
│   ├── next_do_service.py
│   ├── analytics_service.py
│   └── agent_service.py
└── utils/
    ├── scoring.py
    └── helpers.py
```

---

## Testing Strategy

### Unit Tests
- Test scoring algorithms
- Test state machine transitions
- Test validation logic

### Integration Tests
- Test full endpoint flows
- Use test database (Supabase project or local Postgres)

### Manual Testing
- Use `/docs` Swagger UI
- Create Postman/Insomnia collection

---

## Next Steps Checklist

### Immediate (This Week)
- [ ] Create `backend/routers/projects.py` with CRUD endpoints
- [ ] Create `backend/models/project.py` with Pydantic schemas
- [ ] Add project-related tables to Supabase (if not exists)
- [ ] Test project endpoints manually

### Short Term (Next 2 Weeks)
- [ ] Create tasks endpoints
- [ ] Create task actions endpoints
- [ ] Implement basic Next Do algorithm
- [ ] Create dashboard summary endpoint

### Medium Term (Month 1)
- [ ] Implement Priority Engine agent
- [ ] Add analytics endpoints
- [ ] Set up notification system
- [ ] Add comprehensive error handling

### Long Term
- [ ] AI agents with LLM integration
- [ ] Real-time WebSocket events
- [ ] Performance optimization
- [ ] Rate limiting and caching

---

## Questions to Resolve

1. **Task dependencies:** How complex should the dependency graph be? Simple "blocked by" or full DAG?

2. **Energy tracking:** Should energy auto-decay over the day, or only update on explicit check-ins?

3. **AI model choice:** OpenAI, Anthropic, or local models for agent intelligence?

4. **Multi-device:** How to handle user working on multiple devices? Session conflicts?

5. **Offline support:** Should the API support any offline/sync patterns?

---

## References

- [api-endpoints.md](./api-endpoints.md) - Full endpoint specification
- [api-examples.md](./api-examples.md) - Request/response examples
- [database-erd.md](./database-erd.md) - Database schema and relationships
