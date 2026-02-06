# Raimon.app Backend Refactoring Plan

**Date**: February 2025
**Status**: Strategic Planning Phase
**Golden Standard**: `agent_mvp` folder architecture (LangGraph orchestration + Pydantic contracts)

---

## Executive Summary

This document outlines a comprehensive refactoring strategy to consolidate the Raimon backend into a modular, agent-centric architecture. The `agent_mvp` folder serves as the "Golden Standard"—all other code will be refactored to conform to its LangGraph-based orchestration pattern and strict Pydantic data contracts.

### Key Objectives
1. **Structural Consolidation**: Move scattered agent logic into unified `backend/agents/` directory
2. **Orchestration Enhancement**: Centralize LangGraph state machine in `backend/orchestrator/`
3. **Contract Enforcement**: Ensure all data flows through Pydantic models in `backend/models/contracts.py`
4. **Observability**: Implement comprehensive Opik tracing across all agents and endpoints
5. **Modularity**: Enable agents as "plugins" that can be added/removed without breaking the system

---

## Part 1: Proposed Directory Structure

### ASCII Tree (Current + Refactored)

```
backend/
│
├── core/                           # ✅ EXISTING (Keep as-is)
│   ├── __init__.py
│   ├── config.py                   # Application settings
│   ├── security.py                 # JWT, authentication
│   ├── supabase.py                 # Supabase client singleton
│   └── rate_limit.py               # Rate limiting
│
├── models/                         # ✅ EXISTING (Enhance)
│   ├── __init__.py
│   ├── auth.py                     # Auth models
│   ├── contracts.py                # 🔄 REFACTOR: Add mood, energy, intervention_logs
│   ├── user.py                     # User models
│   ├── task.py                     # Task models
│   ├── project.py                  # Project models
│   ├── notification.py             # Notification models
│   └── next_do.py                  # Task selection models
│
├── agents/                         # 🆕 NEW CONSOLIDATED AGENTS DIR
│   ├── __init__.py                 # Export all agent factories
│   │
│   ├── llm_agents/                 # LLM-Powered Agents (call Gemini)
│   │   ├── __init__.py
│   │   ├── do_selector.py          # Task selection via LLM
│   │   ├── coach.py                # Motivational coaching messages
│   │   ├── motivation_agent.py     # Motivation generation
│   │   ├── stuck_pattern_agent.py  # Stuck detection + microtasks
│   │   ├── project_insight_agent.py# Project progress insights
│   │   ├── context_continuity_agent.py # Context resumption
│   │   ├── prompts.py              # Centralized LLM prompts
│   │   └── base.py                 # BaseLLMAgent abstract class
│   │
│   ├── deterministic_agents/       # Pure Logic Agents (no LLM calls)
│   │   ├── __init__.py
│   │   ├── user_profile_agent.py   # Analyze user patterns
│   │   ├── state_adapter_agent.py  # Check-in → constraints
│   │   ├── priority_engine_agent.py# Score task candidates
│   │   ├── time_learning_agent.py  # Time pattern analysis
│   │   ├── gamification_rules.py   # XP/level/streak updates
│   │   └── base.py                 # BaseDeterministicAgent
│   │
│   ├── contracts.py                # Agent I/O Pydantic schemas
│   ├── events.py                   # Event definitions & logging
│   └── factory.py                  # Agent factory for DI
│
├── orchestrator/                   # 🔄 REFACTOR: Enhanced LangGraph
│   ├── __init__.py
│   ├── orchestrator.py             # RaimonOrchestrator (LangGraph runner)
│   ├── graph.py                    # GraphState definition
│   ├── nodes.py                    # Node handler functions
│   ├── edges.py                    # Edge routing logic
│   ├── contracts.py                # 🔄 ENHANCE: Add mood, energy, logs
│   └── validators.py               # Fallback validation + recovery
│
├── services/                       # ✅ EXISTING (No changes needed)
|   |    └── llm_service
|   |          ├── __init__.py
|   |          ├── base_llm_client.py
|   |          ├── gemini_client.py
|   |          └── llm_service.py
|   |         
│   ├── __init__.py
│   ├── llm_services.py             # LLM API wrapper
│   ├── user_service.py             # User business logic
│   ├── task_service.py             # Task business logic
│   ├── project_service.py          # Project business logic
│   └── gamification_service.py     # Gamification logic
│
├── database/                       # ✅ EXISTING
│   ├── migrations/
│   │   ├── 001_flower_points_graveyard.sql
│   │   ├── 002_add_notes_column.sql
│   │   └── 003_agent_mvp_tables.sql
│   └── schema.sql
│
├── opik_utils/                     # 🔄 REFACTOR: Enhanced Observability
│   ├── __init__.py
│   ├── config.py                   # Opik configuration
│   ├── client.py                   # OpikManager singleton
│   ├── decorators.py               # @track decorator
│   ├── middleware.py               # FastAPI middleware
│   │
│   ├── trackers/                   # Specialized trackers
│   │   ├── __init__.py
│   │   ├── agent_tracker.py        # Track agent executions
│   │   ├── action_tracker.py       # Track LLM calls
│   │   ├── cost_tracker.py         # Track LLM costs
│   │   └── workflow_tracker.py     # Track orchestrator flows
│   │
│   ├── evaluators/                 # 🆕 Quality evaluators
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseEvaluator abstract class
│   │   ├── hallucination_evaluator.py # Detect LLM hallucinations
│   │   ├── motivation_rubric.py    # Evaluate motivation quality
│   │   ├── selection_accuracy.py   # Evaluate task selection
│   │   └── stuck_detection.py      # Evaluate stuck detection accuracy
│   │
│   ├── metrics/                    # 🆕 Custom metrics
│   │   ├── __init__.py
│   │   ├── agent_metrics.py        # Agent performance metrics
│   │   ├── task_selection_metrics.py # Selection quality metrics
│   │   └── user_engagement.py      # User engagement metrics
│   │
│   ├── dashboards/                 # 🆕 Visualization configs
│   │   ├── __init__.py
│   │   └── opik_queries.py         # Pre-built Opik queries
│   │
│   └── utils.py                    # Helper utilities
│
├── routers/                        # ✅ EXISTING (Minor updates)
│   ├── __init__.py
│   ├── auth.py                     # Auth endpoints
│   ├── users.py                    # User endpoints
│   ├── projects.py                 # Project endpoints
│   ├── tasks.py                    # Task endpoints
│   ├── dashboard.py                # Dashboard endpoints
│   ├── analytics.py                # Analytics endpoints
│   ├── notifications.py            # Notification endpoints
│   ├── reminders.py                # Reminder endpoints
│   ├── integrations.py             # Integration endpoints
│   ├── feedback.py                 # Feedback endpoints
│   ├── agent_mvp.py                # 🔄 REFACTOR: Use new agents
│   └── agents/                     # 🆕 Agent-specific endpoints
│       ├── __init__.py
│       └── management.py           # Agent health/status endpoints
│
├── middleware/                     # 🆕 Middleware components
│   ├── __init__.py
│   ├── cors_middleware.py          # CORS handling
│   ├── jwt_middleware.py           # JWT authentication
│   └── request_size_limit.py       # Request size limits
│
├── main.py                         # 🔄 REFACTOR: Updated imports
├── requirements.txt                # Dependencies
└── pytest.ini                      # Test configuration

tests/
├── __init__.py
├── conftest.py                     # 🆕 Shared fixtures
│
├── test_agents/                    # 🆕 Agent tests
│   ├── __init__.py
│   ├── test_llm_agents.py
│   ├── test_deterministic_agents.py
│   └── test_agent_contracts.py
│
├── test_orchestrator/              # 🆕 Orchestrator tests
│   ├── __init__.py
│   ├── test_graph.py
│   ├── test_routing.py
│   └── test_state_management.py
│
├── test_opik/                      # 🆕 Observability tests
│   ├── __init__.py
│   ├── test_decorators.py
│   ├── test_evaluators.py
│   └── test_metrics.py
│
├── test_services/                  # Service tests
│   └── __init__.py
│
├── test_routers/                   # Router/endpoint tests
│   └── __init__.py
│
└── tests_agent_mvp/                # ✅ EXISTING (Keep as-is)
    ├── __init__.py
    ├── test_graph.py
    └── test_selector_contracts.py
              
docs/
├── README.md                           # START HERE
├── END_TO_END_FLOW.md                  # Complete flow overview
│
└── docs/                               # MAIN DOCUMENTATION
    |── frontend/
    |   └── /
    |
    └── backend/
        ├── README.md                       # Backend overview
        ├── security.md                 # Security
        ├── vscode-setup.md             # IDE setup
        ├── CODE_CHANGES_REFERENCE.md       # What changed
        |
        ├── agent_mvp/                     # ✅ EXISTING Agent MVP docs
        │   ├── AGENT_MVP_INDEX.md         # Start here for agent_mvp
        │   ├── AGENT_MVP_SETUP.md         # Setup instructions
        │   ├── AGENT_MVP_WALKTHROUGH.md   # How it works
        │   ├── AGENT_MVP_COMPLETE.md      # Full documentation
        │   ├── AGENT_MVP_SUMMARY.md       # Quick summary
        │   ├── AGENT_MVP_FILES.md         # File reference
        │   ├── README.md                  # from agent_mvp
        │   ├── agent_mvp_summary.md
        │   └── demo_runbook.md
        |
        ├── orchestration/
        │   ├── AGENT_INTEGRATION_VERIFICATION.md
        │   ├── QUICK_REFERENCE.md              # Quick lookup
        │   ├── ROUTE_TO_AGENT_EVENT_MAPPING.md # Routes guide
        │   ├── VERIFICATION_GUIDE.md           # Verification steps
        │   └── VERIFICATION_SUMMARY.md         # Verification results
        │
        |── api/                            # ✅ EXISTING Observability
        |   ├── backend-setup.md            # How to setup backend
        |   ├── api-endpoints.md            # API documentation
        |   ├── api-examples.md             # API usage examples
        |   ├── database-erd.md             # Database schema
        |   └── developer-roadmap.md        # Development plan
        |
        ├── opik/                       
        │   └──  OPIK_TRACING.md            # Observability
        |
        ├── refactoring/                       
        │   └──  
        │   
        └── tests/
              └── TEST_COVERAGE_SUMMARY.md   # Test documentation

.private/docs/
├── PRUPOSED_REFACTORING_PLAN.md    # Original plan
├── NEW_STRUCTURE_PLAN.md           # 🆕 THIS DOCUMENT
├── MIGRATION_GUIDE.md              # 🆕 Step-by-step migration
└── IMPLEMENTATION_CHECKLIST.md     # 🆕 Implementation tracker
```

---

## Part 2: Comprehensive API Endpoints Overview

### Authentication Endpoints (`/api/auth`)
```
POST   /api/auth/register          → auth.register()
POST   /api/auth/login             → auth.login()
POST   /api/auth/refresh           → auth.refresh_token()
POST   /api/auth/logout            → auth.logout()
```

### User Endpoints (`/api/users`)
```
GET    /api/users/profile          → users.get_profile()
PUT    /api/users/profile          → users.update_profile()
POST   /api/users/state/check-in   → users.daily_checkin()  [Triggers CHECKIN event]
GET    /api/users/preferences      → users.get_preferences()
```

### Task Endpoints (`/api/tasks`)
```
GET    /api/tasks                  → tasks.list_tasks()
POST   /api/tasks                  → tasks.create_task()
GET    /api/tasks/{id}             → tasks.get_task()
PUT    /api/tasks/{id}             → tasks.update_task()
DELETE /api/tasks/{id}             → tasks.delete_task()
POST   /api/tasks/{id}/start       → tasks.start_task()     [Triggers DO_ACTION:start]
POST   /api/tasks/{id}/pause       → tasks.pause_task()     [Triggers DO_ACTION:pause]
POST   /api/tasks/{id}/complete    → tasks.complete_task()  [Triggers DO_ACTION:complete]
POST   /api/tasks/{id}/intervention→ tasks.intervention()   [Triggers DO_ACTION:stuck]
POST   /api/tasks/{id}/break       → tasks.take_break()
```

### Project Endpoints (`/api/projects`)
```
GET    /api/projects               → projects.list_projects()
POST   /api/projects               → projects.create_project()
GET    /api/projects/{id}          → projects.get_project()
PUT    /api/projects/{id}          → projects.update_project()
DELETE /api/projects/{id}          → projects.delete_project()
GET    /api/projects/{id}/tasks    → projects.get_tasks()
```

### Dashboard Endpoints (`/api/dashboard`)
```
GET    /api/dashboard/summary      → dashboard.get_summary()     [Triggers APP_OPEN]
GET    /api/dashboard/today-tasks  → dashboard.get_today_tasks()
POST   /api/dashboard/done-for-today → dashboard.end_day()       [Triggers DAY_END]
```

### Agent MVP Endpoints (`/api/agent-mvp`)
```
POST   /api/agent-mvp/smoke        → agent_mvp.smoke_test()
POST   /api/agent-mvp/next-do      → agent_mvp.next_do()         [Orchestrator: DO_NEXT]
POST   /api/agent-mvp/app-open     → agent_mvp.app_open()        [Orchestrator: APP_OPEN]
POST   /api/agent-mvp/checkin      → agent_mvp.checkin()         [Orchestrator: CHECKIN]
POST   /api/agent-mvp/do-action    → agent_mvp.do_action()       [Orchestrator: DO_ACTION]
POST   /api/agent-mvp/day-end      → agent_mvp.day_end()         [Orchestrator: DAY_END]
POST   /api/agent-mvp/insights     → agent_mvp.get_insights()
POST   /api/agent-mvp/simulate     → agent_mvp.simulate()        [No auth, local testing]
```

### Analytics Endpoints (`/api/analytics`)
```
GET    /api/analytics/summary      → analytics.get_summary()
GET    /api/analytics/completion   → analytics.get_completion_rate()
GET    /api/analytics/focus        → analytics.get_focus_stats()
```

### Notifications Endpoints (`/api/notifications`)
```
GET    /api/notifications          → notifications.list()
POST   /api/notifications/{id}/read → notifications.mark_read()
DELETE /api/notifications/{id}     → notifications.delete()
```

---

## Part 3: Enhanced Contracts & Data Flow

### GraphState (Enhanced)

**File**: `backend/orchestrator/contracts.py`

```python
class GraphState(BaseModel):
    """LangGraph state with mood & energy tracking."""
    model_config = {"arbitrary_types_allowed": True}

    # Core
    user_id: str
    current_event: Optional[Any] = None

    # User state (NEW)
    mood: Optional[str] = None           # e.g., "motivated", "tired", "frustrated"
    energy_level: int = Field(5, ge=1, le=10)

    # Task selection
    candidates: List[TaskCandidate] = Field(default_factory=list)
    constraints: Optional[SelectionConstraints] = None
    active_do: Optional[Dict[str, Any]] = None

    # Agent outputs
    coach_message: Optional[CoachOutput] = None
    motivation_message: Optional[MotivationMessage] = None
    stuck_analysis: Optional[StuckAnalysis] = None
    microtasks: Optional[List[Microtask]] = None
    day_insights: Optional[List[Insight]] = None

    # Intervention tracking (NEW)
    intervention_logs: List[Dict[str, Any]] = Field(default_factory=list)

    # Opik tracing
    opik_trace_id: Optional[str] = None

    # Status
    success: bool = True
    error: Optional[str] = None
```

### Agent Input/Output Contracts

**File**: `backend/agents/contracts.py`

```python
class AgentInput(BaseModel):
    """Base input for all agents."""
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentOutput(BaseModel):
    """Base output for all agents."""
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
```

---

## Part 4: Agent Architecture

### LLM-Powered Agents Pattern

**File**: `backend/agents/llm_agents/base.py`

```python
from abc import ABC, abstractmethod
from opik import track

class BaseLLMAgent(ABC):
    """Base class for LLM-powered agents."""

    def __init__(self, llm_service, opik_tracker=None):
        self.llm_service = llm_service
        self.opik_tracker = opik_tracker

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process input through LLM and return structured output."""
        pass
```

### Deterministic Agents Pattern

**File**: `backend/agents/deterministic_agents/base.py`

```python
from abc import ABC, abstractmethod

class BaseDeterministicAgent(ABC):
    """Base class for deterministic agents (pure logic, no LLM)."""

    @abstractmethod
    def process(self, input: AgentInput) -> AgentOutput:
        """Process input with deterministic logic."""
        pass
```

---

## Part 5: Opik Observability Framework

### Key Improvements

#### 1. **@track Decorator on All LangGraph Nodes**

```python
from opik import track

class RaimonOrchestrator:
    @track(name="orchestrator_handle_app_open")
    def _handle_app_open(self, state: GraphState) -> GraphState:
        """Handle APP_OPEN event."""
        # Implementation
```

#### 2. **OpikManager Singleton**

**File**: `backend/opik_utils/client.py`

```python
class OpikManager:
    """Singleton for centralized Opik logging."""
    _instance = None

    def __init__(self):
        self.client = opik.Opik(api_key=os.getenv("OPIK_API_KEY"))
        self.project = self.client.get_project(os.getenv("OPIK_PROJECT_NAME"))

    @staticmethod
    def get_instance():
        if OpikManager._instance is None:
            OpikManager._instance = OpikManager()
        return OpikManager._instance
```

#### 3. **Custom Evaluators**

**File**: `backend/opik_utils/evaluators/`

```
Hallucination Evaluator
  → Detect factually incorrect LLM outputs
  → Check against user's actual task data

Motivation Rubric Evaluator
  → Grade motivation messages (1-5 stars)
  → Check personalization level
  → Verify tone alignment

Selection Accuracy Evaluator
  → Compare LLM selection vs. deterministic ranking
  → Track convergence over time

Stuck Detection Evaluator
  → Evaluate stuck detection accuracy
  → Compare vs. user's actual feedback
```

#### 4. **Custom Metrics**

**File**: `backend/opik_utils/metrics/`

```
Agent Performance Metrics
  ✓ Execution time per agent
  ✓ Success rate
  ✓ Error recovery rate

Task Selection Metrics
  ✓ Selection accuracy (user satisfaction)
  ✓ Alternative suggestion quality
  ✓ Energy level alignment

User Engagement Metrics
  ✓ App open frequency
  ✓ Check-in completion rate
  ✓ Task completion rate
  ✓ Average session duration
```

#### 5. **Opik Dashboard Queries**

**File**: `backend/opik_utils/dashboards/opik_queries.py`

```python
# Pre-built queries for common analyses
QUERIES = {
    "agent_latency": "SELECT agent_name, AVG(duration) FROM traces",
    "error_rate": "SELECT agent_name, COUNT(*) WHERE status='error'",
    "selection_convergence": "SELECT * FROM metrics WHERE metric='selection_accuracy'",
}
```

---

## Part 6: Refactoring Roadmap

### Phase 1: Preparation (Week 1)
- [ ] Create new directory structures (agents/, orchestrator/, etc.)
- [ ] Define comprehensive Pydantic contracts
- [ ] Set up base classes for agents
- [ ] Enhance Opik evaluators and metrics

### Phase 2: Agent Consolidation (Weeks 2-3)
- [ ] Move LLM agents to `backend/agents/llm_agents/`
- [ ] Move deterministic agents to `backend/agents/deterministic_agents/`
- [ ] Create agent factory with dependency injection
- [ ] Add @track decorators to all agents

### Phase 3: Orchestrator Enhancement (Week 4)
- [ ] Refactor orchestrator to use new agent factory
- [ ] Update GraphState with mood/energy/intervention tracking
- [ ] Implement enhanced edge routing
- [ ] Add comprehensive error handling & fallbacks

### Phase 4: Opik Optimization (Week 5)
- [ ] Implement evaluators
- [ ] Set up custom metrics
- [ ] Create Opik dashboard queries
- [ ] Add performance benchmarking

### Phase 5: Testing & Documentation (Week 6)
- [ ] Unit tests for all agents
- [ ] Integration tests for orchestrator
- [ ] Opik tracing verification
- [ ] Update API documentation
- [ ] Create migration guide

---

## Part 7: Backward Compatibility & Migration

### Breaking Changes (Minimal)
- GraphState structure changes (additive only, no removal)
- Agent I/O format (new Pydantic contracts)
- Opik trace names (fully documented)

### Non-Breaking Changes
- All existing routers continue to work
- All existing endpoints work unchanged
- Database schema remains compatible
- Old agents can co-exist during transition

### Migration Path
1. Deploy new structures alongside old code
2. Update routers to use new agents gradually
3. Run both systems in parallel for validation
4. Deprecate old code after 1-2 sprints
5. Remove legacy code in major version bump

---

## Part 8: Testing Strategy

### Unit Tests
```
✓ Each agent: input validation, output contracts, error handling
✓ Each orchestrator node: state transitions, routing logic
✓ Opik decorators: trace capture verification
✓ Evaluators: accuracy metrics
```

### Integration Tests
```
✓ Full orchestrator flow (APP_OPEN → DO_NEXT → DO_ACTION → DAY_END)
✓ Agent factory with dependency injection
✓ Opik middleware integration
✓ Error recovery & fallbacks
```

### End-to-End Tests
```
✓ Smoke tests for all endpoints
✓ User journey tests (realistic flows)
✓ Performance benchmarks
✓ Opik trace validation
```

---

## Part 9: Opik Extensions & Recommendations

### Recommended Custom Implementations

#### 1. **Hallucination Detector**
- Monitor LLM outputs for factual inconsistencies
- Compare against user's actual task database
- Flag suspicious outputs with confidence scores

#### 2. **Energy/Mood Analyzer**
- Track user energy patterns over time
- Correlate mood with task completion rates
- Recommend optimal task times based on history

#### 3. **Selection Confidence Score**
- Compare LLM selection vs. deterministic ranking
- High convergence = high confidence in selection
- Low convergence = fallback to deterministic

#### 4. **Agent Performance Dashboard**
- Real-time agent health metrics
- Error rate by agent type
- Latency trends
- User satisfaction correlation

#### 5. **Cost Analyzer**
- Track LLM API costs per agent
- Identify cost optimization opportunities
- Compare LLM vs. deterministic agent ROI

---

## Part 10: Key Design Principles

### 1. **Golden Standard Pattern**
```
agent_mvp architecture = {
  - LangGraph for orchestration
  - Pydantic for strict contracts
  - @track for observability
  - Error handling with fallbacks
}

All new code follows this pattern exactly.
```

### 2. **Separation of Concerns**
```
- LLM Agents: Call LLM, handle uncertainty
- Deterministic: Pure logic, guaranteed correctness
- Orchestrator: Coordinate and validate
- Services: Business logic, DB access
- Routers: HTTP interface
```

### 3. **Contract-First Development**
```
1. Define Pydantic models first
2. Implement agents to contract
3. Add tests that validate contracts
4. Update Opik evaluators for contract validation
```

### 4. **Error Handling Strategy**
```
- Primary: LLM-based agent
- Fallback 1: Deterministic agent
- Fallback 2: Previous user behavior
- Fallback 3: Safe defaults
```

### 5. **Testability Requirements**
```
- All agents: isolated, mockable
- All nodes: pure functions (except storage)
- All contracts: pydantic validated
- All flows: deterministically reproducible
```

---

## Part 11: Success Metrics

### Code Quality
- [ ] 100% of agents conform to base class pattern
- [ ] 100% of Pydantic contracts validated at boundaries
- [ ] 90%+ test coverage for orchestrator
- [ ] Zero breaking changes to existing APIs

### Observability
- [ ] All LangGraph nodes traced with @track
- [ ] All agent executions logged in Opik
- [ ] Evaluators report on 5+ quality metrics
- [ ] Custom dashboard shows real-time agent health

### Performance
- [ ] Agent execution < 2s p95 latency
- [ ] Orchestrator < 3s p95 latency
- [ ] LLM fallback kicks in < 1s on errors
- [ ] Cache hit rate > 80% for user profiles

### User Impact
- [ ] No regression in task selection accuracy
- [ ] Improved coaching message personalization
- [ ] Better stuck detection (fewer false positives)
- [ ] Higher user satisfaction with recommendations

---

## Appendix: File Migration Matrix

| Current Location | New Location | Type | Status |
|---|---|---|---|
| `agent_mvp/do_selector.py` | `agents/llm_agents/do_selector.py` | LLM Agent | Migrate |
| `agent_mvp/coach.py` | `agents/llm_agents/coach.py` | LLM Agent | Migrate |
| `agent_mvp/user_profile_agent.py` | `agents/deterministic_agents/user_profile_agent.py` | Deterministic | Migrate |
| `agent_mvp/priority_engine_agent.py` | `agents/deterministic_agents/priority_engine_agent.py` | Deterministic | Migrate |
| `agent_mvp/contracts.py` | `agents/contracts.py` + `orchestrator/contracts.py` | Contracts | Split |
| `agent_mvp/orchestrator.py` | `orchestrator/orchestrator.py` | Core | Move |
| `agent_mvp/graph.py` | `orchestrator/graph.py` | Core | Move |
| `agent_mvp/storage.py` | `services/storage_service.py` | Service | Relocate |

---

**Document Version**: 1.0
**Last Updated**: February 5, 2025
**Next Review**: After Phase 2 Completion
