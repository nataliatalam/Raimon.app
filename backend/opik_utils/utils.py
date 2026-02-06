"""
Helper functions for Opik tracking and formatting
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime, timezone


def format_trace_data(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format trace data for logging

    Args:
        data: The trace data to format
        indent: Number of spaces for indentation

    Returns:
        str: Formatted JSON string

    Example:
        >>> trace = {"model": "gemini-2.0-flash", "tokens": 150}
        >>> print(format_trace_data(trace))
    """
    return json.dumps(data, indent=indent, default=str)


def sanitize_prompt(prompt: str, max_length: int = 1000) -> str:
    """
    Sanitize and truncate prompts for logging

    Args:
        prompt: The prompt text to sanitize
        max_length: Maximum length before truncation

    Returns:
        str: Sanitized prompt

    Example:
        >>> long_prompt = "A" * 2000
        >>> short = sanitize_prompt(long_prompt, max_length=100)
        >>> len(short) <= 103  # 100 + "..."
    """
    if len(prompt) > max_length:
        return prompt[:max_length] + "..."
    return prompt


def extract_metadata(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata from request data

    Args:
        request_data: The raw request data

    Returns:
        Dict: Extracted metadata

    Example:
        >>> request = {"timestamp": "2026-01-24", "user_id": "123", "extra": "data"}
        >>> metadata = extract_metadata(request)
        >>> "user_id" in metadata
        True
    """
    return {
        "timestamp": request_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "user_id": request_data.get("user_id"),
        "session_id": request_data.get("session_id"),
        "request_id": request_data.get("request_id"),
    }


def build_trace_context(
    operation: str,
    input_data: Any,
    output_data: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a standardized trace context for Opik

    Args:
        operation: Name of the operation being traced
        input_data: Input data for the operation
        output_data: Output data from the operation
        metadata: Additional metadata

    Returns:
        Dict: Standardized trace context

    Example:
        >>> context = build_trace_context(
        ...     operation="llm_call",
        ...     input_data={"prompt": "Hello"},
        ...     output_data={"response": "Hi there!"},
        ...     metadata={"model": "gemini-2.0-flash"}
        ... )
        >>> context["operation"]
        'llm_call'
    """
    return {
        "operation": operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_data,
        "output": output_data,
        "metadata": metadata or {},
    }


def calculate_token_cost(
    tokens_used: int,
    model_name: str = "gemini-2.0-flash",
    cost_per_1k: float = 0.001
) -> float:
    """
    Calculate the cost of tokens used

    Args:
        tokens_used: Number of tokens consumed
        model_name: Name of the model
        cost_per_1k: Cost per 1000 tokens

    Returns:
        float: Estimated cost in dollars

    Example:
        >>> cost = calculate_token_cost(tokens_used=5000, cost_per_1k=0.001)
        >>> cost
        0.005
    """
    return (tokens_used / 1000) * cost_per_1k


def format_duration(seconds: float) -> str:
    """
    Format duration in a human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration string

    Example:
        >>> format_duration(0.123)
        '123.00ms'
        >>> format_duration(1.5)
        '1.50s'
        >>> format_duration(65)
        '1m 5.00s'
    """
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"


def mask_sensitive_data(data: Dict[str, Any], keys_to_mask: list[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary

    Args:
        data: Dictionary containing potentially sensitive data
        keys_to_mask: List of keys to mask (defaults to common sensitive keys)

    Returns:
        Dict: Dictionary with masked sensitive data

    Example:
        >>> data = {"password": "secret123", "username": "john"}
        >>> masked = mask_sensitive_data(data, keys_to_mask=["password"])
        >>> masked["password"]
        '***MASKED***'
    """
    if keys_to_mask is None:
        keys_to_mask = ["password", "api_key", "secret", "token", "authorization"]

    masked_data = data.copy()
    for key in keys_to_mask:
        if key in masked_data:
            masked_data[key] = "***MASKED***"

    return masked_data
