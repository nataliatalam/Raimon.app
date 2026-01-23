import os
from dotenv import load_dotenv
from google import genai  # Correct import for the new SDK
import opik

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

# 1. Test Gemini (New Client-based approach)
try:
    # The new SDK uses a Client object instead of a global configure()
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Use gemini-2.0-flash for general testing
    response = client.models.generate_content(
        model=MODEL_NAME, 
        contents="Say hello"
    )
    print("✅ Gemini API working:", response.text[:50])
except Exception as e:
    print("❌ Gemini API error:", e)

# 2. Test Opik
try:
    from opik import Opik
    client = Opik()
    print("✅ Opik connection successful")
except Exception as e:
    print("❌ Opik connection error:", e)