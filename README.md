# Garmin-Reports

A simple project to export reports from garmin data.

## Helpers

Query to get influxdb pace for a certain timerange for zone2 running.
```
SELECT (mean("DurationSeconds") / 60) / (mean("Distance") / 1000)  
FROM "ActivityGPS" 
WHERE 
  time >= now() - 7d AND time <= now()
  AND "HearRate" >= 135
  AND "HearRate" <= 152
GROUP BY time(1m) fill(null)
```