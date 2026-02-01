"""
Test tracing functionality with Opik
Migrated from backend/tests/test_tracing.py
"""
import sys
import os

# Add the backend folder to the path so we can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.llm_services import generate_response


def test_basic_tracing():
    """Test that tracing works with Gemini and Opik"""
    result = generate_response("What is 2+2?")
    print(f"Result: {result}")
    print("Check your Opik dashboard for the trace!")
    return result


if __name__ == "__main__":
    test_basic_tracing()
