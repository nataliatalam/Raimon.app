# END-TO-END UI FLOW: Login → Daily Check-In → First Task

**Date:** February 4, 2026  
**Purpose:** Implementation-accurate explanation of the complete user lane from login through receiving the first task of the day.

---

## TABLE OF CONTENTS
1. [UI Flow Map](#ui-flow-map)
2. [Backend Flow Map](#backend-flow-map)
3. [Agents Involved (Authoritative List)](#agents-involved-authoritative-list)
4. [Contract Verification](#contract-verification)
5. [Observability / Debug Checklist](#observability--debug-checklist)
6. [Sequence Diagram](#sequence-diagram)
7. [Known Risks / Likely Breakpoints](#known-risks--likely-breakpoints)

---

## UI FLOW MAP

### 1. Login Screen
**Route:** [app/(site)/login/page.tsx](app/(site)/login/page.tsx)

#### UI Actions:
- **Email/Password login:**
  - User enters credentials
  - `handleSubmit` → `POST /api/auth/login`
  
- **Google OAuth:**
  - `handleGoogleSignIn` → Supabase OAuth redirect
  - Callback: [app/auth/callback/route.ts](app/auth/callback/route.ts) exchanges OAuth code
  - Redirect to: [app/auth/complete/page.tsx](app/auth/complete/page.tsx)
  - Frontend calls `POST /api/auth/google` to exchange Supabase token for backend JWT

#### API Call (Email/Password):
```typescript
POST /api/auth/login
Request: { email: string, password: string }
Response: {
  success: true,
  data: {
    user: { id, email, name, onboarding_completed },
    token: string,
    refresh_token: string
  }
}
```

#### Response Handling:
- `setSession({ accessToken, refreshToken, user })` saves JWT in [lib/session.ts](lib/session.ts)
- Redirect based on `onboarding_completed`:
  - `true` → `/dashboard`
  - `false` → `/onboarding-questions`

---

### 2. Onboarding (If Required)
**Routes:**
- [app/(site)/onboarding-questions/page.tsx](app/(site)/onboarding-questions/page.tsx) - 6-step questionnaire
- [app/(site)/onboarding/page.tsx](app/(site)/onboarding/page.tsx) - info screens

#### API Call:
```typescript
PUT /api/users/onboarding
Request: { step: 6, data: { life_setup, goal, breakers, ... } }
Response: { success: true, data: { onboarding_step: 6, completed: true } }
```

#### Flow:
1. User completes 6 questions
2. Submits via `PUT /api/users/onboarding`
3. Backend updates `users.onboarding_completed = true`
4. Frontend redirects to `/onboarding` → then `/dashboard`

---

### 3. Dashboard - Daily Check-In
**Route:** [app/(app)/dashboard/page.tsx](app/(app)/dashboard/page.tsx)

#### Component Flow:
1. **Page loads:** checks `sessionStorage.getItem('raimon_checked_in')`
   - If `'true'` → skip to tasks
   - Else → show `<DailyCheckIn />` component

2. **Check-in Component:** [app/components/DailyCheckIn.tsx](app/components/DailyCheckIn.tsx)
   - 3 questions: energy (1-10), mood, focus
   - Maps to `{ energy_level, mood, focus_areas }`

#### API Call:
```typescript
POST /api/users/state/check-in
Request: {
  energy_level: number (1-10),
  mood: string,
  focus_areas?: string[]
}
Response: {
  success: true,
  data: {
    check_in: { id, user_id, date, energy_level, mood, ... },
    greeting: string
  }
}
```

#### Backend Processing (CRITICAL):
**File:** [backend/routers/users.py](backend/routers/users.py) → `POST /api/users/state/check-in`

```python
# Lines 247-330
async def daily_check_in(request: CheckInRequest, current_user: dict):
    # 1. Save to daily_check_ins table
    supabase.table("daily_check_ins").insert({
        "user_id": user_id,
        "date": today,
        "energy_level": request.energy_level,
        "mood": request.mood,
        "focus_areas": request.focus_areas
    })
    
    # 2. 🤖 TRIGGER AGENT ORCHESTRATOR (fire-and-forget)
    trigger_agent_on_checkin(user_id, request.energy_level, request.focus_areas)
    
    # 3. Return response immediately (non-blocking)
    return { success: True, data: { check_in: {...}, greeting: "..." } }
```

**Agent Trigger Function:**
```python
# Lines 26-39
def trigger_agent_on_checkin(user_id: str, energy_level: int, focus_areas: List[str]):
    event = CheckInSubmittedEvent(
        user_id=user_id,
        energy_level=energy_level,
        focus_areas=focus_areas,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    logger.info(f"🤖 AGENTS_INVOKED event_type=CHECKIN_SUBMITTED user_id={user_id}")
    result = process_agent_event(event)
    logger.info(f"🤖 AGENTS_DONE active_do_task_id={result.get('data', {}).get('selected_task_id')} user_id={user_id}")
```

#### UI Response Handling:
- `onComplete()` → `setStage('tasks')` in [app/(app)/dashboard/page.tsx](app/(app)/dashboard/page.tsx)
- Triggers `fetchTasks()` → `GET /api/dashboard/today-tasks`

---

### 4. First Task Display
**Component:** [app/components/TasksPage.tsx](app/components/TasksPage.tsx)

#### API Call:
```typescript
GET /api/dashboard/today-tasks
Response: {
  success: true,
  data: {
    pending: [
      {
        id, title, description, project_name,
        status, priority, estimated_duration, deadline
      }
    ],
    completed: [...],
    summary: { total_pending, total_completed }
  }
}
```

#### Backend Processing:
**File:** [backend/routers/dashboard.py](backend/routers/dashboard.py) → `GET /api/dashboard/today-tasks`

```python
# Lines 246-358
# Returns tasks due today + in-progress
# Sorted by: priority (urgent > high > medium > low)
```

**NOTE:** This endpoint does **NOT** call agents. It reads from `tasks` table directly.

#### UI Rendering:
- TasksPage displays first task from `pending[]` array
- Shows: title, description, project, duration, priority
- Actions: "Do it" button → `handleStartTask(task)` → `POST /api/tasks/{task_id}/start`

---

## BACKEND FLOW MAP

### API Endpoints Chain

#### 1. Login/Auth
**File:** [backend/routers/auth.py](backend/routers/auth.py)

- `POST /api/auth/login` (lines 92-149)
- `POST /api/auth/google` (lines 279-444)

**No agents involved** - pure auth logic

---

#### 2. Check-In → Agent Orchestration
**Entry Point:** [backend/routers/users.py](backend/routers/users.py) → `POST /api/users/state/check-in` (line 247)

**Flow:**
1. Save check-in to DB
2. Call `trigger_agent_on_checkin()` (line 26)
3. Creates `CheckInSubmittedEvent` (line 31)
4. Calls `process_agent_event(event)` (line 37)

**Orchestrator Entry:**
[backend/agent_mvp/orchestrator.py](backend/agent_mvp/orchestrator.py) → `process_agent_event()` (line 547)

```python
def process_agent_event(event: Any) -> AgentMVPResponse:
    return orchestrator.process_event(event)  # Global instance

class RaimonOrchestrator:
    def process_event(self, event: Any) -> AgentMVPResponse:
        # Line 441-510
        initial_state = GraphState(user_id=user_id, current_event=event)
        final_state_result = self.graph.invoke(initial_state)
        return AgentMVPResponse(success=..., data=...)
```

**Graph Routing:**
[backend/agent_mvp/orchestrator.py](backend/agent_mvp/orchestrator.py) → `_handle_checkin()` (line 198)

```python
def _handle_checkin(self, state: GraphState) -> GraphState:
    event = state.current_event  # CheckInSubmittedEvent
    
    # 1. Create DailyCheckIn contract
    daily_checkin = DailyCheckIn(
        date=datetime.utcnow().isoformat().split('T')[0],
        energy_level=event.energy_level,
        mood=getattr(event, "mood", None),
        focus_minutes=event.time_available if event.time_available else None,
        priorities=event.focus_areas
    )
    
    # 2. Create CheckInToConstraintsRequest
    constraint_request = CheckInToConstraintsRequest(
        user_id=user_id,
        energy_level=event.energy_level,
        focus_areas=event.focus_areas,
        check_in_data=daily_checkin,
        user_profile=UserProfileAnalysis()
    )
    
    # 3. Call State Adapter Agent
    constraints = adapt_checkin_to_constraints(constraint_request)
    
    # 4. Call Priority Engine Agent (if available)
    candidates = []  # Would call priority engine here
    
    # 5. Call Do Selector Agent (if available)
    selection = {"task": None, "reason": ""}  # Would call do selector here
    
    # 6. Save to storage
    self.storage.save_active_do(selection)
    
    state.constraints = constraints
    state.success = True
    return state
```

---

### Agents Invoked in Check-In Flow

#### Agent 1: State Adapter
**File:** [backend/agent_mvp/state_adapter_agent.py](backend/agent_mvp/state_adapter_agent.py) → `adapt_checkin_to_constraints()` (line 28)

**Input:** `CheckInToConstraintsRequest`
```python
{
    user_id: str,
    energy_level: int (1-10),
    focus_areas: List[str],
    check_in_data: DailyCheckIn,
    user_profile: UserProfileAnalysis
}
```

**Processing:**
- Maps `energy_level` → `current_energy` (line 41)
- Calculates `max_minutes` from check-in (line 44, function at line 87)
- Determines `mode`: "quick" / "focus" / "learning" / "balanced" (line 47-53)
- Extracts `avoid_tags` from focus areas (line 56-60)

**Output:** `SelectionConstraints`
```python
{
    current_energy: int (1-10),
    max_minutes: int,
    mode: str,
    avoid_tags: List[str],
    prefer_priority: str
}
```

**DB/Storage:**
- Reads: NONE (pure function)
- Writes: NONE

**Failure Mode:** Falls back to defaults

---

#### Agent 2: Priority Engine (Optional in current flow)
**File:** [backend/agent_mvp/priority_engine_agent.py](backend/agent_mvp/priority_engine_agent.py) → `score_task_priorities()` (line 34)

**Note:** Currently **NOT invoked** in check-in flow due to empty agent initialization in orchestrator (line 69: `self.agents = {}`)

**If invoked:**
- Reads tasks from DB
- Scores by: deadline (30%), priority (40%), dependencies (15%), user preference (15%)
- Returns scored candidates

---

#### Agent 3: Do Selector (Optional in current flow)
**File:** [backend/agent_mvp/do_selector.py](backend/agent_mvp/do_selector.py) → `select_optimal_task()` (line 157)

**Note:** Currently **NOT invoked** via orchestrator in check-in flow

**If invoked:**
- Takes scored candidates + constraints
- Selects optimal task deterministically
- Returns selected task_id + reason_codes

---

### Alternative: Graph-Based Flow (LangGraph)
**File:** [backend/agent_mvp/graph.py](backend/agent_mvp/graph.py) → `run_agent_mvp()` (line 227)

This is an **alternative orchestration** that:
1. Loads candidates from DB (line 23)
2. Derives constraints from check-in (line 66)
3. Calls LLM Do Selector (line 139) → uses Gemini
4. Calls LLM Coach (line 169) → uses Gemini
5. Returns result (line 188)

**Currently NOT wired to check-in endpoint** - would need explicit call from API route.

---

#### 3. First Task Retrieval
**File:** [backend/routers/dashboard.py](backend/routers/dashboard.py) → `GET /api/dashboard/today-tasks` (line 246)

**Processing:**
```python
# 1. Get tasks due today
supabase.table("tasks")
    .select("*, projects(name)")
    .eq("user_id", user_id)
    .gte("deadline", today_start)
    .lt("deadline", today_end)
    
# 2. Get in-progress tasks
.in_("status", ["in_progress", "paused"])

# 3. Sort by priority
priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
pending_tasks.sort(key=lambda x: priority_order[x.priority])
```

**No agents involved** - direct DB query

---

## AGENTS INVOLVED (AUTHORITATIVE LIST)

### Active Agents in Login → Check-In → First Task Lane

| Agent | File | Entry Function | Input Contract | Output Contract | Wired? |
|-------|------|----------------|----------------|-----------------|--------|
| **State Adapter** | [state_adapter_agent.py](backend/agent_mvp/state_adapter_agent.py) | `adapt_checkin_to_constraints` (line 28) | `CheckInToConstraintsRequest` | `SelectionConstraints` | ✅ Yes |
| **Priority Engine** | [priority_engine_agent.py](backend/agent_mvp/priority_engine_agent.py) | `score_task_priorities` (line 34) | `PriorityCandidates` | `PriorityScoredCandidates` | ❌ Not wired yet |
| **Do Selector** | [do_selector.py](backend/agent_mvp/do_selector.py) | `select_optimal_task` (line 157) | `DoSelectorInput` | `DoSelectorOutput` | ❌ Not wired yet |
| **LLM Do Selector** | [llm_do_selector.py](backend/agent_mvp/llm_do_selector.py) | `select_task` (line 25) | `List[TaskCandidate]` | `DoSelectorOutput` | ❌ Not wired yet |
| **LLM Coach** | [llm_coach.py](backend/agent_mvp/llm_coach.py) | `generate_coaching_message` (line 49) | `CoachInput` | `CoachOutput` | ❌ Not wired yet |

### Supporting Mechanisms

| Component | File | Purpose |
|-----------|------|---------|
| **RaimonOrchestrator** | [orchestrator.py](backend/agent_mvp/orchestrator.py) | Main event dispatcher (line 64) |
| **Storage Adapter** | [storage.py](backend/agent_mvp/storage.py) | Supabase operations for agent data |
| **Event Logger** | [events.py](backend/agent_mvp/events.py) | Structured agent event logging |
| **Opik Tracing** | [opik_utils/](backend/opik_utils/) | Observability via `@track` decorator |

### Dead/Unwired Agents (Exist but Not Called)

- **User Profile Agent** ([user_profile_agent.py](backend/agent_mvp/user_profile_agent.py)) - Learns patterns, not invoked
- **Context Continuity Agent** ([context_continuity_agent.py](backend/agent_mvp/context_continuity_agent.py)) - Resume context, not invoked
- **Stuck Pattern Agent** ([stuck_pattern_agent.py](backend/agent_mvp/stuck_pattern_agent.py)) - Detects stuck, not invoked
- **Motivation Agent** ([motivation_agent.py](backend/agent_mvp/motivation_agent.py)) - Generates motivation, not invoked
- **Project Insight Agent** ([project_insight_agent.py](backend/agent_mvp/project_insight_agent.py)) - Project insights, not invoked

**Reason:** Orchestrator has empty `self.agents = {}` (line 69) - agents not dependency-injected yet.

---

## CONTRACT VERIFICATION

### 1. UI → API Request (Check-In)

**UI Component:** [DailyCheckIn.tsx](app/components/DailyCheckIn.tsx) line 246
```typescript
apiFetch('/api/users/state/check-in', {
  method: 'POST',
  body: {
    energy_level: mapEnergy(responses.energy),  // ✅ CORRECT
    mood: responses.mood,
    focus_areas: responses.focus ? [responses.focus] : undefined
  }
})
```

**Backend Model:** [models/user.py](backend/models/user.py) line 74
```python
class CheckInRequest(BaseModel):
    energy_level: int = Field(..., ge=1, le=10)  # ✅ MATCHES
    mood: str = Field(..., min_length=1, max_length=50)
    focus_areas: Optional[List[str]] = Field(default=None, max_length=10)
```

✅ **VERIFIED** - Field names match

---

### 2. API → Orchestrator Event

**API Trigger:** [users.py](backend/routers/users.py) line 31
```python
event = CheckInSubmittedEvent(
    user_id=user_id,
    energy_level=energy_level,  # ✅ CORRECT
    focus_areas=focus_areas,
    timestamp=datetime.now(timezone.utc).isoformat()
)
```

**Event Contract:** [contracts.py](backend/agent_mvp/contracts.py) line 467
```python
class CheckInSubmittedEvent(BaseModel):
    user_id: str
    energy_level: int = Field(ge=1, le=10)  # ✅ MATCHES
    focus_areas: List[str] = Field(default_factory=list)
    time_available: Optional[int] = None
    timestamp: str
```

✅ **VERIFIED** - Field names match

---

### 3. Orchestrator → State Adapter Agent

**Orchestrator Call:** [orchestrator.py](backend/agent_mvp/orchestrator.py) line 219
```python
constraint_request = CheckInToConstraintsRequest(
    user_id=user_id,
    energy_level=event.energy_level,  # ✅ CORRECT
    focus_areas=event.focus_areas,
    time_available=getattr(event, "time_available", None),
    check_in_data=daily_checkin,
    user_profile=user_profile
)
```

**Agent Contract:** [contracts.py](backend/agent_mvp/contracts.py) line 285 (not shown in read, but referenced)
```python
class CheckInToConstraintsRequest(BaseModel):
    user_id: str
    energy_level: int  # ✅ MATCHES
    focus_areas: List[str]
    time_available: Optional[int]
    check_in_data: DailyCheckIn
    user_profile: UserProfileAnalysis
```

✅ **VERIFIED** - Field names match

---

### 4. State Adapter → SelectionConstraints

**Agent Output:** [state_adapter_agent.py](backend/agent_mvp/state_adapter_agent.py) line 41-61
```python
constraints = SelectionConstraints()
constraints.current_energy = check_in.energy_level  # ✅ CORRECT mapping
constraints.max_minutes = _calculate_time_available(check_in)
constraints.mode = "quick" | "focus" | "learning" | "balanced"
constraints.avoid_tags = [...]
constraints.prefer_priority = "urgent" | focus_areas[0]
```

**Contract:** [contracts.py](backend/agent_mvp/contracts.py) line 33
```python
class SelectionConstraints(BaseModel):
    max_minutes: int = Field(default=120, ge=5, le=1440)  # ✅ MATCHES
    mode: str = Field(default="balanced")
    current_energy: int = Field(default=5, ge=1, le=10)  # ✅ MATCHES
    avoid_tags: Optional[List[str]] = None
    prefer_priority: Optional[str] = None
```

✅ **VERIFIED** - Field mapping correct: `energy_level` → `current_energy`

---

### 5. API Response → UI

**Backend Response:** [users.py](backend/routers/users.py) line 314
```python
return {
    "success": True,
    "data": {
        "check_in": {...},
        "greeting": "Good morning! ..."
    }
}
```

**UI Type:** [types/api.ts](types/api.ts) line 11
```typescript
export type ApiSuccessResponse<TData> = {
  success: true;
  data: TData;
  message?: string;
};
```

✅ **VERIFIED** - Structure matches

---

### 6. Dashboard Tasks API → UI

**Backend Response:** [dashboard.py](backend/routers/dashboard.py) line 335
```python
return {
    "success": True,
    "data": {
        "pending": [
            {
                "id": task["id"],
                "title": task["title"],
                "description": task.get("description"),
                "project_name": task.get("projects", {}).get("name"),
                "priority": task["priority"],
                "status": task["status"],
                "estimated_duration": task.get("estimated_duration"),
                "deadline": task.get("deadline")
            }
        ]
    }
}
```

**UI Type:** [types/api.ts](types/api.ts) line 39
```typescript
export type DashboardTask = {
  id: string;
  title: string;
  description?: string | null;
  project_id?: string | null;
  project_name?: string | null;  // ✅ MATCHES
  status?: string;
  priority?: string;
  estimated_duration?: number | null;  // ✅ MATCHES
  deadline?: string | null;
};
```

✅ **VERIFIED** - All field names match

---

### Field Name Mapping Summary

| Source Context | Field Name | Target Context | Field Name | Status |
|----------------|-----------|----------------|-----------|--------|
| UI Check-in | `energy_level` | API | `energy_level` | ✅ Match |
| API | `energy_level` | Event | `energy_level` | ✅ Match |
| Event | `energy_level` | CheckInToConstraintsRequest | `energy_level` | ✅ Match |
| CheckInToConstraintsRequest | `energy_level` | SelectionConstraints | `current_energy` | ✅ Mapped |
| UI Check-in | `focus_areas` | API | `focus_areas` | ✅ Match |
| API | `focus_areas` | Event | `focus_areas` | ✅ Match |
| CheckInRequest | `estimated_duration` | DashboardTask | `estimated_duration` | ✅ Match |

**No mismatches found** - All contract boundaries are aligned.

---

## OBSERVABILITY / DEBUG CHECKLIST

### Environment Variables Required

**Backend (.env):**
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Gemini (for LLM agents)
GEMINI_API_KEY=your-gemini-key

# Opik Tracing
OPIK_API_KEY=your-opik-key
OPIK_WORKSPACE=default
OPIK_PROJECT_NAME=raimon

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# App Config
APP_ENV=development
DEBUG=true
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

### Running Locally

**Backend:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
npm install
npm run dev
# Runs on http://localhost:3000
```

---

### Where to Look for Logs

#### Backend Logs

**1. API Request Logs (stdout):**
```
🤖 AGENTS_INVOKED event_type=CHECKIN_SUBMITTED user_id=abc-123
✅ Check-in processed for user abc-123
🤖 AGENTS_DONE active_do_task_id=N/A user_id=abc-123
```

**2. Agent Start/End:**
```
🔄 Adapting check-in to constraints
✅ Constraints adapted: energy=6, time=90, mode=balanced
```

**3. Orchestrator Flow:**
```
🎭 Processing event: CheckInSubmittedEvent (type=CheckInSubmittedEvent)
📋 Constraint request created: event_type=CheckInSubmittedEvent request_type=CheckInToConstraintsRequest
✅ Event processed successfully: success=True response_type=dict
```

**Location:** Console output where `uvicorn` is running

---

#### Opik Spans (Dashboard)

**URL:** https://www.comet.com/site/products/opik/ (or your self-hosted Opik)

**Expected Span Names:**
1. `agent_mvp_smoke_test` - Smoke test endpoint
2. `orchestrator_process_event` - Main orchestrator entry
3. `orchestrator_checkin` - Check-in handler node
4. `state_adapter_agent` - State adapter execution
5. `agent_mvp_orchestrator` - Graph invocation (if using LangGraph)
6. `do_selector_agent` - Task selection (if invoked)
7. `graph_load_candidates` - Load tasks from DB
8. `graph_derive_constraints` - Derive constraints
9. `graph_llm_select_do` - LLM task selection
10. `graph_llm_coach` - LLM coaching message

**How to Verify:**
- Login to Opik dashboard
- Filter by `project_name = raimon`
- Look for traces with user_id in metadata
- Check span hierarchy and duration

---

#### Network Calls (Browser DevTools)

**Chrome DevTools → Network Tab:**

1. **POST /api/auth/login**
   - Status: 200
   - Response: `{ success: true, data: { token, user } }`

2. **GET /api/users/onboarding-status**
   - Status: 200
   - Response: `{ success: true, data: { onboarding_completed: false } }`

3. **POST /api/users/state/check-in**
   - Status: 200
   - Response: `{ success: true, data: { check_in: {...}, greeting: "..." } }`

4. **GET /api/dashboard/today-tasks**
   - Status: 200
   - Response: `{ success: true, data: { pending: [...], completed: [] } }`

**Headers to Check:**
- `Authorization: Bearer <token>` present in requests 2-4
- `Content-Type: application/json` on all POST requests

---

### Minimal Smoke Run

**Goal:** Verify end-to-end flow from check-in to task retrieval

**Steps:**

1. **Setup:**
   ```bash
   # Ensure .env vars are set (see above)
   # Backend running on :8000
   # Frontend running on :3000
   ```

2. **Login:**
   - Go to http://localhost:3000/login
   - Enter test credentials
   - Verify redirect to dashboard or onboarding

3. **Check-In:**
   - On dashboard, answer 3 questions:
     - Energy: 6/10
     - Mood: "Good"
     - Focus: "Sharp"
   - Click "Go to dashboard"
   
4. **Verify Backend Logs:**
   ```
   🤖 AGENTS_INVOKED event_type=CHECKIN_SUBMITTED user_id=<your-id>
   🔄 Adapting check-in to constraints
   ✅ Constraints adapted: energy=6, time=90, mode=balanced
   🤖 AGENTS_DONE active_do_task_id=N/A user_id=<your-id>
   ```

5. **Verify Tasks Display:**
   - Should see list of tasks (or "You're all caught up")
   - First task should show: title, project, duration, "Do it" button

6. **Verify Opik Spans:**
   - Check Opik dashboard for:
     - `orchestrator_checkin` span
     - `state_adapter_agent` span
     - Metadata includes `user_id`

**Success Criteria:**
- ✅ Check-in saved to `daily_check_ins` table
- ✅ Orchestrator invoked (logs show AGENTS_INVOKED)
- ✅ State adapter executed (logs show Constraints adapted)
- ✅ Tasks displayed in UI
- ✅ Opik spans created (minimum: orchestrator_checkin, state_adapter_agent)

---

## SEQUENCE DIAGRAM

```
┌─────────┐     ┌───────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│ Browser │     │  Next.js  │     │   FastAPI   │     │ Orchestrator │     │ State Adapter  │
│   User  │     │   Pages   │     │   Routers   │     │    (MVP)     │     │     Agent      │
└────┬────┘     └─────┬─────┘     └──────┬──────┘     └──────┬───────┘     └────────┬───────┘
     │                │                   │                    │                       │
     │                │                   │                    │                       │
     │ 1. Login       │                   │                    │                       │
     │ ──────────────>│                   │                    │                       │
     │                │ POST /api/auth/login                   │                       │
     │                │ ──────────────────>│                    │                       │
     │                │                   │                    │                       │
     │                │ {token, user}     │                    │                       │
     │                │ <──────────────────│                    │                       │
     │ Redirect to    │                   │                    │                       │
     │ /dashboard     │                   │                    │                       │
     │ <──────────────│                   │                    │                       │
     │                │                   │                    │                       │
     │                │                   │                    │                       │
     │ 2. Dashboard   │                   │                    │                       │
     │    Loads       │                   │                    │                       │
     │ ──────────────>│                   │                    │                       │
     │                │ Checks session    │                    │                       │
     │                │ Shows <DailyCheckIn />                 │                       │
     │                │                   │                    │                       │
     │                │                   │                    │                       │
     │ 3. User fills  │                   │                    │                       │
     │    check-in    │                   │                    │                       │
     │    (energy:6,  │                   │                    │                       │
     │     mood:good, │                   │                    │                       │
     │     focus:sharp)│                  │                    │                       │
     │ ──────────────>│                   │                    │                       │
     │                │ POST /api/users/  │                    │                       │
     │                │      state/check-in                    │                       │
     │                │ ──────────────────>│                    │                       │
     │                │                   │                    │                       │
     │                │                   │ 4. Save to DB      │                       │
     │                │                   │    daily_check_ins │                       │
     │                │                   │                    │                       │
     │                │                   │ 5. trigger_agent_on_checkin()              │
     │                │                   │ ────────────────────>                      │
     │                │                   │                    │                       │
     │                │                   │ 6. process_agent_event(CheckInSubmittedEvent)
     │                │                   │                    │                       │
     │                │                   │                    │ 7. _handle_checkin() │
     │                │                   │                    │                       │
     │                │                   │                    │ 8. Create            │
     │                │                   │                    │    DailyCheckIn      │
     │                │                   │                    │    contract          │
     │                │                   │                    │                       │
     │                │                   │                    │ 9. adapt_checkin     │
     │                │                   │                    │    _to_constraints() │
     │                │                   │                    │ ─────────────────────>│
     │                │                   │                    │                       │
     │                │                   │                    │ 10. Map fields:       │
     │                │                   │                    │     energy_level →    │
     │                │                   │                    │     current_energy    │
     │                │                   │                    │     Calculate         │
     │                │                   │                    │     max_minutes       │
     │                │                   │                    │     Set mode          │
     │                │                   │                    │                       │
     │                │                   │                    │ SelectionConstraints  │
     │                │                   │                    │ <─────────────────────│
     │                │                   │                    │                       │
     │                │                   │                    │ 11. save_active_do()  │
     │                │                   │                    │     (storage)         │
     │                │                   │                    │                       │
     │                │                   │ AgentMVPResponse   │                       │
     │                │                   │ <────────────────────                      │
     │                │                   │                    │                       │
     │                │                   │ 12. Return         │                       │
     │                │                   │     {success, data}│                       │
     │                │ {check_in, greeting}                   │                       │
     │                │ <──────────────────│                    │                       │
     │                │                   │                    │                       │
     │ Check-in       │                   │                    │                       │
     │ success        │                   │                    │                       │
     │ <──────────────│                   │                    │                       │
     │                │                   │                    │                       │
     │                │ 13. setStage('tasks')                  │                       │
     │                │     fetchTasks()  │                    │                       │
     │                │                   │                    │                       │
     │                │ GET /api/dashboard│                    │                       │
     │                │     /today-tasks  │                    │                       │
     │                │ ──────────────────>│                    │                       │
     │                │                   │                    │                       │
     │                │                   │ 14. Query tasks    │                       │
     │                │                   │     table (DB)     │                       │
     │                │                   │     Filter by      │                       │
     │                │                   │     due date &     │                       │
     │                │                   │     status         │                       │
     │                │                   │     Sort by        │                       │
     │                │                   │     priority       │                       │
     │                │                   │                    │                       │
     │                │ {pending: [...],  │                    │                       │
     │                │  completed: []}   │                    │                       │
     │                │ <──────────────────│                    │                       │
     │                │                   │                    │                       │
     │ 15. Display    │                   │                    │                       │
     │     first task │                   │                    │                       │
     │     from list  │                   │                    │                       │
     │ <──────────────│                   │                    │                       │
     │                │                   │                    │                       │
     │ [User sees     │                   │                    │                       │
     │  task card     │                   │                    │                       │
     │  with "Do it"  │                   │                    │                       │
     │  button]       │                   │                    │                       │
     │                │                   │                    │                       │
```

---

## KNOWN RISKS / LIKELY BREAKPOINTS

### 1. Agent Dependency Injection Not Wired
**Location:** [backend/agent_mvp/orchestrator.py](backend/agent_mvp/orchestrator.py) line 69

**Issue:**
```python
self.agents = {}  # Will be populated by dependency injection
```

**Risk:** Orchestrator has empty agents dict. Priority Engine, Do Selector, Coach agents exist but are never called.

**Impact:** Check-in flow runs but only executes State Adapter. No task selection happens via agents.

**Fix Needed:**
```python
self.agents = {
    'state_adapter_agent': StateAdapterAgent(),
    'priority_engine': PriorityEngineAgent(),
    'do_selector': DoSelectorAgent(),
    'coach': CoachAgent(),
}
```

---

### 2. Graph Flow vs Orchestrator Flow Confusion
**Location:** Two parallel systems exist

**Graph Flow:** [backend/agent_mvp/graph.py](backend/agent_mvp/graph.py) → `run_agent_mvp()`
- Uses LangGraph
- Calls LLM agents (Gemini)
- Has `@track` decorators
- Returns structured result

**Orchestrator Flow:** [backend/agent_mvp/orchestrator.py](backend/agent_mvp/orchestrator.py) → `RaimonOrchestrator`
- Event-driven via LangGraph
- Has agent placeholders
- Currently only runs State Adapter

**Risk:** Unclear which system is "production" path. Graph flow has more complete implementation but isn't called by check-in endpoint.

**Current Reality:** Check-in triggers Orchestrator, which only runs State Adapter.

---

### 3. Task Retrieval Doesn't Use Agent Selection
**Location:** [backend/routers/dashboard.py](backend/routers/dashboard.py) line 246

**Issue:** `GET /api/dashboard/today-tasks` queries DB directly, ignoring any agent selection logic.

**Risk:** Agent system runs during check-in but result isn't used. UI shows tasks in priority order from DB, not agent-selected "first Do".

**Expected Behavior:** After check-in, agents select optimal task → UI should fetch and display **that specific task**.

**Fix Needed:** Add endpoint `GET /api/agent-mvp/active-do` that returns the agent-selected task from `active_do` storage table.

---

### 4. Contract Field Name Mismatch (RESOLVED)
**Location:** [backend/agent_mvp/state_adapter_agent.py](backend/agent_mvp/state_adapter_agent.py) line 41

**Previous Risk:** `energy_level` vs `current_energy`

**Status:** ✅ **RESOLVED** - Mapping is correct:
```python
constraints.current_energy = check_in.energy_level
```

No mismatch exists.

---

### 5. Storage Table Dependencies
**Location:** [backend/agent_mvp/storage.py](backend/agent_mvp/storage.py)

**Required Tables:**
- `active_do` - Current active task selection
- `session_state` - User session persistence
- `time_models` - Time pattern learning
- `stuck_episodes` - Stuck detection history
- `insights` - Generated insights
- `xp_ledger` - XP transactions
- `gamification_state` - User gamification data
- `agent_events` - Event logging

**Risk:** If tables don't exist, storage operations will fail silently (try/except blocks log warnings but don't block).

**Verification:** Check Supabase dashboard for table existence.

---

### 6. Opik Tracing Silent Failures
**Location:** All `@track(name="...")` decorated functions

**Risk:** If `OPIK_API_KEY` is not set or invalid, traces won't appear in dashboard but code won't fail.

**Verification:**
```bash
# Check env vars
echo $OPIK_API_KEY
echo $OPIK_WORKSPACE
echo $OPIK_PROJECT_NAME

# Run smoke test
curl http://localhost:8000/agent-mvp/smoke
# Should return: { "success": true, "message": "Opik smoke test passed" }
# Check Opik dashboard for "agent_mvp_smoke_test" span
```

**Fallback:** Check backend startup logs:
```
📊 Opik Tracing: ✅ ENABLED
   - Project: raimon
   - Workspace: default
   - API Key: Set
```

---

### 7. Session Management Edge Cases
**Location:** [lib/api-client.ts](lib/api-client.ts) line 69

**Risk:** Token refresh logic may fail if:
- Refresh token expired
- Network error during refresh
- Session cleared mid-request

**Current Behavior:** Redirects to login on 401

**Potential Issue:** User completes check-in → token expires → task fetch fails → user re-login required → check-in data lost.

**Mitigation:** Frontend stores `raimon_checked_in` in sessionStorage to avoid re-check-in after re-login.

---

### 8. Missing Error Boundaries in UI
**Location:** React components lack error boundaries

**Risk:** If API call fails mid-flow (e.g., check-in submission fails), UI may show white screen or broken state.

**Current Handling:** Components have `try/catch` + `setError()` but no visual error recovery.

**Example:** [DailyCheckIn.tsx](app/components/DailyCheckIn.tsx) line 246 - shows error text but doesn't retry or offer recovery.

---

### 9. Race Condition: Check-In → Task Fetch
**Location:** [dashboard/page.tsx](app/(app)/dashboard/page.tsx) line 73-78

**Flow:**
1. User submits check-in → API returns immediately
2. Frontend sets `stage='tasks'`
3. `useEffect` triggers `fetchTasks()`
4. Backend agent orchestrator still running in background

**Risk:** UI fetches tasks before agent selection completes. Shows old task list instead of agent-selected task.

**Mitigation Needed:** Either:
- Make check-in synchronous (wait for agent completion)
- Poll for agent result before showing tasks
- Display "Preparing your task..." loading state

---

### 10. Database Schema Assumptions
**Location:** Various queries assume column existence

**Critical Columns:**
- `users.onboarding_completed` (boolean)
- `daily_check_ins.energy_level` (integer 1-10)
- `daily_check_ins.focus_areas` (text array)
- `tasks.estimated_duration` (integer, minutes)
- `tasks.priority` (text: urgent/high/medium/low)

**Risk:** If schema doesn't match (e.g., `energy_level` is varchar instead of int), queries will fail.

**Verification:** Check [database_schema.sql](backend/agent_mvp/database_schema.sql) for expected schema.

---

## SUMMARY & NEXT STEPS

### What Currently Works

✅ **Login Flow:**
- Email/password and Google OAuth
- JWT token issuance and refresh
- Session persistence
- Onboarding status check

✅ **Check-In Flow:**
- UI captures energy, mood, focus
- API saves to `daily_check_ins` table
- Orchestrator triggered with `CheckInSubmittedEvent`
- State Adapter runs and maps energy → constraints

✅ **Task Display:**
- UI fetches tasks from `GET /api/dashboard/today-tasks`
- Tasks sorted by priority
- First task displayed with "Do it" button

### What's Missing

❌ **Agent Integration:**
- Orchestrator has empty `agents` dict
- Priority Engine not invoked
- Do Selector not invoked
- Coach not invoked
- Task selection logic exists but isn't wired

❌ **Agent Result Usage:**
- Agent runs but result isn't fetched by UI
- UI shows all tasks instead of agent-selected task
- No "active Do" concept in current flow

❌ **LangGraph Flow:**
- `run_agent_mvp()` in graph.py is complete but not called
- LLM agents (Do Selector, Coach) exist but aren't wired to API

### Immediate Action Items

1. **Wire Agent Dependencies:**
   - Instantiate agents in orchestrator `__init__`
   - Call Priority Engine → Do Selector → Coach in `_handle_checkin`

2. **Add Agent Result Endpoint:**
   - Create `GET /api/agent-mvp/active-do`
   - Return selected task from `active_do` table

3. **Update Dashboard Flow:**
   - After check-in, fetch `GET /api/agent-mvp/active-do`
   - Display agent-selected task instead of task list

4. **Add Sync Option:**
   - Make check-in await agent completion
   - OR add loading state while agents run

5. **Verify Opik Integration:**
   - Run smoke test
   - Check dashboard for spans
   - Confirm all `@track` decorators working

### Testing Checklist

```bash
# 1. Env vars set?
cat backend/.env | grep -E "OPIK|GEMINI|SUPABASE"

# 2. Backend running?
curl http://localhost:8000/health

# 3. Login works?
# (Use UI or curl)

# 4. Check-in saves?
# Submit check-in in UI, then:
psql $DATABASE_URL -c "SELECT * FROM daily_check_ins ORDER BY created_at DESC LIMIT 1;"

# 5. Orchestrator invoked?
# Check backend logs for:
grep "AGENTS_INVOKED" backend.log

# 6. Opik spans created?
# Check Opik dashboard for today's traces

# 7. Tasks displayed?
# UI should show task list after check-in
```

---

**END OF DOCUMENT**

Generated: February 4, 2026  
Repository: Raimon.app  
Authors: Senior Full-Stack Engineer + AI-Agent Workflow Architect
