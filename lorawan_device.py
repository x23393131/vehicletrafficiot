import os
import time
import json
import random
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime

# PDATED certificate paths
CA_PATH = "certs/AmazonRootCA1.pem"
CERT_PATH = "certs/device-certificate.pem.crt"
KEY_PATH = "certs/private.pem.key"

# MQTT Configuration
BROKER = "a3hyjp4joybycm-ats.iot.us-east-1.amazonaws.com"  # Replace this
PORT = 8883
TOPIC = "lorawan/traffic"

client = mqtt.Client()

client.tls_set(
    ca_certs=CA_PATH,
    certfile=CERT_PATH,
    keyfile=KEY_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.connect(BROKER, PORT)
client.loop_start()

print(" LoRaWAN device started. Publishing traffic data...")

while True:
    payload = {
        "timestamp": str(datetime.utcnow()),
        "location": {"lat": 53.349805, "lng": -6.26031},
        "vehicle_count": random.randint(1, 20)
    }
    client.publish(TOPIC, json.dumps(payload))
    print(" Sent:", payload)
    time.sleep(5)
