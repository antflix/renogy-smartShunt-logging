#!/bin/bash
BROKER="10.0.0.195"
USER="ant"
PASS="Ameo1988!"

echo "Collecting retained MQTT topics..."
mosquitto_sub -h "$BROKER" -u "$USER" -P "$PASS" -t "#" --retained-only -v -C 1000 | \
while read -r line; do
  topic=$(echo "$line" | awk '{print $1}')
  echo "Clearing: $topic"
  mosquitto_pub -h "$BROKER" -u "$USER" -P "$PASS" -t "$topic" -n -r
done

echo "✅ All retained topics cleared."
