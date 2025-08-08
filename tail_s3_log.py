import boto3
import json
import time
from datetime import datetime

# Constants
LAMBDA_NAME = 'fog_handler'
BUCKET_NAME = 'lorawan-traffic-logs'
OBJECT_KEY = 'logs/traffic-latest.csv'
REGION = 'us-east-1'

# Clients
logs_client = boto3.client('logs', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

def check_lambda_logs():
    print("\n🔍 Checking latest Lambda execution logs...")
    try:
        log_group = f"/aws/lambda/{LAMBDA_NAME}"
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        if not streams['logStreams']:
            print("❌ No logs found.")
            return
        stream_name = streams['logStreams'][0]['logStreamName']
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=int((time.time() - 300) * 1000),  # last 5 min
            limit=20
        )
        for e in events['events']:
            print("📌", e['message'].strip())
    except Exception as e:
        print("❌ Error checking logs:", str(e))

def check_s3_output(lines=25):
    print("\n📁 Checking S3 output...")
    try:
        obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        data = obj['Body'].read().decode('utf-8').strip().split('\n')
        print(f"✅ Found {len(data)} entries.")
        print("🧾 Last entries:")
        for line in data[-lines:]:
            print(" →", line)
    except Exception as e:
        print("❌ S3 Read Error:", str(e))

if __name__ == '__main__':
    print("🚦 IoT Core ➝ Lambda ➝ S3 Monitoring Started")
    check_lambda_logs()
    check_s3_output()
