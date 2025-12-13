from fastapi import APIRouter, FastAPI


def get_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health():
        return "ok"

    return router


def create_fast_api_app() -> FastAPI:
    app = FastAPI(
        title="Stride",
        description="An api to get relevant garmin data.",
        version="0.1.0",
    )
    app.include_router(get_router())
    return app
