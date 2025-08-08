# lorawan_device.py
# Simulates a LoRaWAN end device sending vehicle count data via MQTT

import json
import time
import paho.mqtt.client as mqtt
from vehicle_detector import detect_vehicles

CA_PATH = "certs/AmazonRootCA1.pem"
CERT_PATH = "certs/device-certificate.pem.crt"
KEY_PATH = "certs/private.pem.key"
MQTT_BROKER = "your-iot-endpoint.amazonaws.com" 


client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("LoRaWAN device started. Sending data to gateway...")

try:
    while True:
        data = detect_vehicles()
        print(f"Sending: {data}")
        client.publish(TOPIC, json.dumps(data))
        time.sleep(10)  # Simulate LoRa delay
except KeyboardInterrupt:
    print("Stopped.")
    client.disconnect()
