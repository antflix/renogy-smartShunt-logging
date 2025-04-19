import paho.mqtt.client as mqtt
import logging
import json
class MQTTManager(mqtt.Client):
    def __init__(self, broker, port=1883, client_id="", username=None, password=None, keepalive=60):
         # Create MQTT client instance
        super().__init__(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, reconnect_on_failure=False)
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.subscriptions = {}
        self.published_devices = set()
        # Set username and password if provided
        if username and password:
            self.username_pw_set(username, password)

    def create_mqtt_device(self, device_name: str, field_name: str, unit: str = "", device_class: str = "", state_class: str = "measurement"):
        unique_id = f"{device_name}_{field_name}"
        discovery_topic = f"homeassistant/sensor/{unique_id}/config"
        state_topic = f"{self.topic_prefix}/{device_name}/{field_name}/state"

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

        self.publish(discovery_topic, json.dumps(payload), retain=True)
        self.published_devices.add(unique_id)

    def publish_telemetry(self, device_name, telemetry: dict):
        for field, value in telemetry.items():
            unique_id = f"{device_name}_{field}"
            if unique_id not in self.published_devices:
                unit = self.unit_map.get(field, "")
                device_class = self.device_class_map.get(field, "")
                self.create_mqtt_device(device_name, field, unit, device_class)

            topic = f"{self.topic_prefix}/{device_name}/{field}/state"
            self.publish(topic, json.dumps({"value": value}))
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """
        Callback triggered when the client connects to the broker.
        """
        if rc == 0:
            logging.info(msg="Connected to MQTT Broker!")
        else:
            logging.error(msg=f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, userdata, disconnect_flags, reason, properties=None):
        """
        Callback triggered when the client disconnects.
        """
        logging.info(msg="Disconnected from MQTT Broker")

    def on_message(self, client, userdata, msg, properties=None):
        """
        Callback triggered when a message is received.
        """
        logging.info(msg=f"Message received: {msg.payload.decode()} from topic: {msg.topic}")
        if msg.topic in self.subscriptions:
            self.subscriptions[msg.topic](msg.topic, msg.payload.decode())

    def connect_to_broker(self):
        logging.info(msg="Connecting to broker...")
        error_code = self.connect(host=self.broker, port=self.port, keepalive=self.keepalive)
        logging.info(msg=f" - {error_code}")

    def subscribe_to_topic(self, topic, on_message_callback=None, qos=0):
        self.subscribe(topic=topic, qos=qos)
        logging.info(msg=f"Subscribed to topic: {topic}")
        if on_message_callback:
            self.subscriptions[topic] = on_message_callback

    def publish_message(self, topic, payload, qos=0, retain=True):
        logging.info(msg=f"Publishing to topic: {topic}")
        self.publish(topic=topic, payload=payload, qos=qos, retain=retain)
        logging.info(msg=f"Published message: {payload} to topic: {topic}")

    def start(self):
        logging.info(msg="Starting MQTT client...")
        error_code = self.loop_start()
        logging.info(msg=f" - {error_code}")

    def stop(self):
        logging.info(msg="Stopping service.")
        self.loop_stop()
        self.disconnect()
