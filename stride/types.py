from dataclasses import dataclass

from influxdb import InfluxDBClient
from pydantic_ai import Agent


@dataclass
class AppContext:
    influx_conn: InfluxDBClient
    agent: Agent | None = None
