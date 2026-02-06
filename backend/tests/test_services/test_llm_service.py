"""
Tests for LLM Service infrastructure.

Tests cover:
- BaseLLMClient abstract interface
- GeminiClient implementation
- LLMService wrapper and facade
- Provider abstraction and swapping
- Error handling and fallbacks
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from services.llm_service import (
    BaseLLMClient,
    GeminiClient,
    LLMService,
    get_gemini_client,
)


@pytest.mark.unit
@pytest.mark.agent
class TestBaseLLMClient:
    """Test BaseLLMClient abstract interface."""

    def test_base_llm_client_is_abstract(self):
        """BaseLLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMClient()

    def test_base_llm_client_requires_json_method(self):
        """Subclasses must implement generate_json_response."""

        class IncompleteClient(BaseLLMClient):
            def generate_text(self, prompt, temperature=0.7, max_tokens=500):
                return "text"

        with pytest.raises(TypeError):
            IncompleteClient()

    def test_base_llm_client_requires_text_method(self):
        """Subclasses must implement generate_text."""

        class IncompleteClient(BaseLLMClient):
            def generate_json_response(
                self, prompt, expected_format=None, temperature=0.7, max_tokens=1024
            ):
                return {}

        with pytest.raises(TypeError):
            IncompleteClient()


@pytest.mark.unit
@pytest.mark.agent
class TestGeminiClient:
    """Test GeminiClient implementation."""

    def test_gemini_client_requires_api_key(self):
        """GeminiClient raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY not set"):
                GeminiClient()

    def test_gemini_client_with_api_key(self):
        """GeminiClient initializes with API key."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("google.genai.Client"):
                client = GeminiClient()
                assert client.api_key == "test-key"
                assert client.model == "gemini-2.5-flash-lite"

    def test_gemini_client_custom_model(self):
        """GeminiClient accepts custom model."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("google.genai.Client"):
                client = GeminiClient(model="custom-model")
                assert client.model == "custom-model"

    @patch("google.genai.Client")
    def test_gemini_generate_json_success(self, mock_client_class):
        """GeminiClient successfully generates JSON."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '{"key": "value"}'
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient()
            result = client.generate_json_response("test prompt")

            assert result == {"key": "value"}

    @patch("google.genai.Client")
    def test_gemini_generate_json_with_markdown(self, mock_client_class):
        """GeminiClient extracts JSON from markdown code blocks."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = '```json\n{"key": "value"}\n```'
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient()
            result = client.generate_json_response("test prompt")

            assert result == {"key": "value"}

    @patch("google.genai.Client")
    def test_gemini_generate_json_invalid(self, mock_client_class):
        """GeminiClient raises error for invalid JSON."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "not valid json"
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient()
            with pytest.raises(ValueError, match="not valid JSON"):
                client.generate_json_response("test prompt")

    @patch("google.genai.Client")
    def test_gemini_generate_text(self, mock_client_class):
        """GeminiClient successfully generates text."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Generated text response"
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient()
            result = client.generate_text("test prompt")

            assert result == "Generated text response"

    @patch("google.genai.Client")
    def test_gemini_client_is_llm_client(self, mock_client_class):
        """GeminiClient implements BaseLLMClient."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            mock_client_class.return_value = MagicMock()
            client = GeminiClient()
            assert isinstance(client, BaseLLMClient)

    def test_get_gemini_client_singleton(self):
        """get_gemini_client returns singleton instance."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("google.genai.Client"):
                client1 = get_gemini_client()
                client2 = get_gemini_client()
                assert client1 is client2


@pytest.mark.unit
@pytest.mark.agent
class TestLLMService:
    """Test LLMService wrapper and facade."""

    def test_llm_service_default_client(self):
        """LLMService creates default Gemini client."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("google.genai.Client"):
                service = LLMService()
                assert isinstance(service.client, GeminiClient)

    def test_llm_service_custom_client(self):
        """LLMService accepts custom client."""
        mock_client = MagicMock(spec=BaseLLMClient)
        service = LLMService(client=mock_client)
        assert service.client is mock_client

    def test_llm_service_generate_json(self):
        """LLMService delegates generate_json to client."""
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.generate_json_response.return_value = {"result": "test"}

        service = LLMService(client=mock_client)
        result = service.generate_json("test prompt")

        assert result == {"result": "test"}
        mock_client.generate_json_response.assert_called_once()

    def test_llm_service_generate_json_with_params(self):
        """LLMService passes parameters to client."""
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.generate_json_response.return_value = {}

        service = LLMService(client=mock_client)
        service.generate_json(
            "prompt", expected_format="schema", temperature=0.5, max_tokens=500
        )

        mock_client.generate_json_response.assert_called_once_with(
            prompt="prompt",
            expected_format="schema",
            temperature=0.5,
            max_tokens=500,
        )

    def test_llm_service_generate_text(self):
        """LLMService delegates generate_text to client."""
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.generate_text.return_value = "generated text"

        service = LLMService(client=mock_client)
        result = service.generate_text("test prompt")

        assert result == "generated text"
        mock_client.generate_text.assert_called_once()

    def test_llm_service_get_client(self):
        """LLMService provides access to underlying client."""
        mock_client = MagicMock(spec=BaseLLMClient)
        service = LLMService(client=mock_client)
        assert service.get_client() is mock_client

    def test_llm_service_set_client(self):
        """LLMService allows switching client at runtime."""
        client1 = MagicMock(spec=BaseLLMClient)
        client2 = MagicMock(spec=BaseLLMClient)

        service = LLMService(client=client1)
        assert service.client is client1

        service.set_client(client2)
        assert service.client is client2

    def test_llm_service_error_propagation(self):
        """LLMService propagates client errors."""
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.generate_json_response.side_effect = ValueError("Test error")

        service = LLMService(client=mock_client)
        with pytest.raises(ValueError, match="Test error"):
            service.generate_json("prompt")


@pytest.mark.integration
@pytest.mark.agent
class TestLLMServiceIntegration:
    """Integration tests for LLM service with agents."""

    def test_llm_service_with_multiple_agents(self):
        """LLMService can be shared across multiple agents."""
        mock_client = MagicMock(spec=BaseLLMClient)
        mock_client.generate_json_response.return_value = {"task_id": "task-1"}
        mock_client.generate_text.return_value = "coaching message"

        service = LLMService(client=mock_client)

        # Agent 1: JSON response
        result1 = service.generate_json("select task prompt")
        assert result1 == {"task_id": "task-1"}

        # Agent 2: Text response
        result2 = service.generate_text("coaching prompt")
        assert result2 == "coaching message"

        # Service tracks both calls
        assert mock_client.generate_json_response.call_count == 1
        assert mock_client.generate_text.call_count == 1

    def test_llm_service_opik_compatibility(self):
        """LLMService clients maintain Opik @track decorators."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("google.genai.Client"):
                client = GeminiClient()
                # Check that methods have Opik decorator
                assert hasattr(client.generate_json_response, "__wrapped__")
                assert hasattr(client.generate_text, "__wrapped__")
