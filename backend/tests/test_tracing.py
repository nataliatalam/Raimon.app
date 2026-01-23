# tests/test_tracing.py
from services.llm_service import generate_response

def test_basic_tracing():
    """Test that tracing works"""
    result = generate_response("What is 2+2?")
    print(f"Result: {result}")
    print("Check your Opik dashboard for the trace!")

if __name__ == "__main__":
    test_basic_tracing()