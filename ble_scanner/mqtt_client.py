import json
import ssl
import paho.mqtt.client as mqtt

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
        "rssi": rssi
    }
    client.publish(MQTT_TOPIC, json.dumps(payload))