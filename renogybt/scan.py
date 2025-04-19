import asyncio
from bleak import BleakClient, BleakScanner

async def run():
    print("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover()
    for i, d in enumerate(devices, start=1):
        print(f"{i}. {d.name} [{d.address}]")

    device_address = input("Enter the Bluetooth device address to connect: ").strip()
    print(f"Connecting to {device_address}...")
    async with BleakClient(device_address) as client:
        is_connected = client.is_connected
        print(f"Connected: {is_connected}")
        
        services = client.services
        print("Discovered Services:")
        for service in services:
            print(f"Service {service.uuid} ({service.description}):")
            for char in service.characteristics:
                print(f"  Characteristic {char.uuid} ({char.description})")
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        print(f"    Value: {value}")
                    except Exception as e:
                        print(f"    Could not read value: {e}")

if __name__ == "__main__":
    asyncio.run(run())
