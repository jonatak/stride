from pprint import pprint

from psycopg_pool import AsyncConnectionPool
from pydantic_ai import ModelMessage, ModelRequest, SystemPromptPart

from stride.types import AppContext

from .dao import save_summary

SUMMARY_PROMPT = """
You are maintaining a compact, durable memory for an ongoing conversation.

Your task is to summarize the conversation content into a concise internal memory
that will be used as context in future interactions.

RULES (STRICT):
- Be factual and neutral.
- If information is uncertain or speculative, OMIT it.
- Do NOT invent facts.
- Do NOT include conversational filler, tone, or phrasing.
- Do NOT include tool calls, tool outputs, or debugging chatter.

OUTPUT FORMAT:
- Bullet points only.
- Maximum 10 bullets.
- Each bullet must be a single sentence.
- No introduction, no conclusion.
"""


async def messages_summary(ctx: AppContext, last_id: int, messages: list[ModelMessage]):
    if len(messages) > 10:
        summary = await ctx.summary_agent.run(
            SUMMARY_PROMPT, message_history=messages[:-1]
        )
        result: list[ModelMessage] = [
            ModelRequest(
                parts=[
                    SystemPromptPart(
                        content=f"Conversation summary: ...{summary.output}"
                    )
                ]
            )
        ]
        async with ctx.pg_pool.connection() as conn:
            await save_summary(conn, result, last_id)
