from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool


def init_postgres_connection(uri: str) -> AsyncConnectionPool:
    return AsyncConnectionPool(uri, max_size=4, min_size=2, open=False)


def create_fast_api_lifespan(pool: AsyncConnectionPool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await pool.open()
        yield
        await pool.close()

    return lifespan
