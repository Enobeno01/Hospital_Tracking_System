import asyncio
from bleak import BleakScanner

def detection_callback(device, advertisement_data):
    print("-----")
    print("Name:", device.name)
    print("Address/UUID:", device.address)
    print("RSSI:", advertisement_data.rssi)
    print("Local name:", advertisement_data.local_name)
    print("Service UUIDs:", advertisement_data.service_uuids)
    print("Manufacturer data:", advertisement_data.manufacturer_data)
    print("Service data:", advertisement_data.service_data)

async def main():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()

asyncio.run(main())