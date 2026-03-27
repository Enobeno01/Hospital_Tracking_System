import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from sqlmodel import Session, select

from database.connection import engine
from backend.models import Asset

BACKEND_URL = "http://127.0.0.1:8000/zone-events"
ZONE_ID = 4
GATEWAY_ID = 1

last_sent = {}
COOLDOWN_SECONDS = 10


def on_connect(client, userdata, flags, rc):
    print("MQTT connected:", rc)
    client.subscribe("ble/tags")


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
client.on_connect = on_connect
client.on_message = on_message


def start():
    print("MQTT STARTAR...")
    client.connect("localhost", 1883, 60)
    client.loop_start()