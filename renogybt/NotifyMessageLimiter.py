import time

# This class is recommended for RNG_SHNT messages 
# because the shunt device spams the connected service
# - see a usage example in DeviceInstance class

class RateLimiter:
    def __init__(self, interval):
        self.interval = interval  # Minimum time (in seconds) between processing
        self.last_processed = 0  # Timestamp of the last processed message

    def should_process(self):
        current_time = time.time()
        if current_time - self.last_processed >= self.interval:
            self.last_processed = current_time
            return True
        return False
