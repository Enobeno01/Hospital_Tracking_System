import json
import ssl
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session, select

from database.connection import engine
from backend.models import Asset

BACKEND_URL = "http://127.0.0.1:8000/zone-events"
ZONE_ID = 3
GATEWAY_ID = 1

MQTT_HOST = "hospitaltraking-bdc24495.a01.euc1.aws.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "manar"
MQTT_PASSWORD = "Hejhejdu1"
MQTT_TOPIC = "ble/tags"

last_sent = {}
COOLDOWN_SECONDS = 10


def on_connect(client, userdata, flags, rc):
    print("MQTT connected:", rc)
    client.subscribe(MQTT_TOPIC)


def find_asset_by_beacon(tag_id: str):
    with Session(engine) as session:
        statement = select(Asset).where(Asset.beacon_id == tag_id)
        return session.exec(statement).first()


def on_message(client, userdata, msg):
    print("MQTT message received")

    data = json.loads(msg.payload.decode())
    print("Data:", data)

    tag_id = data.get("tag_id")
    rssi = data.get("rssi")

    asset = find_asset_by_beacon(tag_id)

    if not asset:
        print("Unknown beacon:", tag_id)
        return

    now = datetime.utcnow()
    last_time = last_sent.get(tag_id)

    if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
        print(f"Skipping duplicate for {asset.asset_id}")
        return

    payload = {
        "asset_id": asset.asset_id,
        "zone_id": ZONE_ID,
        "gateway_id": GATEWAY_ID
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