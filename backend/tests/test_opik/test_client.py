"""
Tests for Opik client functionality
"""
import pytest
from opik_utils import get_opik_client, OpikManager


def test_opik_client_singleton():
    """Test that OpikManager is a singleton"""
    client1 = get_opik_client()
    client2 = get_opik_client()
    assert client1 is client2


def test_opik_client_has_opik_property():
    """Test that OpikManager has opik property"""
    client = get_opik_client()
    assert hasattr(client, "opik")
    assert client.opik is not None


def test_opik_client_has_genai_property():
    """Test that OpikManager has genai property"""
    client = get_opik_client()
    assert hasattr(client, "genai")
    assert client.genai is not None


def test_opik_manager_instance():
    """Test OpikManager instantiation"""
    manager = OpikManager()
    assert manager is not None
    assert isinstance(manager, OpikManager)
