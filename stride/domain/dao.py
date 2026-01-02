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

ACTIVITIES_QUERY = """
SELECT
        "ActivityID" as activity_id,
        "activityName" as activity_name,
        "distance" as distance_m,
        "elapsedDuration" as duration_s,
        "averageSpeed" as avg_speed_m_per_s,
        "averageHR" as avg_hr_bpm,
        "maxHR" as max_hr_bpm,
        "hrTimeInZone_1" as z1_s,
        "hrTimeInZone_2" as z2_s,
        "hrTimeInZone_3" as z3_s,
        "hrTimeInZone_4" as z4_s,
        "hrTimeInZone_5" as z5_s
FROM "ActivitySummary"
WHERE
  time >= '{start}'
  AND time <= '{end}'
 AND "activityType" = 'running'
ORDER BY time DESC
"""

ACTIVITY_DETAILS_QUERY = """
SELECT
    last("DurationSeconds") as duration_s,
    mean("HeartRate") as hr,
    last("Distance") as distance_m,
    mean("Altitude") as altitude,
    mean("Cadence") as cadence,
    last("Latitude") as latitude,
    last("Longitude") as longitude
FROM "ActivityGPS"
WHERE
    "Activity_ID" = {activity_id}
GROUP BY time(30s), "Activity_ID" fill(none)
"""

ACTIVITY_INFO_QUERY = """
SELECT
        "ActivityID" as activity_id,
        "activityName" as activity_name,
        "distance" as distance_m,
        "elapsedDuration" as duration_s,
        "averageSpeed" as avg_speed_m_per_s,
        "averageHR" as avg_hr_bpm,
        "maxHR" as max_hr_bpm,
        "hrTimeInZone_1" as z1_s,
        "hrTimeInZone_2" as z2_s,
        "hrTimeInZone_3" as z3_s,
        "hrTimeInZone_4" as z4_s,
        "hrTimeInZone_5" as z5_s,
        time
FROM "ActivitySummary"
WHERE
  "Activity_ID" = {activity_id}
LIMIT 1
"""

VO2_MAX_QUERY = """
SELECT mean("VO2_max_value") as vo2_max
FROM "VO2_Max"
WHERE
  time >= '{start}'
  AND time <= '{end}'
GROUP BY time(1d) fill(null)
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


def get_activities_series(conn: InfluxDBClient, start: date, end: date):
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = ACTIVITIES_QUERY.format(start=start_str, end=end_str)

    return list(conn.query(query))


def get_activity_details_series(conn: InfluxDBClient, activity_id: int):
    query = ACTIVITY_DETAILS_QUERY.format(activity_id=activity_id)
    return list(conn.query(query))


def get_activity_info(conn: InfluxDBClient, activity_id: int):
    query = ACTIVITY_INFO_QUERY.format(activity_id=activity_id)
    return list(conn.query(query))


def get_vo2_max_series(conn: InfluxDBClient, start: date, end: date):
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    query = VO2_MAX_QUERY.format(start=start_str, end=end_str)

    return list(conn.query(query))
