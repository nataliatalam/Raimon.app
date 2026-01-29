"""
Agent MVP: Gemini-Powered Task Selection & Coaching

This is a minimal, production-ready MVP that orchestrates two LLM agents
using LangGraph for task selection and motivational coaching.

================================================================================
QUICK START
================================================================================

1. Prerequisites:
   - GOOGLE_API_KEY set in .env (Gemini access)
   - SUPABASE_URL, SUPABASE_KEY set (task data)
   - OPIK_API_KEY, OPIK_WORKSPACE, OPIK_PROJECT_NAME (observability)
   - Python 3.10+
   - Dependencies: fastapi, google-genai, opik, supabase-py

2. Run the backend:
   uvicorn main:app --reload

3. Test the endpoint:

   # Authenticated request (requires valid JWT token):
   curl -X POST http://localhost:8000/agent-mvp/next-do \\
     -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \\
     -H "Content-Type: application/json"

   # Or use the simulate endpoint (no auth required):
   curl -X POST http://localhost:8000/agent-mvp/simulate

4. Run tests:
   pytest backend/tests_agent_mvp/ -v

================================================================================
ARCHITECTURE
================================================================================

FOLDER STRUCTURE:
backend/agent_mvp/
  ├── __init__.py                # Package docs
  ├── contracts.py               # Pydantic data models
  ├── gemini_client.py           # Gemini wrapper with Opik tracing
  ├── prompts.py                 # LLM prompt templates
  ├── validators.py              # Output validation & fallback logic
  ├── llm_do_selector.py         # DoSelector agent (task selection)
  ├── llm_coach.py               # Coach agent (motivational copy)
  └── graph.py                   # LangGraph orchestrator (6 nodes)

backend/routers/
  └── agent_mvp.py               # FastAPI router (2 endpoints)

backend/tests_agent_mvp/
  ├── test_graph.py              # Integration + node tests
  ├── test_selector_contracts.py # Validation + contract tests
  └── __init__.py

================================================================================
AGENTS
================================================================================

1. DO SELECTOR (Gemini 2.5-flash-lite)
   ─────────────────────────────────────

   Input:
   - List of candidate tasks (open tasks for user)
   - Constraints: max_time, energy, mode (focus/quick/learning/balanced)
   - Optional: recent actions context

   Process:
   - Builds bounded prompt with all candidate info
   - Calls Gemini with temp=0.5 (deterministic)
   - Expects strict JSON: { task_id, reason_codes[], alt_task_ids[] }

   Output:
   - task_id: UUID of selected task (MUST be in candidates)
   - reason_codes: Array of 0-3 reason labels (e.g., "deadline_urgent")
   - alt_task_ids: 0-2 alternative tasks

   Fallback:
   - If LLM returns invalid JSON or non-existent task_id
   - Deterministic fallback: pick highest priority + shortest duration
   - Logged as "fallback_deterministic"


2. COACH (Gemini 2.5-flash-lite)
   ──────────────────────────────

   Input:
   - Selected task object (title, priority, duration, due_at)
   - Reason codes explaining why selected
   - Mode (focus/quick/learning/balanced)
   - Optional: user name

   Process:
   - Builds bounded prompt (no hallucination risk)
   - Calls Gemini with temp=0.8 (creative but controlled)
   - Expects strict JSON: { title, message, next_step }

   Output:
   - title: Short motivational phrase (≤100 chars)
   - message: 1-2 sentences max (≤300 chars)
   - next_step: Micro-action under 10 words

   Fallback:
   - If LLM violates constraints (e.g., message too long)
   - Returns: { "Let's go", "You've got this.", "Begin." }


================================================================================
LANGGRAPH ORCHESTRATION (6 nodes)
================================================================================

   ┌──────────────────┐
   │ 1. Load Candidates│  → Query Supabase for user's open tasks
   └────────┬─────────┘
            │
   ┌────────▼──────────────┐
   │2. Derive Constraints  │  → Read energy from daily_check_in or defaults
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │3. LLM Select Do       │  → Call DoSelector agent
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │4. Validate/Fallback   │  → Validate task_id in candidates
   └────────┬──────────────┘   (fallback is automatic in agent)
            │
   ┌────────▼──────────────┐
   │5. LLM Coach           │  → Call Coach agent for messaging
   └────────┬──────────────┘
            │
   ┌────────▼──────────────┐
   │6. Return Result       │  → Format response JSON
   └──────────────────────┘

   State carries:
   - user_id, candidates[], constraints, active_do, coach_message, error


================================================================================
ENDPOINTS
================================================================================

1. POST /agent-mvp/next-do
   ─────────────────────────
   Auth: Required (Bearer JWT token)

   Request body (optional):
   {
     "max_minutes": 120,
     "mode": "balanced",
     "current_energy": 6,
     "avoid_tags": ["admin"],
     "prefer_priority": "high"
   }

   Response:
   {
     "success": true,
     "data": {
       "active_do": {
         "task_id": "uuid-123",
         "task_title": "Fix login page CSS",
         "reason_codes": ["priority_high", "deadline_soon"],
         "alt_task_ids": ["uuid-456"],
         "selected_at": "2026-01-28T12:00:00Z"
       },
       "coach_message": {
         "title": "CSS time!",
         "message": "Let's fix the login page. You've got this.",
         "next_step": "Open the CSS file."
       }
     }
   }

   Errors:
   - 404: No open tasks found
   - 500: Agent processing error


2. POST /agent-mvp/simulate
   ──────────────────────────
   Auth: Not required
   Purpose: Local testing with mock tasks (no DB)

   Request body (optional):
   {
     "max_minutes": 60,
     "mode": "quick",
     "current_energy": 4
   }

   Response: Same format as /next-do


================================================================================
DATA MODELS (Pydantic Contracts)
================================================================================

TaskCandidate:
  id (str)                      # UUID
  title (str)                   # 1-500 chars, sanitized
  priority (str)                # low/medium/high/urgent
  status (str)                  # todo/in_progress/paused/blocked/completed
  estimated_duration (int)      # 1-1440 minutes
  due_at (datetime, optional)   # ISO string
  tags (List[str], optional)    # 0-20 tags
  created_at (datetime)         # ISO string

SelectionConstraints:
  max_minutes (int)             # 5-1440 (default 120)
  mode (str)                    # focus/quick/learning/balanced (default balanced)
  current_energy (int)          # 1-10 (default 5)
  avoid_tags (List[str])        # tags to exclude
  prefer_priority (str)         # if provided, prioritize this priority

DoSelectorOutput:
  task_id (str)                 # Must be one of candidate IDs
  reason_codes (List[str])      # 0-3 codes
  alt_task_ids (List[str])      # 0-2 alternative IDs

CoachOutput:
  title (str)                   # 1-100 chars
  message (str)                 # 5-300 chars, 1-2 sentences max
  next_step (str)               # 1-100 chars, under 10 words


================================================================================
OPIK TRACING
================================================================================

Every LLM call and graph node is automatically traced in Opik:

Traced Functions:
  @track(name="gemini_call")
    ├─ agent_mvp_orchestrator (main entry point)
    ├─ graph_load_candidates (Supabase query)
    ├─ graph_derive_constraints (check-in lookup)
    ├─ graph_llm_select_do (DoSelector call)
    ├─ graph_llm_coach (Coach call)
    └─ graph_return_result (format response)

  @track(name="gemini_call")
    ├─ do_selector_agent (with DoSelector.select_task)
    └─ coach_agent (with Coach.generate_coaching_message)

  @track(name="gemini_call")
    ├─ GeminiClient.generate_json_response (Gemini API call)
    └─ GeminiClient.generate_text (Gemini API call)

Visible in Opik dashboard:
  - Request/response pairs
  - Token usage per call
  - Latency metrics
  - Error tracking
  - Custom metadata (user_id, task_id, etc.)


================================================================================
VALIDATION & FALLBACK STRATEGY
================================================================================

PROBLEM: LLMs sometimes hallucinate, violate JSON, or pick invalid tasks

SOLUTION: Strict validation with deterministic fallback

DoSelector:
  1. Parse JSON response from Gemini
  2. Check task_id exists in candidates
  3. Filter alt_task_ids to only valid candidates
  4. If any validation fails → use fallback
     - Fallback: pick highest priority + shortest duration
     - Logged for observability
  5. Return (DoSelectorOutput, is_valid: bool)

Coach:
  1. Parse JSON response from Gemini
  2. Validate:
     - title: 1-100 chars
     - message: 1-2 sentences, ≤300 chars
     - next_step: under 10 words
  3. If validation fails → use minimal fallback
     - Fallback: { "Let's go", "You've got this.", "Begin." }
  4. Return (CoachOutput, is_valid: bool)


================================================================================
CONSTRAINTS
================================================================================

✅ ALLOWED:
  - Read-only Supabase queries (tasks, projects, daily_check_ins, work_sessions)
  - Call Gemini models (JSON-constrained prompts)
  - Log to Opik for observability
  - Validate and fallback gracefully
  - Return standardized JSON responses

❌ NOT ALLOWED (in MVP):
  - Writing to tasks table (no mutations)
  - Creating streaks or XP
  - Calling external APIs
  - Storing selection history in DB
  - Running long-lived background jobs


================================================================================
TESTING
================================================================================

Run all tests:
  pytest backend/tests_agent_mvp/ -v

Run specific test file:
  pytest backend/tests_agent_mvp/test_graph.py -v

Run specific test:
  pytest backend/tests_agent_mvp/test_graph.py::test_do_selector_returns_valid_task_id -v

Test coverage:
  - ✅ DoSelector returns valid task_id from candidates
  - ✅ Invalid LLM output triggers fallback
  - ✅ Fallback picks highest priority + shortest task
  - ✅ Coach output is short (1-2 sentences)
  - ✅ Coach message respects task context
  - ✅ Coach falls back on validation error
  - ✅ Graph nodes flow state correctly
  - ✅ End-to-end flow with mocks
  - ✅ Contract validation (TaskCandidate, SelectionConstraints, etc.)
  - ✅ Constraints validate energy range, max_minutes, mode


================================================================================
DEPLOYMENT CHECKLIST
================================================================================

Before deploying to production:

  □ GOOGLE_API_KEY configured in .env
  □ OPIK_API_KEY, OPIK_WORKSPACE, OPIK_PROJECT_NAME set
  □ Supabase URL and keys configured
  □ JWT secrets configured (existing)
  □ Rate limiting enabled (existing middleware)
  □ CORS origins updated for production domain
  □ SSL/TLS certificates valid
  □ Opik project created in dashboard
  □ Test endpoint with real user JWT token
  □ Monitor Opik dashboard for LLM costs
  □ Set up alerts for failed requests (>10% error rate)
  □ Document endpoint in API docs
  □ Add endpoint to API gateway if using one


================================================================================
PERFORMANCE & COST NOTES
================================================================================

Latency:
  - Supabase query: ~50-200ms
  - DoSelector LLM call: ~1-3 seconds
  - Coach LLM call: ~0.5-1.5 seconds
  - Total end-to-end: ~3-5 seconds

Cost per request:
  - DoSelector: ~500 input tokens + ~50 output tokens
  - Coach: ~400 input tokens + ~20 output tokens
  - Using Gemini 2.5-flash-lite (cheapest model)
  - ~$0.001-0.002 USD per full request

Optimization tips:
  - Cache task queries by user (Redis)
  - Batch multiple users' requests
  - Use temperature=0.5 for DoSelector (deterministic)
  - Limit output tokens (max_tokens=200-300)
  - Monitor Opik for expensive LLM calls


================================================================================
FUTURE ENHANCEMENTS
================================================================================

Potential improvements after MVP:
  1. Persist selection history in ai_learning_data table
  2. A/B test different prompt variations
  3. Add more reason codes (task dependencies, collaborators, etc.)
  4. Multi-modal input (voice, image recognition)
  5. Real-time task filtering (due task changes)
  6. User preference learning (weight reason codes)
  7. Batch selection API (multiple tasks at once)
  8. Scheduled recommendations (daily digest)
  9. Fallback to more conservative prompts under load
  10. Redis caching for frequent queries


================================================================================
TROUBLESHOOTING
================================================================================

Issue: "GOOGLE_API_KEY not set"
  → Check .env file has GOOGLE_API_KEY=sk-...
  → Ensure env vars are loaded before starting app

Issue: "No open tasks found"
  → User has no tasks in status: todo/in_progress/paused/blocked
  → Check tasks table in Supabase for this user_id

Issue: "Invalid JSON from Gemini"
  → Fallback selected automatically
  → Check Opik dashboard for failed LLM calls
  → May need to refine prompts if frequent

Issue: "task_id not in candidates"
  → Gemini hallucinated a task ID
  → Fallback selected deterministically
  → Logged in Opik, safe to ignore

Issue: Slow responses (>10 seconds)
  → Check Supabase query performance
  → Check Gemini API latency in Opik
  → Consider caching candidate list

Issue: Tests fail with import errors
  → Ensure backend/ is in PYTHONPATH
  → Run from repo root: pytest backend/tests_agent_mvp/
  → Check Python 3.10+ installed
"""
