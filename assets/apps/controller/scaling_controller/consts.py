DB_PATH = 'metrics.db'
KEY = '/opt/test/assets/general/key.rsa'
MAX_INSTANCES = 3

INSERT_VALUE = "insert into metrics(instance, timestamp, metric, value) values (?, ?, ?, ?)"
CREATE_METRICS_TABLE = """
CREATE TABLE metrics(
    instance,
    timestamp,
    metric,
    value
)
"""
GET_LAST_METRIC = """
SELECT value FROM metrics 
WHERE 
  instance=? AND metric=? 
ORDER BY timestamp DESC
LIMIT 1
"""
