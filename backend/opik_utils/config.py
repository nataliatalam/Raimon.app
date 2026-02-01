"""
Opik configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class OpikSettings(BaseSettings):
    """
    Opik configuration settings

    Environment variables should be prefixed with OPIK_
    Example: OPIK_API_KEY, OPIK_WORKSPACE, OPIK_PROJECT_NAME
    """
    api_key: str
    workspace: str = "default"
    project_name: str = "raimon"

    # Optional features
    enable_middleware: bool = True
    log_level: str = "INFO"

    class Config:
        env_prefix = "OPIK_"
        env_file = ".env"


def get_opik_settings() -> OpikSettings:
    """
    Get Opik settings singleton

    Returns:
        OpikSettings: Configuration settings for Opik

    Example:
        >>> from opik.config import get_opik_settings
        >>> settings = get_opik_settings()
        >>> print(settings.project_name)
    """
    return OpikSettings()
