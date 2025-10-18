#!/bin/bash
# Start the AI Coding Assistant Client in HTTP/SSE mode
# This connects to a standalone SSE MCP server

echo "🌐 Starting AI Coding Assistant Client (HTTP/SSE Mode)..."
echo ""
echo "MODE: HTTP/SSE (connect to standalone server)"
echo "Make sure the server is running: ./start_server.sh"
echo ""

# Default SSE server URL (must include /sse endpoint)
SERVER_URL="${SERVER_URL:-http://localhost:8000/sse}"

echo "Connecting to: $SERVER_URL"
echo ""

# Start client in HTTP mode
cd mcp-client
python3 client.py --http "$SERVER_URL"
