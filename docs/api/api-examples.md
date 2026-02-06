# API Request/Response Examples

## Authentication

### POST /api/auth/signup
**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "name": "John Doe",
      "onboarding_completed": false
    },
    "token": "jwt-token-here",
    "refresh_token": "refresh-token-here"
  }
}
```

### POST /api/auth/login
**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "name": "John Doe",
      "onboarding_completed": true,
      "last_login_at": "2026-01-21T15:30:00Z"
    },
    "token": "jwt-token-here",
    "refresh_token": "refresh-token-here"
  }
}
```

## Onboarding

### PUT /api/users/onboarding
**Request:**
```json
{
  "step": 1,
  "data": {
    "goals": [
      "Improve focus",
      "Complete projects on time",
      "Better work-life balance"
    ],
    "work_style": {
      "preferred_work_hours": "9am-5pm",
      "break_preference": "pomodoro",
      "energy_pattern": "morning_person"
    },
    "energy_patterns": {
      "peak_hours": ["9-11", "14-16"],
      "low_energy_hours": ["13-14"]
    }
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "onboarding_step": 1,
    "completed": false,
    "next_step": "create_first_project"
  }
}
```

## Projects

### POST /api/projects
**Request:**
```json
{
  "name": "Website Redesign",
  "description": "Complete redesign of company website",
  "priority": 1,
  "color": "#FF6B6B",
  "icon": "🎨",
  "start_date": "2026-01-22",
  "target_end_date": "2026-03-15",
  "details": {
    "goals": [
      "Improve user experience",
      "Increase conversion rate by 20%",
      "Mobile-first design"
    ],
    "stakeholders": [
      {
        "name": "Sarah Johnson",
        "role": "Product Manager",
        "email": "sarah@company.com"
      }
    ],
    "resources": [
      {
        "type": "document",
        "title": "Design Brief",
        "url": "https://docs.example.com/brief"
      }
    ]
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "proj-uuid-here",
      "user_id": "user-uuid",
      "name": "Website Redesign",
      "description": "Complete redesign of company website",
      "status": "active",
      "priority": 1,
      "color": "#FF6B6B",
      "icon": "🎨",
      "start_date": "2026-01-22",
      "target_end_date": "2026-03-15",
      "created_at": "2026-01-21T15:30:00Z"
    }
  }
}
```

### GET /api/projects
**Response (200):**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "proj-1",
        "name": "Website Redesign",
        "status": "active",
        "priority": 1,
        "progress": 45,
        "task_count": 12,
        "completed_tasks": 5,
        "target_end_date": "2026-03-15"
      },
      {
        "id": "proj-2",
        "name": "Mobile App",
        "status": "active",
        "priority": 2,
        "progress": 20,
        "task_count": 8,
        "completed_tasks": 2,
        "target_end_date": "2026-04-30"
      }
    ],
    "total": 2
  }
}
```

## Tasks

### POST /api/projects/:projectId/tasks
**Request:**
```json
{
  "title": "Design homepage mockup",
  "description": "Create high-fidelity mockup for new homepage",
  "priority": "high",
  "estimated_duration": 120,
  "deadline": "2026-01-25T17:00:00Z",
  "tags": ["design", "mockup", "homepage"]
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": "task-uuid",
      "project_id": "proj-uuid",
      "title": "Design homepage mockup",
      "description": "Create high-fidelity mockup for new homepage",
      "status": "todo",
      "priority": "high",
      "estimated_duration": 120,
      "deadline": "2026-01-25T17:00:00Z",
      "tags": ["design", "mockup", "homepage"],
      "created_at": "2026-01-21T15:30:00Z"
    }
  }
}
```

### POST /api/tasks/:id/start
**Request:**
```json
{
  "energy_level": 8,
  "notes": "Feeling focused and ready to work"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": "task-uuid",
      "status": "in_progress",
      "started_at": "2026-01-21T15:30:00Z"
    },
    "session": {
      "id": "session-uuid",
      "start_time": "2026-01-21T15:30:00Z",
      "energy_before": 8
    }
  }
}
```

## Daily Check-in

### POST /api/users/state/check-in
**Request:**
```json
{
  "energy_level": 7,
  "mood": "focused",
  "sleep_quality": 8,
  "blockers": ["Need design feedback from team"],
  "focus_areas": ["Complete homepage mockup", "Review API documentation"]
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "check_in": {
      "id": "checkin-uuid",
      "date": "2026-01-21",
      "energy_level": 7,
      "mood": "focused",
      "sleep_quality": 8
    },
    "greeting": "Good morning! With your energy at 7/10, you're ready for focused work.",
    "recommendations": {
      "suggested_tasks": [
        {
          "id": "task-1",
          "title": "Design homepage mockup",
          "reason": "High priority and matches your current energy level"
        }
      ],
      "suggested_break_time": "11:30",
      "working_style_today": "deep_work_blocks"
    }
  }
}
```

## AI Agent Insights

### POST /api/agents/priority-engine/analyze
**Request:**
```json
{
  "project_id": "proj-uuid",
  "context": {
    "current_energy": 7,
    "time_available": 180,
    "deadline_pressure": "medium"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "prioritized_tasks": [
      {
        "task_id": "task-1",
        "title": "Design homepage mockup",
        "priority_score": 0.95,
        "reasons": [
          "High impact on project timeline",
          "Matches current energy level",
          "Deadline approaching in 4 days"
        ],
        "estimated_completion": "2026-01-21T17:30:00Z"
      },
      {
        "task_id": "task-2",
        "title": "Review API documentation",
        "priority_score": 0.72,
        "reasons": [
          "Blocking other tasks",
          "Can be done with current energy"
        ]
      }
    ],
    "analysis": {
      "workload_balance": "optimal",
      "risk_factors": [],
      "optimization_suggestions": [
        "Consider batching similar design tasks tomorrow morning"
      ]
    }
  }
}
```

### GET /api/agents/time-learning/predictions
**Response (200):**
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "task_type": "design_mockup",
        "average_duration": 95,
        "confidence": 0.87,
        "factors": {
          "time_of_day_impact": 0.15,
          "complexity_impact": 0.30,
          "energy_impact": 0.20
        }
      }
    ],
    "performance_insights": {
      "peak_performance_times": ["9-11am", "2-4pm"],
      "task_completion_accuracy": 0.82,
      "improvement_over_time": 0.15
    }
  }
}
```

### POST /api/agents/stuck-pattern/detect
**Request:**
```json
{
  "task_id": "task-uuid",
  "session_data": {
    "duration": 45,
    "interruptions": 5,
    "progress_made": false
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "stuck_detected": true,
    "pattern": {
      "type": "frequent_context_switching",
      "severity": "medium",
      "description": "You've been interrupted 5 times in 45 minutes, preventing deep focus"
    },
    "suggestions": [
      {
        "action": "take_short_break",
        "reason": "Reset focus and reduce mental fatigue",
        "duration": 10
      },
      {
        "action": "enable_do_not_disturb",
        "reason": "Block interruptions for next focus session"
      },
      {
        "action": "break_task_into_smaller_parts",
        "reason": "Task might be too complex, try smaller chunks"
      }
    ]
  }
}
```

## Dashboard

### GET /api/dashboard/summary
**Response (200):**
```json
{
  "success": true,
  "data": {
    "greeting": "Good morning, User! You're on a 5-day streak 🔥",
    "current_state": {
      "status": "working",
      "current_task": {
        "id": "task-uuid",
        "title": "Design homepage mockup",
        "elapsed_time": 32,
        "estimated_remaining": 88
      }
    },
    "today": {
      "tasks_completed": 2,
      "tasks_remaining": 4,
      "focus_time": 95,
      "energy_level": 7,
      "next_break": "11:30"
    },
    "projects": [
      {
        "id": "proj-1",
        "name": "Website Redesign",
        "progress": 45,
        "status": "on_track"
      }
    ],
    "insights": [
      {
        "type": "productivity_tip",
        "message": "You're most productive in the morning. Schedule complex tasks before noon."
      }
    ],
    "streaks": {
      "daily_check_in": 5,
      "task_completion": 3
    }
  }
}
```

## Gamification

### GET /api/agents/motivation/streaks
**Response (200):**
```json
{
  "success": true,
  "data": {
    "active_streaks": [
      {
        "type": "daily_check_in",
        "current": 5,
        "longest": 12,
        "next_milestone": 7,
        "milestone_reward": "Week Warrior badge"
      },
      {
        "type": "task_completion",
        "current": 3,
        "longest": 8,
        "next_milestone": 5
      }
    ],
    "recent_achievements": [
      {
        "id": "achievement-1",
        "name": "Early Bird",
        "description": "Completed morning check-in 5 days in a row",
        "earned_at": "2026-01-21T09:00:00Z",
        "points": 50
      }
    ]
  }
}
```

## Analytics

### GET /api/analytics/productivity-metrics
**Query Params:** ?start_date=2026-01-15&end_date=2026-01-21

**Response (200):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2026-01-15",
      "end": "2026-01-21"
    },
    "metrics": {
      "total_focus_time": 1425,
      "tasks_completed": 18,
      "average_task_duration": 79,
      "productivity_score": 0.84,
      "best_day": {
        "date": "2026-01-20",
        "tasks_completed": 5,
        "focus_time": 240
      },
      "peak_hours": ["9-11", "14-16"]
    },
    "trends": {
      "focus_time_trend": 0.12,
      "task_completion_trend": 0.08,
      "energy_variance": 1.5
    },
    "breakdown_by_day": [
      {
        "date": "2026-01-15",
        "focus_time": 180,
        "tasks_completed": 3,
        "energy_average": 7
      }
    ]
  }
}
```
