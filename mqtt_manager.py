import paho.mqtt.client as mqtt
import logging

class MQTTManager(mqtt.Client):
    def __init__(self, broker, port=1883, client_id="", username=None, password=None, keepalive=60):
         # Create MQTT client instance
        super().__init__(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, reconnect_on_failure=False)
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.subscriptions = {}

        # Set username and password if provided
        if username and password:
            self.username_pw_set(username, password)



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
