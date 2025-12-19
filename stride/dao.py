from datetime import date

from influxdb import InfluxDBClient

PACE_QUERY = """
SELECT last("DurationSeconds") as duration_s, mean("HeartRate") as hr, last("Distance") as distance_m, last("Activity_ID") as activity_id
FROM "ActivityGPS"
WHERE
  time >= '{start}'
  AND time <= '{end}'
  AND ("ActivitySelector"::tag =~ /-running$/)
GROUP BY time(1m), "ActivityID" fill(none)
"""


def init_connection(
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


def get_pace_series(conn: InfluxDBClient, start: date, end: date):
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = PACE_QUERY.format(start=start_str, end=end_str)

    return list(conn.query(query))
