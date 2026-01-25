"""
Setup tests for Opik and Gemini integration
Migrated from backend/tests/test_setup.py
"""
import os
from dotenv import load_dotenv
from google import genai  # Correct import for the new SDK
import opik

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"


def test_gemini_api():
    """Test Gemini API with new Client-based approach"""
    try:
        # The new SDK uses a Client object instead of a global configure()
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Use gemini-2.5-flash for general testing
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="Say hello"
        )
        print("✅ Google API working:", response.text[:50])
        return True
    except Exception as e:
        print("❌ Gemini API error:", e)
        return False


def test_opik_connection():
    """Test Opik connection"""
    try:
        from opik import Opik
        client = Opik()
        print("✅ Opik connection successful")
        return True
    except Exception as e:
        print("❌ Opik connection error:", e)
        return False


if __name__ == "__main__":
    print("--- Testing Gemini API ---")
    test_gemini_api()

    print("\n--- Testing Opik Connection ---")
    test_opik_connection()
