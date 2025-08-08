# AWS LoRaWAN Traffic Monitoring Simulation - Setup Instructions

## 1. Create AWS IoT Core Resources
- Go to AWS IoT Core
- Register a "Thing"
- Download the certificates (place in `certs/`)
- Note your IoT endpoint (replace in `lorawan_device.py`)

## 2. Create and Attach IoT Rule
- Rule Name: `lorawanTrafficRule`
- SQL: SELECT * FROM 'lorawan/traffic'
- Action: Invoke Lambda (select `fog_handler`)

## 3. Create S3 Bucket
- Create an S3 bucket (e.g., `lorawan-traffic-logs`)
- Update `BUCKET_NAME` in `fog_handler.py`

## 4. Deploy Lambda
- Runtime: Python 3.9+
- Permissions: Grant access to `s3:PutObject` and `logs:*`
- Upload `fog_handler.py` as deployment package

## 5. Run Device Simulator
```bash
python3 lorawan_device.py
```

## Output
- Messages sent to AWS IoT Core via MQTT
- Lambda triggered by IoT Rule
- CSV log created in S3 bucket
