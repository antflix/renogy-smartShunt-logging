#!/bin/bash
# filepath: /Users/admin/renogy-data-capture/retry_device_id.sh

# Loop device_id values from 0 to 255
for id in {0..255}; do
    echo "Trying device_id: $id..."
    
    # Update the device_id value in config.ini.
    # This creates a backup file named config.ini.bak.
    sed -i.bak -E "s/^(device_id\s*=\s*).*/\1$id/" config.ini
    
    # Run the example.py script with the updated config.ini
    python3 ./example.py config.ini
    RESULT=$?
    
    if [ $RESULT -eq 0 ]; then
        echo "Success: device_id set to $id"
        exit 0
    else
        echo "Script failed with device_id: $id (exit code $RESULT). Retrying with next value..."
    fi

    # Optionally pause before next attempt
    sleep 5
done

echo "No successful device_id found."
exit 1
