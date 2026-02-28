#!/bin/bash
# InfluxDB setup script for FactoryOPS
# Creates telemetry bucket with 90-day retention

set -e

INFLUX_URL="${INFLUXDB_URL:-http://localhost:8086}"
INFLUX_ORG="${INFLUXDB_ORG:-factoryops}"
INFLUX_TOKEN="${INFLUXDB_TOKEN:-factoryops-admin-token}"

echo "Waiting for InfluxDB to be ready..."
until curl -s -f "${INFLUX_URL}/health" > /dev/null 2>&1; do
    echo "Waiting..."
    sleep 2
done

echo "InfluxDB is ready!"

# Create the telemetry bucket if it doesn't exist
echo "Creating telemetry bucket..."
curl -s -X POST "${INFLUX_URL}/api/v2/buckets" \
    -H "Authorization: Token ${INFLUX_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
        \"org\": \"${INFLUX_ORG}\",
        \"name\": \"telemetry\",
        \"retentionRules\": [
            {
                \"type\": \"expire\",
                \"everySeconds\": 7776000
            }
        ],
        \"description\": \"FactoryOPS telemetry data - 90 day retention\"
    }" || echo "Bucket may already exist"

echo "InfluxDB setup complete!"
