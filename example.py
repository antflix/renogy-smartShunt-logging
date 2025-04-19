
import logging
import configparser
import os
import sys
import time
from renogybt import ShuntClient, InverterClient, RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils
from mqtt_manager import MQTTManager

# Logging setup
logging.basicConfig(level=logging.DEBUG)

# Load config
config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
config = configparser.ConfigParser(inline_comment_prefixes=('#'))
config.read(config_path)
data_logger: DataLogger = DataLogger(config)

# MQTT Setup
MQTT_BROKER = config['mqtt']['server']
MQTT_PORT = config.getint('mqtt', 'port', fallback=1883)
MQTT_USER = config['mqtt'].get('user')
MQTT_PASS = config['mqtt'].get('password')
MQTT_TOPIC_PREFIX = config['mqtt'].get('topic', fallback="solar/state")

mqttc = MQTTManager(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USER,
    password=MQTT_PASS
)
mqttc.connect_to_broker()
mqttc.start()

# Polling interval limiter
last_mqtt_publish = 0

def on_data_received(client, data):
    global last_mqtt_publish
    now = time.time()
    poll_interval = config['data'].getint('poll_interval', fallback=60)

    if now - last_mqtt_publish < poll_interval:
        return
    last_mqtt_publish = now

    filtered_data = Utils.filter_fields(data, config['data']['fields'])
    device_name = client.device.alias()
    logging.debug(f"{device_name} => {filtered_data}")

    # Publish to MQTT
    if config['mqtt'].getboolean('enabled'):
        for key, value in filtered_data.items():
            sensor_id = f"{device_name}_{key}"

            if sensor_id not in mqttc.published_devices:
                mqttc.create_mqtt_device(device_name=device_name, field_name=key)

            topic = f"{MQTT_TOPIC_PREFIX}/{key}/state"
            mqttc.publish_message(topic=topic, payload=json.dumps({"value": value}), retain=True)

    # Optional: log to remote or pvoutput
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=filtered_data)

    if config['pvoutput'].getboolean('enabled') and config['device']['type'] == 'RNG_CTRL':
        data_logger.log_pvoutput(json_data=filtered_data)

    if not config['data'].getboolean('enable_polling'):
        client.disconnect()
def on_error(client, error):
    logging.error(f"on_error: {error}")

# Start correct client based on config
device_type = config['device']['type']
if device_type == 'RNG_CTRL':
    RoverClient(config, on_data_received, on_error).connect()
elif device_type == 'RNG_CTRL_HIST':
    RoverHistoryClient(config, on_data_received, on_error).connect()
elif device_type == 'RNG_BATT':
    BatteryClient(config, on_data_received, on_error).connect()
elif device_type == 'RNG_INVT':
    InverterClient(config, on_data_received, on_error).connect()
elif device_type == 'RNG_SHNT':
    ShuntClient(config, on_data_received, on_error).connect()
else:
    logging.error("unknown device type")
