import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from renogybt.DeviceEntry import Instance

app = FastAPI()

@app.get("/hello-world")
async def hello_world():
    print("HELLO WORLD")

@app.get("/test-ble-device")
async def test_ble_device():
    try:
        print("Running example script...")
        instance = Instance()
        instance.run()
        
        response = {
            "status_code": 200
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ERROR: {e}")

    return response


# Define the request model
class HexData(BaseModel):
    hex_array: str  # Hexadecimal byte array as a string

@app.post("/process-hex")
async def process_hex(data: HexData):
    # Validate and process the input hex data
    try:
        # Convert the hexadecimal string into a byte array
        byte_array = bytes.fromhex(data.hex_array)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hexadecimal format")
    
    # Example processing (return the length of the byte array)
    response = {
        "byte_array": list(byte_array),
        "length": len(byte_array)
    }

    # Publish the message to the MQTT broker
    try:
        mqtt_payload = {
            "hex_array": data.hex_array,
            "byte_array": list(byte_array),
            "length": len(byte_array)
        }
        print(f"Received BLE payload: {mqtt_payload}")
        # mqtt_client.publish(MQTT_TOPIC, str(mqtt_payload))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to MQTT: {e}")

    return response
