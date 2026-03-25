import json
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe("ble/tags")
    print("Subscribed to ble/tags")

def on_message(client, userdata, msg):
    print("MESSAGE ARRIVED")
    print("Topic:", msg.topic)
    print("Raw:", msg.payload)
    data = json.loads(msg.payload.decode())
    print("Received:", data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

def start():
    print("MQTT STARTAR...")
    client.connect("localhost", 1883, 60)
    client.loop_start()