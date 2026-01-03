import asyncio
from datetime import date
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse

from stride import domain
from stride.api.schemas import (
    ActivitiesResponse,
    ActivityDetailsResponse,
    ActivityInfoResponse,
    ChatRequest,
    ChatStreamResponse,
    PaceResponse,
)
from stride.domain.types import HRInfos
from stride.types import AppContext


def get_router(ctx: AppContext) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/hr/zones")
    def hr_zone() -> HRInfos:
        return domain.generate_hr_zone_infos()

    @router.get("/pace/monthly")
    def pace_monthly(start: date, end: date) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_series_monthly(ctx, start, end))

    @router.get("/summary/yearly/{year}")
    def pace_yearly(
        year: Annotated[int, Path(title="The year of the summary", ge=2021, lt=2050)],
    ) -> PaceResponse:
        return PaceResponse(series=domain.generate_pace_info_yearly(ctx, year))

    @router.get("/activities")
    def activities(start: date, end: date) -> ActivitiesResponse:
        return ActivitiesResponse(
            series=domain.generate_activities_infos(ctx, start, end)
        )

    @router.get("/activities/details/{activity_id}")
    def activity_details(activity_id: int) -> ActivityDetailsResponse:
        return ActivityDetailsResponse(
            series=domain.generate_activity_details_serie(ctx, activity_id)
        )

    @router.get("/activities/{activity_id}")
    def activity_info(activity_id: int) -> ActivityInfoResponse:
        activity = domain.generate_activity_info_by_id(ctx, activity_id)

        if activity is None:
            raise HTTPException(status_code=404, detail="Item not found")

        return ActivityInfoResponse(
            activity=domain.generate_activity_info_by_id(ctx, activity_id)
        )

    @router.post("/chat")
    async def chat_simple(payload: ChatRequest):
        assert ctx.agent
        async with ctx.agent:
            result = await ctx.agent.run(payload.message)
            return result.output

    @router.post("/chat/stream")
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
