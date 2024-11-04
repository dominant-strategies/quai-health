#!/bin/bash

# Default port and health status
PORT=80
HEALTHY=true

# Parse flags
while getopts ":p:" opt; do
  case ${opt} in
    p )
      PORT=$OPTARG
      ;;
    \? )
      echo "Usage: $0 [-p port]"
      exit 1
      ;;
  esac
done

# Export environment variables
export PORT="$PORT"
export HEALTHY="$HEALTHY"

# Start Gunicorn with Flask app on specified port
echo "Starting health check server on port $PORT with HEALTHY=$HEALTHY using Gunicorn"
gunicorn -w 4 -b 0.0.0.0:$PORT flask_app:app --timeout 60

