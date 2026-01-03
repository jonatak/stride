import asyncio
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from stride.api.schemas import ChatRequest, ChatStreamResponse
from stride.types import AppContext


def get_chat_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.post("/message")
    async def chat_simple(payload: ChatRequest):
        assert ctx.agent
        async with ctx.agent:
            result = await ctx.agent.run(payload.message)
            return result.output

    @router.post("/stream")
    async def chat(payload: ChatRequest):
        def sse_data(msg: ChatStreamResponse) -> str:
            return f"data: {msg.model_dump_json()}\n\n"

        # SSE "comment" line; clients ignore it but it keeps the connection alive.
        def sse_ping() -> str:
            return ": ping\n\n"

        async def event_generator() -> AsyncIterator[str]:
            assert ctx.agent is not None

            HEARTBEAT_SECONDS = 1

            try:
                async with ctx.agent:
                    async with ctx.agent.run_stream(payload.message) as result:
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

                        yield sse_data(ChatStreamResponse(done=True))

            except Exception as e:
                yield sse_data(ChatStreamResponse(error=str(e)))

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
