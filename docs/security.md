# Security Audit Report - Raimon Backend API

**Date:** January 22, 2026
**Scope:** Full backend codebase analysis
**Severity Levels:** CRITICAL | HIGH | MEDIUM | LOW | INFO

---

## Executive Summary

The Raimon backend is a FastAPI application using Supabase (PostgreSQL + Auth) with JWT authentication. This report covers security vulnerabilities, data leak risks, and database injection analysis across all modules.

**Total findings:** 28
- Critical: 5
- High: 8
- Medium: 10
- Low: 3
- Informational: 2

---

## CRITICAL Findings

### 1. No Password Strength Validation
**File:** `models/auth.py:8-9, 26`
**Risk:** Weak passwords, brute force

```python
class SignupRequest(BaseModel):
    password: str  # No min_length, no complexity rules

class ResetPasswordRequest(BaseModel):
    password: str  # Same issue
```

Users can set passwords like `"1"` or `"a"`. No minimum length, no uppercase/number/special character requirements.

**Remediation:**
```python
password: str = Field(..., min_length=8, max_length=128)
# Add a validator for complexity requirements
```

---

### 2. No Rate Limiting on Authentication Endpoints
**File:** `routers/auth.py` (all endpoints)
**Risk:** Brute force attacks, credential stuffing, account enumeration

No rate limiting exists on `/api/auth/login`, `/api/auth/signup`, `/api/auth/forgot-password`, or `/api/auth/verify-code`. An attacker can:
- Brute force passwords at unlimited speed
- Enumerate valid emails via signup
- Flood OTP verification attempts

**Remediation:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
```

---

### 3. Debug Mode Enabled by Default in Production
**File:** `core/config.py:19`
**Risk:** Information disclosure, verbose error output

```python
debug: bool = True  # Default should be False
```

If `.env` doesn't explicitly set `DEBUG=false`, the application runs in debug mode in production, potentially exposing stack traces and internal state.

**Remediation:**
```python
debug: bool = False  # Safe default
app_env: str = "production"  # Safe default
```

---

### 4. Internal Error Messages Leak Database Schema
**File:** `routers/projects.py` (all try/except blocks)
**Risk:** Information disclosure

```python
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to fetch project: {str(e)}",  # LEAKS INTERNAL ERROR
    )
```

`str(e)` from Supabase errors can contain:
- Table names and column names
- SQL error details
- Connection strings
- Internal API URLs

**Remediation:**
```python
except Exception as e:
    logger.error(f"Failed to fetch project: {str(e)}")  # Log internally
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch project",  # Generic message to client
    )
```

---

### 5. JWT Tokens Not Invalidated on Logout
**File:** `routers/auth.py:132-144`, `core/security.py`
**Risk:** Session hijacking after logout

```python
@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    supabase.auth.sign_out()  # Only signs out of Supabase
    return AuthResponse(success=True, message="Successfully logged out")
```

The JWT access and refresh tokens remain valid after logout. An attacker with a stolen token can continue making authenticated requests until the token expires (30 minutes for access, 7 days for refresh).

**Remediation:** Implement a token blacklist:
- Store invalidated tokens in Redis/database
- Check blacklist in `verify_token()`
- Or use short-lived tokens (5 min) with token rotation

---

## HIGH Findings

### 6. `.single()` Throws Unhandled Exceptions
**Files:** `routers/tasks.py:28-34,48-54`, `routers/notifications.py:71-73,129-131`, `routers/dashboard.py:74,349-350`, `routers/integrations.py:143-145,199-202,234-238,295-298`, `routers/next_do.py:136-140`
**Risk:** 500 Internal Server Error, information leakage

The Supabase `.single()` method throws an exception when 0 or 2+ rows are found. This was the original cause of the project GET failure. Many routers still use it without try/except.

**Remediation:** Replace `.single()` with `.execute()` and check `response.data`:
```python
response = supabase.table("x").select("*").eq("id", id).execute()
if not response.data:
    raise HTTPException(404, "Not found")
return response.data[0]
```

---

### 7. No Input Sanitization (XSS Risk)
**Files:** All models accepting string fields
**Risk:** Stored XSS

Fields like `name`, `description`, `notes`, `reason`, `message` accept arbitrary text including HTML/JavaScript:

```json
{"name": "<script>alert('xss')</script>"}
{"description": "<img src=x onerror=steal(document.cookie)>"}
```

If the frontend renders these without escaping, stored XSS is possible.

**Remediation:**
```python
import bleach

@field_validator('name', 'description')
@classmethod
def sanitize(cls, v):
    if v:
        return bleach.clean(v, tags=[], strip=True)
    return v
```

---

### 8. Refresh Tokens Cannot Be Revoked
**File:** `routers/auth.py:147-178`, `core/security.py`
**Risk:** Persistent unauthorized access

There is no token revocation mechanism. If a refresh token is compromised, it remains valid for 7 days with no way to invalidate it.

**Remediation:**
- Store refresh tokens in database with `is_revoked` flag
- Add `/api/auth/revoke` endpoint
- Check revocation status during refresh

---

### 9. Service Role Key Exposed in Application Memory
**File:** `core/supabase.py:7-8`
**Risk:** Full database bypass if memory is dumped

```python
supabase_admin: Client = create_client(
    settings.supabase_url, settings.supabase_service_role_key
)
```

The service role key bypasses ALL Row Level Security. While `get_supabase_admin()` isn't used in routes currently, it's importable by any module. If accidentally used in a user-facing endpoint, it grants unrestricted database access.

**Remediation:**
- Remove admin client from regular application code
- Only initialize admin client in background jobs/admin scripts
- Or add a middleware check that prevents admin client usage in request context

---

### 10. No UUID Validation on Path Parameters
**Files:** All routers with `{project_id}`, `{task_id}`, `{notification_id}`
**Risk:** Database errors, potential injection

```python
@router.get("/{project_id}")
async def get_project(project_id: str, ...):  # Accepts any string
```

Path parameters accept any string, not just UUIDs. Malformed IDs like `'; DROP TABLE projects; --` reach the database query.

**Note:** The Supabase SDK uses parameterized queries via PostgREST, so SQL injection isn't directly possible, but malformed input causes unnecessary database errors and error message leakage.

**Remediation:**
```python
from uuid import UUID

@router.get("/{project_id}")
async def get_project(project_id: UUID, ...):  # FastAPI validates UUID format
```

---

### 11. User Profile Returns All Columns
**File:** `core/security.py:71`
**Risk:** Sensitive data exposure

```python
response = supabase.table("users").select("*").eq("id", user_id).single().execute()
```

`select("*")` returns ALL columns from the users table. This object is then passed to `current_user` and exposed in `/api/users/profile`. Could include:
- Internal metadata fields
- Password hashes (if stored)
- Service-level flags

**Remediation:**
```python
response = supabase.table("users").select(
    "id, email, name, avatar_url, onboarding_completed, onboarding_step, created_at"
).eq("id", user_id).single().execute()
```

---

### 12. Integration Credentials Stored as Plain JSON
**File:** `routers/integrations.py:23-25, 159-165`
**Risk:** Credential theft via database breach

```python
class ConnectRequest(BaseModel):
    credentials: Optional[dict] = None  # Stored as plain JSON

integration_data = {
    "settings": request.settings or {},  # May contain API keys
}
```

OAuth tokens, API keys, or other credentials passed during integration connection are stored as unencrypted JSON in the database.

**Remediation:**
- Encrypt credentials before storage using AES-256
- Use a secrets manager (AWS Secrets Manager, Vault)
- Never return full credentials in GET responses

---

### 13. Subtask Cascade Delete Without Ownership Check
**File:** `routers/tasks.py:287-299`
**Risk:** Authorization bypass

```python
for subtask in subtasks.data:
    supabase.table("tasks").delete().eq("id", subtask["id"]).execute()
```

When deleting a task, subtasks are deleted by ID without verifying the user owns them. If a subtask could somehow be shared (future feature), this is a privilege escalation.

**Remediation:**
```python
supabase.table("tasks").delete().eq("id", subtask["id"]).eq("user_id", user_id).execute()
```

---

## MEDIUM Findings

### 14. No Pagination on Multiple Endpoints
**Files:** `routers/projects.py:68-101`, `routers/tasks.py:99-145`, `routers/dashboard.py`
**Risk:** Denial of service, resource exhaustion

`list_projects`, `list_project_tasks`, and dashboard endpoints have no `limit` parameter. A user with thousands of projects/tasks could cause:
- High memory usage
- Slow response times
- Database connection pool exhaustion

**Remediation:** Add pagination to all list endpoints:
```python
limit: int = Query(default=50, le=100)
offset: int = Query(default=0, ge=0)
```

---

### 15. API Documentation Publicly Accessible
**File:** `main.py:25-26`
**Risk:** Information disclosure

```python
docs_url="/docs",
redoc_url="/redoc",
```

Swagger UI and ReDoc are accessible without authentication, exposing all endpoint schemas, request/response formats, and data structures to potential attackers.

**Remediation:**
```python
docs_url="/docs" if settings.debug else None,
redoc_url="/redoc" if settings.debug else None,
```

---

### 16. No HTTPS Enforcement
**File:** `main.py:92-96`
**Risk:** Man-in-the-middle attacks

The server runs on HTTP. JWT tokens, passwords, and user data are transmitted in plaintext.

**Remediation:**
- Deploy behind HTTPS reverse proxy (nginx, Caddy)
- Add HSTS headers
- Redirect HTTP to HTTPS

---

### 17. CORS Configuration Too Permissive for Production
**File:** `main.py:30-36`
**Risk:** Cross-origin attacks in production

```python
allow_origins=["http://localhost:3000", "http://localhost:8000"],
allow_methods=["*"],
allow_headers=["*"],
```

Only localhost origins are configured. In production, this either:
- Blocks the actual frontend (if deployed on a domain), or
- Gets changed to `["*"]` which allows any origin

**Remediation:**
```python
allow_origins=settings.allowed_origins.split(","),  # From env variable
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
allow_headers=["Authorization", "Content-Type"],
```

---

### 18. Unvalidated `Dict[str, Any]` Models
**Files:** `models/user.py:23-25,29-31,36`, `models/project.py:36,69`
**Risk:** Arbitrary data injection

```python
class OnboardingUpdate(BaseModel):
    data: Dict[str, Any]  # Accepts anything

class ProjectCreate(BaseModel):
    details: Optional[Dict[str, Any]] = None  # No schema validation
```

These fields accept any JSON structure, bypassing Pydantic's type safety. Attackers can inject:
- Extremely large nested objects (DoS)
- Unexpected field types that crash downstream code
- Malicious content stored in the database

**Remediation:** Define specific schemas instead of `Dict[str, Any]`.

---

### 19. No Audit Logging
**Risk:** Inability to detect breaches, no forensic trail

There is no logging of:
- Authentication attempts (success/failure)
- Data access patterns
- Administrative actions
- Token usage

**Remediation:** Add structured audit logging:
```python
logger.info("auth.login", extra={"user_id": user_id, "ip": request.client.host, "success": True})
```

---

### 20. No Request Body Size Limits
**Risk:** Denial of service

No `max_content_length` or body size validation. An attacker can send multi-GB request bodies to exhaust memory.

**Remediation:**
```python
from fastapi import Request

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > 1_000_000:  # 1MB
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
    return await call_next(request)
```

---

### 21. No `max_length` on Many Text Fields
**Files:** `models/task.py:26,67`, `models/user.py:18-19`, multiple models
**Risk:** Database storage exhaustion

```python
description: Optional[str] = None  # Unlimited length
notes: Optional[str] = None  # Unlimited length
reason: Optional[str] = None  # Unlimited length
```

**Remediation:**
```python
description: Optional[str] = Field(default=None, max_length=5000)
notes: Optional[str] = Field(default=None, max_length=2000)
```

---

### 22. `energy_level` Validation Inconsistency
**Files:** `routers/users.py:254`, `models/task.py:55,65`, `models/user.py:41`
**Risk:** Data integrity

`energy_level` is validated in some places (1-10) but not in `CheckInRequest`:
```python
class CheckInRequest(BaseModel):
    energy_level: int  # No ge=1, le=10 constraint
```

**Remediation:**
```python
energy_level: int = Field(..., ge=1, le=10)
```

---

### 23. Tags Array Has No Limits
**File:** `models/task.py:30,41`
**Risk:** Storage exhaustion, performance degradation

```python
tags: Optional[List[str]] = None  # No max items, no max length per tag
```

A user can submit thousands of tags or very long tag strings.

**Remediation:**
```python
tags: Optional[List[str]] = Field(default=None, max_length=20)  # max 20 tags

@field_validator('tags')
@classmethod
def validate_tags(cls, v):
    if v:
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag too long (max 50 characters)")
    return v
```

---

## LOW Findings

### 24. No `.env` File in `.gitignore`
**Risk:** Accidental credential commit

Verify that `.env` is listed in `.gitignore` to prevent accidentally committing secrets.

---

### 25. Token Type Confusion Prevention Is Weak
**File:** `core/security.py:45-49`
**Risk:** Token misuse

The token type check exists but uses a simple string comparison. If an attacker crafts a token with `"type": "access"` as a refresh token or vice versa, the check is the only barrier.

**Remediation:** Use separate signing keys for access vs. refresh tokens.

---

### 26. No Security Headers
**Risk:** Clickjacking, MIME sniffing, etc.

Missing headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security`
- `Content-Security-Policy`

**Remediation:**
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## INFORMATIONAL

### 27. Supabase PostgREST Protects Against SQL Injection
The Supabase Python SDK uses PostgREST under the hood, which uses parameterized queries. Direct SQL injection via the SDK's `.eq()`, `.select()`, `.insert()` methods is not possible. However:
- Never use raw SQL queries
- Always validate input types before passing to SDK
- UUID validation on IDs adds defense in depth

### 28. Row Level Security (RLS) Provides Additional Layer
The database schema includes RLS policies that enforce `user_id = auth.uid()`. This means even if application-level checks are bypassed, the database enforces row-level access control (when using the anon key client).

---

## Database Injection Analysis

| Vector | Risk Level | Protected By |
|--------|-----------|--------------|
| SQL Injection via API params | LOW | PostgREST parameterized queries |
| SQL Injection via string fields | LOW | PostgREST parameterized queries |
| NoSQL Injection | N/A | Not applicable (PostgreSQL) |
| ORM Injection | LOW | No raw ORM usage |
| JSONB Injection | MEDIUM | `Dict[str, Any]` fields accept arbitrary JSON |
| Path Traversal | LOW | No file operations |
| LDAP Injection | N/A | Not applicable |
| Command Injection | N/A | No shell commands |

---

## Data Leak Risk Analysis

| Data Type | Risk | Current Protection | Recommended |
|-----------|------|-------------------|-------------|
| Passwords | HIGH | Supabase Auth handles hashing | Add strength validation |
| JWT Tokens | HIGH | HMAC-SHA256 signing | Add token blacklist |
| User Emails | MEDIUM | RLS + user_id filtering | Rate limit account enumeration |
| Integration Credentials | HIGH | None (plain JSON) | Encrypt at rest |
| User Activity Data | LOW | RLS policies | Add audit logging |
| API Keys (Supabase) | CRITICAL | .env file | Verify .gitignore, rotate regularly |
| Error Stack Traces | MEDIUM | Global exception handler | Remove `str(e)` from responses |

---

## Priority Remediation Checklist

### Immediate (Before Production)
- [ ] Add password strength validation (min 8 chars, complexity)
- [ ] Implement rate limiting on auth endpoints
- [ ] Set `debug = False` by default
- [ ] Remove `str(e)` from error responses (log internally only)
- [ ] Disable `/docs` and `/redoc` in production
- [ ] Add UUID validation on path parameters
- [ ] Fix all `.single()` calls to handle missing data

### Short-term (Week 1-2)
- [ ] Implement token blacklist for logout
- [ ] Add security headers middleware
- [ ] Encrypt integration credentials at rest
- [ ] Add pagination to all list endpoints
- [ ] Add `max_length` to all text fields
- [ ] Validate and sanitize all string inputs
- [ ] Configure CORS with production origins
- [ ] Add request body size limits

### Medium-term (Week 3-4)
- [ ] Add structured audit logging
- [ ] Implement refresh token rotation
- [ ] Remove `supabase_admin` from application runtime
- [ ] Add HTTPS enforcement
- [ ] Add OWASP security scanning to CI/CD
- [ ] Penetration testing

---

## Testing Recommendations

1. **Authentication Testing:**
   - Brute force login with common passwords
   - Test token reuse after logout
   - Test expired token handling
   - Test refresh token with access token and vice versa

2. **Authorization Testing:**
   - Access other users' projects/tasks via ID guessing
   - Attempt to modify resources belonging to other users
   - Test RLS policies directly via Supabase dashboard

3. **Input Validation Testing:**
   - Submit XSS payloads in all text fields
   - Submit extremely long strings (>1MB)
   - Submit invalid JSON in `Dict[str, Any]` fields
   - Submit non-UUID strings as IDs

4. **Rate Limiting Testing:**
   - Rapid-fire login attempts
   - Mass signup attempts
   - Bulk API requests from single IP

---

*Report generated by security analysis of the Raimon backend codebase.*
