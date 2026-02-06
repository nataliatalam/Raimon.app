"""
Opik dashboard configurations and queries.

Pre-built dashboard queries and visualization configs for Opik observability.
Includes queries for:
- Agent health and performance
- Task selection accuracy
- User engagement
- Quality metrics (hallucination, motivation, stuck detection)
"""

from opik_utils.dashboards.opik_queries import OpikQueries

__all__ = [
    "OpikQueries",
]
