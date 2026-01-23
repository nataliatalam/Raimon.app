# services/llm_service.py
import sys
import os

# Add the root 'backend' folder to the search path
# This ensures sibling folders like 'config' can see each other
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.opik_config import opik_manager

def generate_response(prompt: str):
    try:
        # Use the modern .models syntax for the 2026 SDK
        response = opik_manager.genai.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    print("🚀 Testing LLM Service...")
    result = generate_response("Say hello!")
    print(f"Gemini Response: {result}")