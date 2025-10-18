#!/bin/bash
# Start the AI Coding Assistant Client

echo "🤖 Starting AI Coding Assistant Client..."
echo ""
echo "Make sure the MCP server is running first!"
echo "If not, run: ./start_server.sh"
echo ""

# Set MCP server URL if not set
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8000}"

# Start client
cd mcp-client
python3 client.py
