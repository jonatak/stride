from dataclasses import dataclass

from influxdb import InfluxDBClient
from psycopg_pool import ConnectionPool
from pydantic_ai import Agent


@dataclass
class AppContext:
    influx_conn: InfluxDBClient
    pg_pool: ConnectionPool
    agent: Agent | None = None
