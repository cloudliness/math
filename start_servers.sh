#!/bin/bash
echo "Starting MathFlow AI Tutor Servers..."

# Start Backend in background
(
  echo "Starting Backend..."
  source venv/bin/activate
  cd backend
  python3 -m app.main
) &

# Start Frontend in background
(
  echo "Starting Frontend..."
  cd frontend
  npm run dev
) &

echo "Servers are starting in the background."
echo "Press Ctrl+C to exit this script (servers will keep running in background)."
echo "Use ./stop_servers.sh to stop them."
wait
