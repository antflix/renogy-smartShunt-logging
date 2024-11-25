import logging
import configparser
import os
import sys
import time
from dotenv import load_dotenv
from renogybt import InverterClient, RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils

logging.basicConfig(level=logging.DEBUG)

class Instance:
    def __init__(self):
        self.is_local_config = False
        self.config = configparser.ConfigParser()
        self.data_logger = None
    
    ## ensures the existing code base receives a ConfigParser object ##
    def check_config_source(self):
        ## Load the .env file
        load_dotenv()
        
        ## Start checking config source
        USE_LOCAL_CONFIG = bool(os.getenv('USE_LOCAL_CONFIG', 'false').lower() in ('true', '1'))
        if not USE_LOCAL_CONFIG:
            config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
            # config_path = "./config.ini"
            self.config = configparser.ConfigParser(inline_comment_prefixes=('#'))
            self.config.read(config_path)
        else: ## Use environment variables or default values to populate the ConfigParser object
            ## Device
            self.config['device'] = {
                'adapter': os.getenv('DEVICE_ADAPTER', ''),
                'mac_address': os.getenv('DEVICE_MAC_ADDRESS', ''),
                'alias': os.getenv('DEVICE_ALIAS', ''),
                'type': os.getenv('DEVICE_TYPE', 'RNG_CTRL'),
                'id': os.getenv('DEVICE_ID', '255')
            }
            ## Data
            self.config['data'] = {
                'polling_enabled': os.getenv('DATA_POLLING_ENABLED', 'false'),
                'poll_interval': os.getenv('DATA_POLL_INTERVAL', '20'),
                'temp_unit': os.getenv('DATA_TEMP_UNIT', 'F'),
                'fields': os.getenv('DATA_FIELDS', '')
            }
            ## Remote logging
            self.config['remote_logging'] = {
                'log_enabled': os.getenv('REMOTE_LOG_ENABLED', 'false'),
                'url': os.getenv('REMOTE_URL', ''),
                'auth_header': os.getenv('REMOTE_AUTH_HEADER', '')
            }
            ## MQTT
            self.config['mqtt'] = {
                'enabled': os.getenv('MQTT_ENABLED', 'false'),
                'server': os.getenv('MQTT_SERVER', ''),
                'port': os.getenv('MQTT_PORT', '1883'),
                'topic': os.getenv('MQTT_TOPIC', 'solar/state'),
                'user': os.getenv('MQTT_USER', ''),
                'password': os.getenv('MQTT_PASSWORD', '')
            }
            ## PVOutput
            self.config['pvoutput'] = {
                'enabled': os.getenv('PVOUT_ENABLED', 'false'),
                'apikey': os.getenv('PVOUT_APIKEY', ''),
                'sysid': os.getenv('PVOUT_SYSID', '')
            }

        self.data_logger: DataLogger = DataLogger(self.config)
        
    
    def run(self):
        self.check_config_source()
        time.sleep(1)
        
        # the callback func when you receive data
        def on_data_received(client, data):
            filtered_data = Utils.filter_fields(data, self.config['data']['fields'])
            logging.debug("{} => {}".format(client.device.alias(), filtered_data))
            if self.config['remote_logging'].getboolean('enabled'):
                self.data_logger.log_remote(json_data=filtered_data)
            if self.config['mqtt'].getboolean('enabled'):
                self.data_logger.log_mqtt(json_data=filtered_data)
            if self.config['pvoutput'].getboolean('enabled') and self.config['device']['type'] == 'RNG_CTRL':
                self.data_logger.log_pvoutput(json_data=filtered_data)
            if not self.config['data'].getboolean('enable_polling'):
                client.disconnect()

        # error callback
        def on_error(client, error):
            logging.error(f"on_error: {error}")

        # start client
        if self.config['device']['type'] == 'RNG_CTRL':
            RoverClient(self.config, on_data_received, on_error).connect()
        elif self.config['device']['type'] == 'RNG_CTRL_HIST':
            RoverHistoryClient(self.config, on_data_received, on_error).connect()
        elif self.config['device']['type'] == 'RNG_BATT':
            BatteryClient(self.config, on_data_received, on_error).connect()
        elif self.config['device']['type'] == 'RNG_INVT':
            InverterClient(self.config, on_data_received, on_error).connect()
        else:
            logging.error("unknown device type")
