from dataclasses import dataclass

from influxdb import InfluxDBClient
from psycopg_pool import AsyncConnectionPool
from pydantic_ai import Agent


@dataclass
class AppContext:
    influx_conn: InfluxDBClient
    pg_pool: AsyncConnectionPool
    agent: Agent | None = None
