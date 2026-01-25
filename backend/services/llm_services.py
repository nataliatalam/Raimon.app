# services/llm_service.py
import sys
import os
from google import genai
from opik import Opik, track
# Add the root 'backend' folder to the search path
# This ensures sibling folders like 'config' can see each other
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the global OpikManager instance
client = Opik()

ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@track
def generate_response(prompt: str):
    try:
        # Az új, 2026-os SDK szintaxis
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    print("🚀 Testing LLM Service...")
    result = generate_response("Say hello!")
    print(f"Gemini Response: {result}")