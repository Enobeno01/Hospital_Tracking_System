import json
import ssl
import paho.mqtt.client as mqtt

GATEWAY_ID = 1
ZONE_ID = 5

MQTT_HOST = "hospitaltraking-bdc24495.a01.euc1.aws.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "manar"
MQTT_PASSWORD = "Hejhejdu1"
MQTT_TOPIC = "ble/tags"

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()


def send_tag(tag_id, rssi):
    payload = {
        "tag_id": tag_id,
        "rssi": rssi,
        "gateway_id": GATEWAY_ID,
        "zone_id": ZONE_ID
    }

    print("Publishing:", payload)

    client.publish(MQTT_TOPIC, json.dumps(payload))