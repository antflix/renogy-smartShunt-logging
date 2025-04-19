import re

filename = "DataLogger.py"
backup = filename + ".bak"

# Read original file
with open(filename, "r") as f:
    original = f.read()

# Backup original
with open(backup, "w") as f:
    f.write(original)

# Define the fixed function body
new_log_mqtt = '''
    def log_mqtt(self, json_data):
        logging.info(f"mqtt logging {json.dumps(json_data)}")
        user = self.config['mqtt']['user']
        password = self.config['mqtt']['password']
        auth = None if not user or not password else {"username": user, "password": password}
        base_topic = self.config['mqtt']['topic']

        for key, value in json_data.items():
            topic = f"{base_topic}/{key}/state"
            publish.single(
                topic=topic,
                payload=str(value),
                hostname=self.config['mqtt']['server'],
                port=self.config['mqtt'].getint('port'),
                auth=auth,
                client_id=self.config['mqtt']['client_id'],
                retain=True
            )
'''

# Replace the existing log_mqtt function
new_code = re.sub(
    r"def log_mqtt\(self, json_data\):[\s\S]+?(?=\n\s+def|\Z)",
    new_log_mqtt.strip(),
    original
)

# Write updated version
with open(filename, "w") as f:
    f.write(new_code)

print(f"✅ log_mqtt() updated in {filename}. Backup saved to {backup}")
