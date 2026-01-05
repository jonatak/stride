from contextlib import asynccontextmanager

from fastapi import FastAPI
from influxdb import InfluxDBClient
from psycopg_pool import ConnectionPool


def init_influx_connection(
    host: str, port: int, user: str, password: str, db: str
) -> InfluxDBClient:
    client = InfluxDBClient(
        host=host,
        port=port,
        username=user,
        password=password,
        database=db,
    )
    return client


def init_postgres_connection(uri: str) -> ConnectionPool:
    return ConnectionPool(uri, max_size=4, min_size=2)


def create_fast_api_lifespan(pool: ConnectionPool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pool.open()
        yield
        pool.close()

    return lifespan
