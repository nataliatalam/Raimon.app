import os
from dotenv import load_dotenv

load_dotenv()

# Set environment variables so Opik finds them immediately on import
# This stops the "API key must be specified" warning
os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY", "")
os.environ["OPIK_WORKSPACE"] = os.getenv("OPIK_WORKSPACE", "default")
os.environ["OPIK_PROJECT_NAME"] = os.getenv("OPIK_PROJECT_NAME", "raimon")

import opik
from opik import Opik
from opik.integrations.genai import track_genai
from google import genai

class OpikManager:
    _instance = None
    _opik_client = None
    _tracked_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpikManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Opik and Gemini with tracking"""
        # Initialize Opik client using the environment variables set above
        self._opik_client = Opik()
        
        # Initialize Gemini Client (THE 2026 WAY)
        # Note: No more genai.configure() - we create a client instance
        raw_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Wrap the client instance with Opik tracking
        # Opik now tracks the client instance, not the whole module
        self._tracked_client = track_genai(raw_client)
        
        print("✅ Opik and Gemini (2026 SDK) initialized successfully")
    
    @property
    def opik(self):
        return self._opik_client
    
    @property
    def genai(self):
        """Returns the tracked Gemini client instance"""
        return self._tracked_client

# Global instance
opik_manager = OpikManager()