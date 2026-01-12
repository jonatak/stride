from influxdb import InfluxDBClient


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
