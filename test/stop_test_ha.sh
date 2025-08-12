#!/bin/bash

# Stop Test Home Assistant Environment

cd "$(dirname "$0")"

echo "Stopping Home Assistant test environment..."
docker-compose down

echo "Test environment stopped."