#!/bin/sh
set -e

# Ensure the config directory exists and has correct permissions
CONFIG_DIR="${CONFIG_PATH%/*}"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
fi

# Ensure we can write to the config directory
# This handles both mounted volumes and container-local directories
if [ -d "$CONFIG_DIR" ]; then
    # Test if we can write to the directory
    if ! touch "$CONFIG_DIR/.write_test" 2>/dev/null; then
        echo "Warning: Cannot write to config directory $CONFIG_DIR"
        echo "Config will be stored in memory only"
    else
        rm -f "$CONFIG_DIR/.write_test"
        echo "Config directory $CONFIG_DIR is writable"
    fi
fi

# Execute the main command
exec "$@"