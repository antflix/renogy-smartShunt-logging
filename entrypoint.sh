#!/bin/bash

# Use host's DBus socket if available
if [ -e /run/dbus/system_bus_socket ]; then
  echo "Using host's DBus socket."
else
  echo "Starting dbus-daemon..."
  dbus-daemon --system --nofork &
fi

echo "Starting bluetoothd service..."
/usr/libexec/bluetooth/bluetoothd --debug &

exec /usr/local/bin/python /app/main.py