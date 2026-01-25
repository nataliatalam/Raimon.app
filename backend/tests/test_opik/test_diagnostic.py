"""
Diagnostic tests for Opik and Gemini integration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import opik

# Force load .env from the root directory
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def check_systems():
    """
    Diagnostic check for Gemini and Opik systems
    Tests both APIs to ensure they're properly configured
    """
    print(f"--- 🔍 DIAGNOSTIC (Path: {env_path}) ---")

    # 1. Test Gemini
    gemini_key = os.getenv('GOOGLE_API_KEY')
    if not gemini_key:
        print("❌ Gemini: GOOGLE_API_KEY is missing from .env")
    else:
        print(f"[1/2] Checking Gemini Key: {gemini_key[:8]}...")
        try:
            client = genai.Client(api_key=gemini_key)
            # Use the full GA version name for 2026
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents="Raimon test"
            )
            print("✅ Gemini: SUCCESS")
        except Exception as e:
            print(f"❌ Gemini: FAILED - {str(e)[:150]}")

    # 2. Test Opik
    opik_key = os.getenv('OPIK_API_KEY')
    if not opik_key:
        print("❌ Opik: OPIK_API_KEY is missing from .env")
    else:
        print(f"[2/2] Checking Opik Key: {opik_key[:8]}...")
        try:
            opik.configure(api_key=opik_key, workspace=os.getenv("OPIK_WORKSPACE"))
            client = opik.Opik()
            print("✅ Opik: Authenticated Successfully")
        except Exception as e:
            print(f"❌ Opik: FAILED - {e}")


if __name__ == "__main__":
    check_systems()
