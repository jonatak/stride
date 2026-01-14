import asyncio

from fastapi import BackgroundTasks

from stride.domain.chat.dao import get_history, insert_message
from stride.types import AppContext

from .schemas import ChatStreamResponse
from .tasks import messages_summary


async def sync_chat(ctx: AppContext, background_task: BackgroundTasks, message: str):
    assert ctx.agent
    async with ctx.pg_pool.connection() as conn:
        history = await get_history(conn)
        async with ctx.agent:
            result = await ctx.agent.run(message, message_history=history)
            messages = result.new_messages()
            message_id = await insert_message(conn, messages=messages)
            background_task.add_task(
                messages_summary, ctx, message_id, result.all_messages()
            )
            return result.output


def sse_data(msg: ChatStreamResponse) -> str:
    return f"data: {msg.model_dump_json()}\n\n"


# SSE "comment" line; clients ignore it but it keeps the connection alive.
def sse_ping() -> str:
    return ": ping\n\n"


async def stream_chat(ctx: AppContext, background_task: BackgroundTasks, message: str):
    assert ctx.agent is not None

    HEARTBEAT_SECONDS = 1
    async with ctx.pg_pool.connection() as conn:
        history = await get_history(conn)
        try:
            async with ctx.agent:
                async with ctx.agent.run_stream(
                    message, message_history=history
                ) as result:
                    stream = result.stream_text(delta=True)
                    aiter = stream.__aiter__()
                    while True:
                        try:
                            # wait for next token, but don't block forever
                            delta = await asyncio.wait_for(
                                anext(aiter), timeout=HEARTBEAT_SECONDS
                            )
                            yield sse_data(ChatStreamResponse(delta=delta))
                        except asyncio.TimeoutError:
                            # no tokens (likely tool call / thinking) -> keep connection alive
                            yield sse_ping()
                            continue
                        except StopAsyncIteration:
                            break
                    message_id = await insert_message(conn, result.new_messages())
                    background_task.add_task(
                        messages_summary, ctx, message_id, result.all_messages()
                    )

                    yield sse_data(ChatStreamResponse(done=True))

        except Exception as e:
            yield sse_data(ChatStreamResponse(error=str(e)))
