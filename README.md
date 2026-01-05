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

## TODO

### Hygiene
- [ ] Organise FastAPI doc per section
- [ ] Add docstring and high level documentation
- [ ] Add UnitTest
- [ ] Review polars data manipulation for more safety and precision
- [ ] Implement caching solution or DB layer for the heaviest endpoint
- [ ] Implement a DB layer for conversation history with agent
- [ ] Add guardrail on API endpoint for query validation and error management
- [ ] Improve MCP querying for models
- [ ] Separate main api into different router for more explicit domain (health, activity and performance)
- [ ] Add obvervability (agent execution, query time ...)

### Features
- [ ] Add CSV export (for chatGPT usage)
- [ ] Implement user profile (simple yaml solution)
- [ ] Implement RAG pipeline to improve agent response
- [ ] Add AI generated summary for each activity on the activity page
