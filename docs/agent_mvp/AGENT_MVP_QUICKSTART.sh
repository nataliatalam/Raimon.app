#!/bin/bash
# Agent MVP - Quick Start Script
# Run from backend directory

echo "🚀 Agent MVP Quick Start"
echo "======================"
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
python --version
echo ""

# Check required env vars
echo "2️⃣  Checking environment variables..."
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY not set. Add to .env file."
    exit 1
fi
echo "✅ GOOGLE_API_KEY found"
echo ""

# Run tests
echo "3️⃣  Running tests..."
echo ""
pytest tests_agent_mvp/ -v --tb=short
TEST_RESULT=$?
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "4️⃣  Ready to start server..."
    echo ""
    echo "Run this command to start the backend:"
    echo "  uvicorn main:app --reload"
    echo ""
    echo "Then test the endpoint:"
    echo "  curl -X POST http://localhost:8000/agent-mvp/simulate"
    echo ""
else
    echo "❌ Tests failed. Fix issues above."
    exit 1
fi
