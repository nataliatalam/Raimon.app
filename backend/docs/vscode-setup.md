# Running Raimon Backend in VS Code

## Prerequisites

1. **Python 3.9+** installed
2. **VS Code** with these extensions:
   - Python (ms-python.python)
   - Pylance (ms-python.vscode-pylance)
   - Python Debugger (ms-python.debugpy)

## Initial Setup

### 1. Open the Backend Folder

```
File → Open Folder → Select /backend
```

Or from terminal:
```bash
cd /Users/olubusayoamowe/Desktop/Raimon.app/backend
code .
```

### 2. Create Virtual Environment

Open VS Code integrated terminal (`Ctrl+`` or `Cmd+``):

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the backend folder:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_public_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional
DEBUG=true
```

### 5. Select Python Interpreter

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Select the interpreter from `./venv/bin/python`

## Running the Server

### Method 1: Using the Debugger (Recommended)

1. Go to **Run and Debug** panel (`Cmd+Shift+D` or `Ctrl+Shift+D`)
2. Select **"FastAPI Backend"** from the dropdown
3. Press **F5** or click the green play button

The server will start with hot-reload enabled at `http://localhost:8000`

### Method 2: Using the Terminal

```bash
# Make sure venv is activated
source venv/bin/activate

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Using VS Code Tasks

Press `Cmd+Shift+B` or `Ctrl+Shift+B` to run the build task (if configured).

## Debugging

### Set Breakpoints

1. Click on the line number gutter to set a breakpoint (red dot)
2. Start the debugger with **"FastAPI Backend"** configuration
3. Make a request to the endpoint
4. Code execution will pause at the breakpoint

### Debug Console

While paused at a breakpoint:
- View variables in the **Variables** panel
- Execute Python code in the **Debug Console**
- Step through code with F10 (step over) or F11 (step into)

## Testing Endpoints

### Using Swagger UI

Open `http://localhost:8000/docs` in your browser for interactive API documentation.

### Using REST Client Extension

Install the **REST Client** extension, then create a `.http` file:

```http
### Health Check
GET http://localhost:8000/health

### Login
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "yourpassword"
}

### List Projects (with auth)
GET http://localhost:8000/api/projects
Authorization: Bearer YOUR_TOKEN_HERE
```

### Using curl in Terminal

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

## Common Issues

### Port Already in Use

If you get "Address already in use" error:

```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Module Not Found

Make sure your virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Supabase Connection Error

1. Verify your `.env` file has correct credentials
2. Check that your Supabase project is active
3. Ensure your IP is not blocked by Supabase

### Authentication 401 Errors

1. Make sure you're passing the token: `Authorization: Bearer <token>`
2. Check if the token is expired (default 30 minutes)
3. Use `/api/auth/refresh-token` to get a new token

## Project Structure

```
backend/
├── .vscode/
│   ├── launch.json      # Debug configurations
│   └── settings.json    # VS Code settings
├── core/
│   ├── config.py        # Settings management
│   ├── security.py      # JWT & auth
│   └── supabase.py      # Database client
├── models/              # Pydantic schemas
├── routers/             # API endpoints
├── database/
│   └── schema.sql       # Database schema
├── docs/                # Documentation
├── main.py              # Application entry
├── requirements.txt     # Dependencies
└── .env                 # Environment variables
```
