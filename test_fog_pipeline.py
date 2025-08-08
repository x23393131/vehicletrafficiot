import boto3
import json
import time
from datetime import datetime

# CONFIGURATIONS
LAMBDA_NAME = 'fog_handler'
BUCKET_NAME = 'lorawan-traffic-logs'
OBJECT_KEY = 'logs/traffic-latest.csv'
REGION = 'us-east-1'

# AWS Clients
logs_client = boto3.client('logs', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

# 1️⃣ MANUAL TEST INVOCATION
def test_lambda_invocation():
    print("\n🚀 Invoking Lambda with test event...")
    test_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "location": {"lat": 53.349805, "lng": -6.26031},
        "vehicle_count": 42
    }
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        result = json.loads(response['Payload'].read().decode())
        print("✅ Lambda responded:", result)
    except Exception as e:
        print("❌ Lambda invoke error:", str(e))

# 2️⃣ CHECK CLOUDWATCH LOGS
def check_lambda_logs():
    print("\n🔍 Checking recent Lambda logs...")
    try:
        log_group = f"/aws/lambda/{LAMBDA_NAME}"
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        if not streams['logStreams']:
            print("❌ No log streams found.")
            return

        log_stream = streams['logStreams'][0]['logStreamName']
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startTime=int((time.time() - 120) * 1000),
            limit=10
        )

        print("📜 Last log entries:")
        for event in events['events']:
            print(f"  📌 {event['message']}")

    except Exception as e:
        print("❌ Error fetching logs:", str(e))

# 3️⃣ CHECK OUTPUT FILE IN S3
def check_s3_file():
    print("\n📁 Checking S3 for output file...")
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        body = response['Body'].read().decode('utf-8').strip().split('\n')

        print(f"✅ Found {len(body)} lines in {OBJECT_KEY}.")
        print("🧾 Last 25 entries:")

        # Show last 25 or all if fewer lines
        for line in body[-25:]:
            print(f"  → {line}")

    except s3_client.exceptions.NoSuchKey:
        print(f"❌ File not found: {OBJECT_KEY}")
    except Exception as e:
        print("❌ Error reading S3:", str(e))

if __name__ == '__main__':
    test_lambda_invocation()
    time.sleep(5)
    check_lambda_logs()
    check_s3_file()
