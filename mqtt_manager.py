import json
import logging
import paho.mqtt.client as mqtt


class MQTTManager:
def __init__(self, broker, port=1883, client_id="", username=None, password=None, keepalive=60, topic_prefix="solar/state"):
    super().__init__(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, reconnect_on_failure=False)
    self.broker = broker
    self.port = port
    self.keepalive = keepalive
    self.topic_prefix = topic_prefix
    self.subscriptions = {}
    self.published_devices = set()

    self.unit_map = {
        "voltage": "V",
        "current": "A",
        "power": "W",
        "state_of_charge": "%",
        "temperature": "°C",
    }

    self.device_class_map = {
        "voltage": "voltage",
        "current": "current",
        "power": "power",
        "state_of_charge": "battery",
        "temperature": "temperature",
    }

    if username and password:
        self.username_pw_set(username, password)

    def connect_to_broker(self):
        logging.info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        self.client.connect(self.broker, self.port, 60)

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def publish_message(self, topic, payload, retain=False):
        logging.debug(f"MQTT publish: {topic} => {payload}")
        self.client.publish(topic, payload, retain=retain)

    def create_mqtt_device(self, device_name, field_name, unit="", device_class="", state_class="measurement"):
        unique_id = f"{device_name}_{field_name}"
        if unique_id in self.published_devices:
            return

        state_topic = f"{self.topic_prefix}/{field_name}/state"
        discovery_topic = f"homeassistant/sensor/{unique_id}/config"

        payload = {
            "name": f"{device_name} {field_name.replace('_', ' ').title()}",
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": {
                "identifiers": [device_name],
                "manufacturer": "Renogy",
                "model": "SmartShunt",
                "name": device_name,
            },
            "unit_of_measurement": unit,
            "value_template": "{{ value_json.value }}",
        }

        if device_class:
            payload["device_class"] = device_class
        if state_class:
            payload["state_class"] = state_class

        self.publish_message(discovery_topic, json.dumps(payload), retain=True)
        self.published_devices.add(unique_id)
