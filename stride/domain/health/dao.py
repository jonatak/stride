from datetime import date

from influxdb import InfluxDBClient

VO2_MAX_QUERY = """
SELECT mean("VO2_max_value") as vo2_max
FROM "VO2_Max"
WHERE
  time >= '{start}'
  AND time <= '{end}'
GROUP BY time(1d) fill(null)
"""

WEIGHT_QUERY = """
SELECT (mean("weight")/ 1000) as weight
FROM "BodyComposition"
WHERE
  time >= '{start}'
  AND time <= '{end}'
GROUP BY time(1d) fill(null)
"""


def get_vo2_max_series(conn: InfluxDBClient, start: date, end: date):
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = VO2_MAX_QUERY.format(start=start_str, end=end_str)
    return list(conn.query(query))


def get_weight_series(conn: InfluxDBClient, start: date, end: date):
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = WEIGHT_QUERY.format(start=start_str, end=end_str)
    return list(conn.query(query))
