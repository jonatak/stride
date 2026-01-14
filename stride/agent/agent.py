from pydantic_ai import Agent, ModelMessage
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from stride.agent.types import AgentContext

from .prompts import SYSTEM_PROMPT


def build_chat_agent(ctx: AgentContext) -> Agent:
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


def context_aware_processor(
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Filter messages based on context
    if len(messages) > 15:
        return messages[-15:]  # Keep only recent messages when token usage is high
    return messages


def build_summary_agent(ctx: AgentContext) -> Agent:
    model = OpenAIChatModel(
        ctx.agent_summary_model,
        provider=OpenAIProvider(
            base_url=ctx.agent_base_url,
            api_key=ctx.agent_api_key,  # ignored by Ollama, but required by the client interface
        ),
    )

    return Agent(model=model, history_processors=[context_aware_processor])
