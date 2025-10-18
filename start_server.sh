#!/bin/bash
# Start the MCP Server

echo "🚀 Starting MCP Server..."
echo "📡 Server will be available at http://localhost:8000"
echo "📡 SSE endpoint: http://localhost:8000/sse"
echo ""

# Set workspace if not set
export WORKSPACE_PATH="${WORKSPACE_PATH:-$(pwd)}"

# Start server
cd mcp-server
python3 server.py
