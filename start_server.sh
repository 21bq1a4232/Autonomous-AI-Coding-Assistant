#!/bin/bash
# Start the MCP Server in SSE mode (optional, for testing)

echo "🚀 Starting MCP Server in SSE mode..."
echo "📡 Server will be available at http://localhost:8000"
echo "📡 SSE endpoint: http://localhost:8000/sse"
echo ""
echo "Note: Client auto-starts server in stdio mode by default"
echo "This script is for manual testing only"
echo ""

# Set workspace if not set
export WORKSPACE_PATH="${WORKSPACE_PATH:-$(pwd)}"

# Start server in SSE mode
cd mcp-server
python3 server.py --sse
