import logging
import configparser
import os
import sys
import time
import threading
from dotenv import load_dotenv
from renogybt import BaseClient, InverterClient, RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils

# logging.basicConfig(level=logging.DEBUG)

class DeviceInstance:
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.data_logger: DataLogger = DataLogger(config)
        self.device_inst: RoverClient | InverterClient = None
        self._stop_event = threading.Event()
        self._initialized_event = threading.Event()  # Event to signal device initialization

        
    def stop(self):
        self._stop_event.set()
         # Wait for device initialization if necessary
        if not self._initialized_event.is_set():
            logging.info("Waiting for device initialization to complete...")
            self._initialized_event.wait()
            
        if self.device_inst:
            logging.info(msg=f"Disconnecting from devive '{self.device_inst.manager.mac_address}' ...")
            self.device_inst.disconnect()
        else:
            logging.error(msg="Device instance does not exists. Try connecting the device.")
    
    def run(self):        
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
                logging.info(msg="Enable device polling to continue...")
                # self.stop()

        # error callback
        def on_error(client, error):
            logging.error(f"on_error: {error}")

        # start client
        if self.config['device']['type'] == 'RNG_CTRL':
            self.device_inst = RoverClient(self.config, on_data_received, on_error)
            self._initialized_event.set()  # Signal that the device is ready
            self.device_inst.connect()
        # elif self.config['device']['type'] == 'RNG_CTRL_HIST':
        #     self.device_inst = RoverHistoryClient(self.config, on_data_received, on_error).connect()
        # elif self.config['device']['type'] == 'RNG_BATT':
        #     self.device_inst = BatteryClient(self.config, on_data_received, on_error).connect()
        elif self.config['device']['type'] == 'RNG_INVT':
            self.device_inst = InverterClient(self.config, on_data_received, on_error)
            self._initialized_event.set()  # Signal that the device is ready
            self.device_inst.connect()
        else:
            logging.error("unknown device type")
        
