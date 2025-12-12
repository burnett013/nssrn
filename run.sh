#!/bin/bash

# Start the API server in the background
echo "Starting API server on port 8001..."
python3 -m api.main &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start the Streamlit dashboard
echo "Starting Streamlit dashboard..."
streamlit run dashboard.py

# When Streamlit exits, kill the API server
pkill -P $$
