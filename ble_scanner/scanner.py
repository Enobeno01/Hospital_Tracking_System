import asyncio
from bleak import BleakScanner
from ble_scanner.mqtt_client import send_tag
import time

last_seen = {}
SEND_INTERVAL = 1  # sekunder

def detection_callback(device, advertisement_data):
    device_name = device.name or ""

    if not device_name.startswith("KBPro"):
        return

    now = time.time()
    last_time = last_seen.get(device.address, 0)

    if now - last_time < SEND_INTERVAL:
        return

    last_seen[device.address] = now

    print("-----")
    print("Name:", device.name)
    print("Address:", device.address)
    print("RSSI:", advertisement_data.rssi)

    send_tag(device.address, advertisement_data.rssi)

async def main():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    print("Scanning...")

    while True:
        await asyncio.sleep(1)

asyncio.run(main())