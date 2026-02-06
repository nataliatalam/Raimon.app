"""
Tests for Agent MVP refactored implementation.

These tests verify that the refactored agent modules work correctly
with the new modularized structure:
- agents/llm_agents/ - LLM-powered agents
- agents/deterministic_agents/ - Deterministic agents
- agents/events.py - Event logging
- models/contracts.py - Data models
- orchestrator/ - Orchestration logic
- services/ - Service layer (storage, LLM)

Test files:
- test_do_selector.py - DoSelector agent tests
- test_events.py - Event logging tests
- test_gamification.py - Gamification rules tests
- test_graph.py - Orchestrator graph integration tests
- test_orchestrator.py - Orchestrator tests
- test_selector_contracts.py - Contract validation tests
"""
