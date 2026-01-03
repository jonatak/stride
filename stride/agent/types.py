from dataclasses import dataclass


@dataclass
class AgentContext:
    mcp_url: str
    agent_model: str
    agent_base_url: str
    agent_api_key: str
