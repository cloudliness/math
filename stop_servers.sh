#!/bin/bash
echo "Stopping MathFlow AI Tutor Servers on ports 8000 and 5173..."

# Force kill processes on specific ports
fuser -k 8000/tcp
fuser -k 5173/tcp

echo "Done."
