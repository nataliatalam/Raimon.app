"""
Opik client manager for Raimon
Handles initialization and provides singleton access to Opik and Gemini clients
"""
import os
from dotenv import load_dotenv
from opik import Opik, track
from core.config import get_settings
from google import genai

load_dotenv()
settings = get_settings()
# genai.configure(api_key=settings.gemini_api_key)

class OpikManager:
    """
    Singleton manager for Opik client and tracked Gemini client

    Usage:
        from opik import get_opik_client

        opik_manager = get_opik_client()
        response = opik_manager.genai.models.generate_content(...)
    """
    _instance = None
    _opik_client = None
    _raw_client = None
    # _tracked_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpikManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Opik and Gemini with tracking"""
        # Set environment variables so Opik finds them immediately on import
        # This stops the "API key must be specified" warning
        os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY", "")
        os.environ["OPIK_WORKSPACE"] = os.getenv("OPIK_WORKSPACE", "default")
        os.environ["OPIK_PROJECT_NAME"] = os.getenv("OPIK_PROJECT_NAME", "raimon")

        # Initialize Opik client using the environment variables set above
        self._opik_client = Opik()

        # Initialize Gemini Client (THE 2026 WAY)
        # Note: No more genai.configure() - we create a client instance
        # raw_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # Wrap the client instance with Opik tracking
        # Opik now tracks the client instance, not the whole module
        # self._tracked_client = track_genai(raw_client)

        # New SDK INICIALIZ (2026): for direct use in tracked methods
        self._raw_client = genai.Client(api_key=settings.google_api_key)

        print("✅ Opik and Gemini (2026 SDK) initialized successfully")

    @property
    def opik(self):
        """Returns the Opik client instance"""
        return self._opik_client

    # @property
    # def genai(self):
    #     """Returns the tracked Gemini client instance"""
    #     return self._tracked_client

    @property
    def genai(self):
        """Returns this manager instance to handle tracked calls"""
        return self

    @track(name="gemini_generation") # This sends the data to Opik dashboard
    def generate_content(self, prompt: str, model: str = "gemini-2.5-flash-lite"):
        """
        Tracked version of content generation.
        Usage: manager.genai.generate_content("Hello")
        """
        response = self._raw_client.models.generate_content(
            model=model,
            contents=prompt
        )
        
        # Returning data with usage metadata for Opik
        return {
            "text": response.text,
            "usage": response.usage_metadata,
            "model": model
        }

# Global instance - created once on module import
_opik_manager = OpikManager()


def get_opik_client() -> OpikManager:
    """
    Get the global OpikManager instance

    Returns:
        OpikManager: Singleton instance with opik and genai clients

    Example:
        >>> from opik import get_opik_client
        >>> manager = get_opik_client()
        >>> response = manager.genai.models.generate_content(...)
    """
    return _opik_manager