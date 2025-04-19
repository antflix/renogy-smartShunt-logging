#!/bin/bash
# filepath: /Users/admin/renogy-data-capture/retry_device_id.sh

# Loop device_id values from 0 to 255 (adjust as needed)
for id in {0..255}
do
    echo "Trying device_id: $id..."
    # Update config.ini by replacing the device_id line.
    sed -i.bak -E "s/^(device_id\s*=\s*).*/\1$id/" config.ini

    # Run the example.py script
    python3 ./example.py config.ini
    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        echo "Success: device_id set to $id"
        exit 0
    else
        echo "Failed with device_id: $id"
    fi
    # Optionally adjust the pause between attempts.
    sleep 5
done

echo "No successful device_id found."
