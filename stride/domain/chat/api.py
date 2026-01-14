from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse

from stride.domain.chat.schemas import ChatRequest
from stride.domain.chat.service import stream_chat, sync_chat
from stride.types import AppContext


def get_chat_router(ctx: AppContext) -> APIRouter:
    router = APIRouter()

    @router.post("/message")
    async def chat_simple(payload: ChatRequest, background_tasks: BackgroundTasks):
        return await sync_chat(ctx, background_tasks, payload.message)

    @router.post("/stream")
    async def chat(payload: ChatRequest, background_tasks: BackgroundTasks):
        return StreamingResponse(
            stream_chat(ctx, background_tasks, payload.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
