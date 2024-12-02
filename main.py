import time
import os
import sys
import threading
import logging
import configparser
from dotenv import load_dotenv
from mqtt_manager import MQTTManager
from renogybt import DataLogger
from renogybt.DeviceEntry import DeviceInstance

# logging.basicConfig(
#     stream=sys.stdout,  # Log to stdout
#     level=logging.INFO,  # Set log level
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )
logging.basicConfig(level=logging.DEBUG)

## Load the .env file
dotenv_loaded = load_dotenv()

## Configuration from env or ini
config = configparser.ConfigParser(inline_comment_prefixes=('#'))
# data_logger: DataLogger = None

## Device Instance to start and stop
listener_thread: threading.Thread = None
device_instance: DeviceInstance = None

def check_config_source():
    ## Start checking config source
    use_docker_config = os.getenv('USE_DOCKER_CONFIG', 'false')
    USE_DOCKER_CONFIG = bool(use_docker_config.lower() in ('true', '1'))
    # print("USE DOCKER", USE_DOCKER_CONFIG)
    if not USE_DOCKER_CONFIG:
        logging.info(msg="Loading config.ini...")
        config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
        # config_path = "./config.ini"
        config.read(config_path)
    else: ## Use environment variables or default values to populate the ConfigParser object
        logging.info(msg="Loading .env...")
        ## Device
        config['device'] = {
            'adapter': os.getenv('DEVICE_ADAPTER', ''),
            'mac_addr': os.getenv('DEVICE_MAC_ADDRESS', ''),
            'alias': os.getenv('DEVICE_ALIAS', ''),
            'type': os.getenv('DEVICE_TYPE', 'RNG_CTRL'),
            'device_id': os.getenv('DEVICE_ID', '255')
        }
        ## Data
        config['data'] = {
            'enable_polling': os.getenv('DATA_POLLING_ENABLED', 'false'),
            'poll_interval': os.getenv('DATA_POLL_INTERVAL', '20'),
            'temperature_unit': os.getenv('DATA_TEMP_UNIT', 'F'),
            'fields': os.getenv('DATA_FIELDS', ''),
            'enable_rate_limiter': os.getenv('DATA_RATE_LIMIT_ENABLED', 'false'),
            'rate_interval': os.getenv('DATA_RATE_INTERVAL', '10'),
        }
        ## Remote logging
        config['remote_logging'] = {
            'enabled': os.getenv('REMOTE_LOG_ENABLED', 'false'),
            'url': os.getenv('REMOTE_URL', ''),
            'auth_header': os.getenv('REMOTE_AUTH_HEADER', '')
        }
        ## MQTT
        config['mqtt'] = {
            'enabled': os.getenv('MQTT_ENABLED', 'false'),
            'client_id': os.getenv('MQTT_CLIENT_ID', 'renogy-bt'),
            'server': os.getenv('MQTT_SERVER', ''),
            'port': os.getenv('MQTT_PORT', '1883'),
            'topic': os.getenv('MQTT_PUBLISH_TOPIC', ''),
            'user': os.getenv('MQTT_USER', ''),
            'password': os.getenv('MQTT_PASSWORD', '')
        }
        ## PVOutput
        config['pvoutput'] = {
            'enabled': os.getenv('PVOUT_ENABLED', 'false'),
            'api_key': os.getenv('PVOUT_APIKEY', ''),
            'system_id': os.getenv('PVOUT_SYSID', '')
        }
        
    for section in config.sections():
        logging.info(msg=f'[{section}]')
        for key, value in config.items(section):
            logging.info(msg=f'{key} = {value}')
        logging.info(msg="")
    data_logger: DataLogger = DataLogger(config)
    return data_logger
        
def handle_smart_shunt_msg(topic, message):
    logging.info(msg=f"Handler for topic: {topic} -> {message}")

def handle_ble_connect_msg(topic, message):
    global device_instance, listener_thread  # Declare globals
    logging.info(msg=f"Handler for topic: {topic} -> {message}")
    
    # Check if a listener is already running
    if device_instance is not None and listener_thread is not None:
        if listener_thread.is_alive():
            logging.info("Device instance is already running.")
            return
    
    # Create a new device instance and thread
    device_instance = DeviceInstance(config)
    listener_thread = threading.Thread(name="device_inst_thread", target=device_instance.run)
    listener_thread.start()
    logging.info("Device instance started.")

def handle_ble_disconnect_msg(topic, message):
    global device_instance, listener_thread  # Declare globals
    logging.info(msg=f"*****Handler for topic: {topic} -> {message} -> {device_instance.device_inst}******")
    
    if device_instance and listener_thread:
        if listener_thread.is_alive():
            # Stop the device instance and wait for the thread to finish
            device_instance.stop()
            listener_thread.join()
            device_instance = None
            listener_thread = None
            logging.info("Device instance stopped.")
    else:
        logging.info("No active device instance to stop.")


def main():
    try:
        data_logger = check_config_source()
        config = data_logger.config
        if not config['mqtt'].getboolean('enabled'):
            logging.error(msg="Please enable MQTT config settings...")
            return

        # Initialize MQTTManager
        mqtt_manager_inst = MQTTManager(
            client_id=config['mqtt']['client_id'], 
            broker=config['mqtt']['server'], 
            port=config['mqtt'].getint('port'),
            username=config['mqtt']['user'],
            password=config['mqtt']['password'])
        
        ## Connect to the MQTT broker
        mqtt_manager_inst.connect_to_broker()
        
        ## Setup device interface topics
        # mqtt_manager_inst.subscribe_to_topic(topic="process/smartshunt/data", on_message_callback=handle_smart_shunt_msg)
        mqtt_manager_inst.subscribe_to_topic(topic=f"renogy-ble/start/{config['device']['mac_addr'].lower()}", on_message_callback=handle_ble_connect_msg)
        mqtt_manager_inst.subscribe_to_topic(topic=f"renogy-ble/stop/{config['device']['mac_addr'].lower()}", on_message_callback=handle_ble_disconnect_msg)
        
        ## Start the service
        logging.info(msg="Waiting for messages...")
        mqtt_manager_inst.start()
        
        # logging.info(msg=f"Waiting for messages... {mqtt_manager_inst.is_connected()}")
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logging.info(msg="Exiting...")
    except Exception as e:
        logging.error(msg=f"An error occurred: {e}")
    
    ## Handle disconnect
    if mqtt_manager_inst.is_connected():
        mqtt_manager_inst.stop()
        

if __name__ == "__main__":
    main()