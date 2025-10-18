#!/bin/bash
# Start the AI Coding Assistant Client

echo "🤖 Starting AI Coding Assistant Client..."
echo ""
echo "MODE: Stdio (auto-start server)"
echo "The client will auto-start the MCP server as a subprocess"
echo ""
echo "To connect to a standalone SSE server instead:"
echo "  python3 mcp-client/client.py --http http://localhost:8000/sse"
echo ""

# Start client in stdio mode (default)
cd mcp-client
python3 client.py
