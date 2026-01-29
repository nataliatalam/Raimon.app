"""
Agent MVP: LangGraph-orchestrated Gemini agents for task selection and coaching.

Modules:
- contracts: Data models for agent I/O
- gemini_client: Gemini API wrapper with Opik tracing
- prompts: LLM prompt templates
- llm_do_selector: Task selection agent
- llm_coach: Coaching message agent
- validators: Output validation & fallback logic
- graph: LangGraph orchestrator
"""
