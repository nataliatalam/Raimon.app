# API Endpoints Documentation

## Authentication & User Management

### Auth Endpoints
```
POST   /api/auth/signup
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh-token
POST   /api/auth/verify-code
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
```

### User Endpoints
```
GET    /api/users/profile
PUT    /api/users/profile
PATCH  /api/users/preferences
GET    /api/users/onboarding-status
PUT    /api/users/onboarding
```

## Project Management

### Project Endpoints
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

### Project Details Endpoints
```
PUT    /api/projects/:id/profile
PUT    /api/projects/:id/goals
PUT    /api/projects/:id/resources
PUT    /api/projects/:id/timeline
PUT    /api/projects/:id/stakeholders
```

## Task Management

### Task Endpoints
```
GET    /api/projects/:projectId/tasks
POST   /api/projects/:projectId/tasks
GET    /api/tasks/:id
PUT    /api/tasks/:id
DELETE /api/tasks/:id
PATCH  /api/tasks/:id/status
PATCH  /api/tasks/:id/priority
```

### Task Actions
```
POST   /api/tasks/:id/start
POST   /api/tasks/:id/pause
POST   /api/tasks/:id/complete
POST   /api/tasks/:id/break
POST   /api/tasks/:id/intervention
```

## State & Progress Tracking

### State Endpoints
```
GET    /api/users/current-state
POST   /api/users/state/check-in
GET    /api/users/state/history
POST   /api/users/state/energy-level
POST   /api/users/state/mood
POST   /api/users/state/blockers
```

### Progress Endpoints
```
GET    /api/projects/:id/progress
GET    /api/tasks/:id/progress
GET    /api/users/achievements
GET    /api/users/streaks
POST   /api/users/microtasks/complete
```

## AI Agents Integration

### User Profile Agent
```
POST   /api/agents/user-profile/analyze
GET    /api/agents/user-profile/insights
POST   /api/agents/user-profile/update-preferences
```

### Priority Engine
```
POST   /api/agents/priority-engine/analyze
GET    /api/agents/priority-engine/recommendations
POST   /api/agents/priority-engine/rerank-tasks
```

### Daily State Adapter
```
POST   /api/agents/state-adapter/check-in
GET    /api/agents/state-adapter/energy-assessment
GET    /api/agents/state-adapter/task-recommendations
```

### Time Learning Agent
```
POST   /api/agents/time-learning/track
GET    /api/agents/time-learning/predictions
GET    /api/agents/time-learning/performance-insights
```

### Stuck Pattern Agent
```
POST   /api/agents/stuck-pattern/detect
GET    /api/agents/stuck-pattern/analysis
POST   /api/agents/stuck-pattern/suggest-solutions
```

### Project Insight Engine
```
GET    /api/agents/project-insight/:projectId/completion-prediction
GET    /api/agents/project-insight/:projectId/risk-analysis
GET    /api/agents/project-insight/:projectId/optimization-suggestions
```

### Streak & Motivation
```
GET    /api/agents/motivation/streaks
GET    /api/agents/motivation/badges
POST   /api/agents/motivation/celebrate
GET    /api/agents/motivation/challenges
```

### Context Continuity
```
GET    /api/agents/context/session-summary
POST   /api/agents/context/save-state
GET    /api/agents/context/next-steps
GET    /api/agents/context/unfinished-work
```

## Dashboard & Analytics

### Dashboard Endpoints
```
GET    /api/dashboard/summary
GET    /api/dashboard/current-task
GET    /api/dashboard/today-tasks
GET    /api/dashboard/greetings
```

### Analytics Endpoints
```
GET    /api/analytics/time-tracking
GET    /api/analytics/productivity-metrics
GET    /api/analytics/project-performance
GET    /api/analytics/goal-progress
```

## Notifications & Reminders

### Notification Endpoints
```
GET    /api/notifications
PUT    /api/notifications/:id/read
PUT    /api/notifications/read-all
DELETE /api/notifications/:id
```

### Reminder Endpoints
```
GET    /api/reminders
POST   /api/reminders
PUT    /api/reminders/:id
DELETE /api/reminders/:id
```

## Webhooks & Integrations

### Integration Endpoints
```
GET    /api/integrations
POST   /api/integrations/:type/connect
DELETE /api/integrations/:type/disconnect
POST   /api/integrations/:type/sync
```

## Real-time & Websocket Events

### WebSocket Events
```
connect: /ws/user/:userId
events:
  - task.started
  - task.completed
  - task.updated
  - state.changed
  - break.started
  - break.ended
  - agent.insight
  - streak.updated
  - notification.new
```
