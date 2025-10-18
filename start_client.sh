#!/bin/bash
# Start the AI Coding Assistant Client

echo "🤖 Starting AI Coding Assistant Client..."
echo ""
echo "The client will auto-start the MCP server"
echo "No need to run start_server.sh separately"
echo ""

# Start client
cd mcp-client
python3 client.py
