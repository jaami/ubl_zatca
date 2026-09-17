#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Set up environment variables for Fatoora SDK
export FATOORA_HOME=/app/ZatcaSDK/Apps
export SDK_CONFIG=/app/ZatcaSDK/Configuration/config.json
export PATH="$PATH:$FATOORA_HOME"

# Log environment variables for debugging
echo "Environment Variables:"
echo "======================"
echo "FATOORA_HOME: $FATOORA_HOME"
echo "SDK_CONFIG: $SDK_CONFIG"
echo "PATH: $PATH"

# Check if the SDK_CONFIG file exists
if [ ! -f "$SDK_CONFIG" ]; then
    echo "Error: SDK_CONFIG file not found at $SDK_CONFIG"
    exit 1
fi

# Change to the application directory
echo "Changing directory to /app"
cd /app || { echo "Failed to change directory to /app"; exit 1; }

# Check if ZatcaSDK directory exists
if [ ! -d "/app/ZatcaSDK" ]; then
    echo "Error: /app/ZatcaSDK directory not found"
    exit 1
fi

echo "Changing directory to /app/ZatcaSDK"
cd /app/ZatcaSDK || exit 1

# Check if install.sh exists
if [ ! -f "./install.sh" ]; then
    echo "Error: install.sh not found in /app/ZatcaSDK"
    exit 1
fi

echo "Running installation script"
./install.sh || { echo "install.sh failed"; exit 1; }
echo "install.sh completed successfully"

# Change back to /app directory before starting Flask application
echo "Changing directory back to /app"
cd /app || exit 1  # Exit if cd fails

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found in /app"
    exit 1
fi

# Start the Flask application
echo "Starting Flask application"
exec python app.py  # or exec python3 app.py if using Python 3
