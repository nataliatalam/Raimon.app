# Backend Setup Guide

This guide covers setting up and running the FastAPI backend with Supabase authentication.

## Prerequisites

- Python 3.10+
- pip or pipenv
- Supabase account and project

## Installation

### 1. Create the backend directory and virtual environment

```bash
cd /path/to/Raimon.app
mkdir -p backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn python-dotenv supabase pydantic python-jose[cryptography] passlib[bcrypt]
```

Or use the requirements.txt:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Running the Server

### Development Mode

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

Once running, the API is available at `http://localhost:8000`.

### Interactive Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Authentication Endpoints

### POST /api/auth/signup

Register a new user account.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securePassword123",
    "name": "John Doe"
  }'
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

Authenticate and receive tokens.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securePassword123"
  }'
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

### POST /api/auth/logout

Invalidate the current session.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <your-token>"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

### POST /api/auth/refresh-token

Refresh the access token.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "new-jwt-token",
    "refresh_token": "new-refresh-token"
  }
}
```

### POST /api/auth/forgot-password

Request a password reset email.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

### POST /api/auth/reset-password

Reset password with token.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset-token-from-email",
    "password": "newSecurePassword123"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Password reset successful"
}
```

---

## User Endpoints

### GET /api/users/profile

Get the current user's profile.

**Request:**
```bash
curl -X GET http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer <your-token>"
```

### PUT /api/users/profile

Update the current user's profile.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "avatar_url": "https://example.com/avatar.png"
  }'
```

---

## Project Endpoints

### GET /api/projects

List all projects for the authenticated user.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer <your-token>"
```

### POST /api/projects

Create a new project.

**Request:**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign",
    "description": "Complete redesign of company website",
    "priority": 1,
    "color": "#FF6B6B",
    "icon": "palette",
    "start_date": "2026-01-22",
    "target_end_date": "2026-03-15"
  }'
```

### GET /api/projects/{id}

Get a specific project.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects/{project_id} \
  -H "Authorization: Bearer <your-token>"
```

### PUT /api/projects/{id}

Update a project.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/projects/{project_id} \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name",
    "status": "active"
  }'
```

### DELETE /api/projects/{id}

Delete a project.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/projects/{project_id} \
  -H "Authorization: Bearer <your-token>"
```

---

## Task Endpoints

### GET /api/projects/{projectId}/tasks

List all tasks for a project.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects/{project_id}/tasks \
  -H "Authorization: Bearer <your-token>"
```

### POST /api/projects/{projectId}/tasks

Create a new task.

**Request:**
```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/tasks \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design homepage mockup",
    "description": "Create high-fidelity mockup for new homepage",
    "priority": "high",
    "estimated_duration": 120,
    "deadline": "2026-01-25T17:00:00Z",
    "tags": ["design", "mockup", "homepage"]
  }'
```

### POST /api/tasks/{id}/start

Start working on a task.

**Request:**
```bash
curl -X POST http://localhost:8000/api/tasks/{task_id}/start \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "energy_level": 8,
    "notes": "Feeling focused and ready to work"
  }'
```

### POST /api/tasks/{id}/complete

Mark a task as complete.

**Request:**
```bash
curl -X POST http://localhost:8000/api/tasks/{task_id}/complete \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "energy_after": 6,
    "notes": "Completed successfully"
  }'
```

---

## State & Check-in Endpoints

### POST /api/users/state/check-in

Daily check-in to record energy and mood.

**Request:**
```bash
curl -X POST http://localhost:8000/api/users/state/check-in \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "energy_level": 7,
    "mood": "focused",
    "sleep_quality": 8,
    "blockers": ["Need design feedback from team"],
    "focus_areas": ["Complete homepage mockup"]
  }'
```

### GET /api/users/current-state

Get the user's current state.

**Request:**
```bash
curl -X GET http://localhost:8000/api/users/current-state \
  -H "Authorization: Bearer <your-token>"
```

---

## Dashboard Endpoints

### GET /api/dashboard/summary

Get the dashboard summary.

**Request:**
```bash
curl -X GET http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer <your-token>"
```

### GET /api/dashboard/today-tasks

Get today's tasks.

**Request:**
```bash
curl -X GET http://localhost:8000/api/dashboard/today-tasks \
  -H "Authorization: Bearer <your-token>"
```

---

## Supabase Database Setup

### Required Tables

Run these SQL commands in your Supabase SQL editor:

```sql
-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- User preferences table
CREATE TABLE public.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    energy_patterns JSONB,
    work_style JSONB,
    notification_settings JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects table
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    priority INTEGER DEFAULT 0,
    color TEXT,
    icon TEXT,
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks table
CREATE TABLE public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES public.tasks(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    estimated_duration INTEGER,
    actual_duration INTEGER,
    deadline TIMESTAMPTZ,
    tags TEXT[],
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own data" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own preferences" ON public.user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own projects" ON public.projects
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own tasks" ON public.tasks
    FOR ALL USING (auth.uid() = user_id);
```

### Supabase Triggers

```sql
-- Auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'name');

    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON public.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Testing with HTTPie (Alternative to curl)

```bash
# Install HTTPie
pip install httpie

# Signup
http POST localhost:8000/api/auth/signup email=user@example.com password=secret123 name="John Doe"

# Login
http POST localhost:8000/api/auth/login email=user@example.com password=secret123

# Get profile (with token)
http GET localhost:8000/api/users/profile "Authorization: Bearer <token>"
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {}
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `INTERNAL_ERROR` | 500 | Server error |
