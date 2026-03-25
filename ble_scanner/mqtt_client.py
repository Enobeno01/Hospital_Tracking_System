# ble_scanner/mqtt_client.py
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883, 60)

def send_tag(tag_id, rssi):
    payload = {
        "tag_id": tag_id,
        "rssi": rssi
    }
    client.publish("ble/tags", json.dumps(payload))