#!/bin/bash
 
export PATH="$PATH:/home/labuser/.local/bin"
set -e
 
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$BASE_DIR"
 
echo "Starting EXLPlain application..."

echo "Installing dependencies..."
pip install -r "$BASE_DIR/requirements.txt"

echo "Starting Frontend..."
cd "$FRONTEND_DIR"
streamlit run app.py &
FRONTEND_PID=$!
 
echo "Frontend PID: $FRONTEND_PID"
trap "echo ' Stopping both...'; kill  $FRONTEND_PID" SIGINT
wait
