# fog_handler.py
# Real-time LoRaWAN MQTT listener that prints vehicle data to terminal

import paho.mqtt.client as mqtt
import json
import time
import ssl

# MQTT Configuration
MQTT_BROKER = "a3hyjp4joybycm-ats.iot.us-east-1.amazonaws.com"  # your AWS IoT Core endpoint
MQTT_PORT = 8883
TOPIC = "lorawan/traffic"
CERT_PATH = "certs/"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connected to AWS IoT Core")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Connection failed (reason code: {reason_code})")

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"⚠️ Disconnected from broker (reason: {reason_code})")
    print("⏳ Reconnecting in 5 seconds...")
    time.sleep(5)
    try:
        client.reconnect()
    except Exception as e:
        print(f"❌ Reconnect failed: {str(e)}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        timestamp = payload.get("timestamp", "N/A")
        location = payload.get("location", {})
        lat = location.get("lat", 0)
        lng = location.get("lng", 0)
        count = payload.get("vehicle_count", 0)

        print(f"\n🚗 Vehicle Data Received @ {timestamp}")
        print(f"   → Location: ({lat:.6f}, {lng:.6f})")
        print(f"   → Vehicle Count: {count}")
        print("--------------------------------------------------")

    except json.JSONDecodeError:
        print("❌ JSON Decode Error")
    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.tls_set(
            ca_certs=f"{CERT_PATH}AmazonRootCA1.pem",
            certfile=f"{CERT_PATH}device-certificate.pem.crt",
            keyfile=f"{CERT_PATH}private.pem.key",
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
    except Exception as e:
        print(f"❌ Failed to configure TLS: {str(e)}")
        return

    try:
        print("🔌 Connecting to AWS IoT Core...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return

    print("\n🚀 Fog handler running. Waiting for LoRaWAN messages...")
    print("📴 Press Ctrl+C to stop.\n")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received, disconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"❌ Unexpected error in loop: {str(e)}")

if __name__ == "__main__":
    main()
