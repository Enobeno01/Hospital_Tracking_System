import json
import ssl
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session, select

from database.connection import engine
from backend.models import Asset

latest_signals = {}
BACKEND_URL = "http://127.0.0.1:8000/zone-events"

MQTT_HOST = "hospitaltraking-bdc24495.a01.euc1.aws.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "manar"
MQTT_PASSWORD = "Hejhejdu1"
MQTT_TOPIC = "ble/tags"

last_sent = {}
COOLDOWN_SECONDS = 1


def on_connect(client, userdata, flags, rc):
    print("MQTT connected:", rc)
    client.subscribe(MQTT_TOPIC)


def find_asset_by_beacon(tag_id: str):
    with Session(engine) as session:
        statement = select(Asset).where(Asset.beacon_id == tag_id)
        return session.exec(statement).first()


def on_message(client, userdata, msg):
    print("MQTT message received")

    try:
        data = json.loads(msg.payload.decode())
    except Exception:
        print("Invalid JSON")
        return

    print("Data:", data)

    tag_id = data.get("tag_id")
    rssi = data.get("rssi")
    gateway_id = data.get("gateway_id")
    zone_id = data.get("zone_id")

    if not gateway_id:
        print("Missing gateway_id")
        return

    if zone_id is None:
        print("Missing zone_id")
        return

    if tag_id not in latest_signals:
        latest_signals[tag_id] = {}

    latest_signals[tag_id][gateway_id] = {
        "rssi": rssi,
        "zone_id": zone_id
    }

    best_gateway = max(
        latest_signals[tag_id],
        key=lambda gw: latest_signals[tag_id][gw]["rssi"]
    )

    print(f"Best gateway for {tag_id}: {best_gateway}")

    if gateway_id != best_gateway:
        print("Skipping weaker signal")
        return

    asset = find_asset_by_beacon(tag_id)

    if not asset:
        print("Unknown beacon:", tag_id)
        return

    now = datetime.utcnow()
    last_time = last_sent.get(tag_id)

    if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
        print(f"Skipping duplicate for {asset.asset_id}")
        return

    best_zone_id = latest_signals[tag_id][best_gateway]["zone_id"]

    payload = {
        "asset_id": asset.asset_id,
        "zone_id": best_zone_id,
        "gateway_id": gateway_id
    }

    try:
        res = requests.post(BACKEND_URL, json=payload)
        print("Zone event sent:", res.status_code)

        if res.ok:
            last_sent[tag_id] = now

    except Exception as e:
        print("Failed to send zone event:", e)


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
client.on_connect = on_connect
client.on_message = on_message


def start():
    print("MQTT STARTAR...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()