from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from stride.agent.types import AgentContext

from .prompts import SYSTEM_PROMPT


def build_agent(ctx: AgentContext) -> Agent:
    model = OpenAIChatModel(
        ctx.agent_model,
        provider=OpenAIProvider(
            base_url=ctx.agent_base_url,
            api_key=ctx.agent_api_key,  # ignored by Ollama, but required by the client interface
        ),
    )
    stride_mcp = MCPServerStreamableHTTP(url=ctx.mcp_url)

    return Agent(
        model=model,
        toolsets=[stride_mcp],
        system_prompt=SYSTEM_PROMPT,
    )
