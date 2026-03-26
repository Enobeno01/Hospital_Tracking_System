import asyncio
from bleak import BleakScanner
from ble_scanner.mqtt_client import send_tag

seen_devices = set()

def detection_callback(device, advertisement_data):
    device_name = device.name or ""

    if not device_name.startswith("KBPro_"):
        return

    if device.address in seen_devices:
        return

    seen_devices.add(device.address)

    print("-----")
    print("Name:", device.name)
    print("Address:", device.address)
    print("RSSI:", advertisement_data.rssi)

    send_tag(device.address, advertisement_data.rssi)

async def main():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    print("Scanning...")
    await asyncio.sleep(20)
    await scanner.stop()

asyncio.run(main())