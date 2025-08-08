# fog_handler.py
# Real-time LoRaWAN MQTT listener with WebSocket dashboard

from flask import Flask, jsonify, render_template
from threading import Thread
import socketio
import paho.mqtt.client as mqtt
import json
import time
from threading import Thread, Lock
import ssl
import os
import urllib.request

# MQTT Configuration
MQTT_BROKER = "a3hyjp4joybycm-ats.iot.us-east-1.amazonaws.com"
MQTT_PORT = 8883
TOPIC = "lorawan/traffic"
ALERT_TOPIC = "lorawan/alerts"
CERT_PATH = "certs/"

# Data storage
message_history = []
gateways_seen = set()
data_lock = Lock()

# Initialize Flask and Socket.IO
app = Flask(__name__)
sio = socketio.Server(async_mode='threading', cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Socket.IO Event Handlers
@sio.event
def connect(sid, environ):
    print(f"📡 Client connected: {sid}")
    with data_lock:
        # Send initial data to new client
        sio.emit('init', {
            'messages': message_history[-25:],
            'gateways': sorted(list(gateways_seen))
        }, room=sid)

@sio.event
def disconnect(sid):
    print(f"📡 Client disconnected: {sid}")

# Helper Functions
def classify_traffic(vehicle_count):
    """Classify traffic level based on vehicle count"""
    if vehicle_count < 5:
        return "LOW"
    elif 5 <= vehicle_count < 15:
        return "MEDIUM"
    else:
        return "HEAVY"

def get_cloud9_preview_url(port=8080):
    try:
        hostname = urllib.request.urlopen(
            "http://169.254.169.254/latest/meta-data/public-hostname", 
            timeout=1
        ).read().decode("utf-8").strip()
        az = urllib.request.urlopen(
            "http://169.254.169.254/latest/meta-data/placement/availability-zone", 
            timeout=1
        ).read().decode("utf-8").strip()
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or az[:-1]
        cloud9_id = hostname.split(".")[0]
        return f"https://{cloud9_id}.vfs.cloud9.{region}.amazonaws.com/"
    except Exception:
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
        return f"https://{region}.console.aws.amazon.com/cloud9"

# Flask Routes
@app.route("/")
def dashboard():
    with data_lock:
        return render_template("dashboard.html",
                            messages=message_history[-25:],
                            gateways=sorted(list(gateways_seen)),
                            status="Fog handler is running")

@app.route("/data")
def get_data():
    return jsonify(message_history[-25:])

@app.route("/gateways")
def get_gateways():
    return jsonify(sorted(list(gateways_seen)))

# MQTT Callbacks
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
        print(f"📩 Raw MQTT payload: {payload}")  # Debug log
        
        timestamp = payload.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        location = payload.get("location", {})
        lat = location.get("lat", 0.0)
        lng = location.get("lng", 0.0)
        count = int(payload.get("vehicle_count", 0))
        gateway = payload.get("gateway_id", "unknown")
        level = classify_traffic(count)

        # Print to console
        level_emoji = {"LOW":"🟢", "MEDIUM":"🟠", "HEAVY":"🔴"}[level]
        print(f"\n🚗 Vehicle Data @ {timestamp}")
        print(f"   → Location: ({lat:.6f}, {lng:.6f})")
        print(f"   → Vehicles: {count}")
        print(f"   → Gateway: {gateway}")
        print(f"   → Traffic: {level_emoji} {level}")
        print("--------------------------------------------------")

        # Update data and emit
        with data_lock:
            gateways_seen.add(gateway)
            message_history.append({
                "timestamp": timestamp,
                "lat": lat,
                "lng": lng,
                "vehicle_count": count,
                "gateway": gateway,
                "traffic_level": level
            })
            if len(message_history) > 100:
                message_history.pop(0)

            # Emit update to all clients
            sio.emit('update', {
                'lat': lat,
                'lng': lng,
                'vehicle_count': count,
                'traffic_level': level,
                'gateway': gateway,
                'timestamp': timestamp
            })
            print(f"📢 Emitted update for gateway {gateway}")

        # Publish alerts if needed
        if level in ("MEDIUM", "HEAVY"):
            alert = {
                "timestamp": timestamp,
                "gateway_id": gateway,
                "vehicle_count": count,
                "traffic_level": level,
                "location": {"lat": lat, "lng": lng}
            }
            client.publish(ALERT_TOPIC, json.dumps(alert))
            print(f"🚨 Published alert for {gateway}")

    except json.JSONDecodeError:
        print("❌ Failed to decode JSON payload")
    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")

def run_flask():
    url = get_cloud9_preview_url(port=8080)
    print("\n🌐 Dashboard URL:")
    print(url)
    print("ℹ️ If it 404s, use Cloud9 menu: Preview → Preview Running Application\n")
    app.run(host="0.0.0.0", port=8080)

def main():
    # Configure MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        # Set up TLS
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
    print("📴 Press Ctrl+C to stop\n")

    # Start Flask in a separate thread
    Thread(target=run_flask, daemon=True).start()

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received, disconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()