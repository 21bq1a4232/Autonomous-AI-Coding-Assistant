#!/usr/bin/env python3
"""Simple HTTP client that connects to MCP server via requests"""

import requests
import json

class SimpleHTTPMCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.request_id = 0

    def call_tool(self, tool_name, arguments):
        """Call a tool via simple HTTP POST"""
        self.request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = requests.post(
            f"{self.base_url}/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        return response.json()

    def list_tools(self):
        """List available tools"""
        self.request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {}
        }

        response = requests.post(
            f"{self.base_url}/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        return response.json()

# Test it
if __name__ == "__main__":
    client = SimpleHTTPMCPClient()

    print("Testing connection to http://localhost:8000")
    print("\n1. Listing tools...")
    tools = client.list_tools()
    print(json.dumps(tools, indent=2))

    print("\n2. Reading a file...")
    result = client.call_tool("read_file", {"path": "README.md"})
    print(json.dumps(result, indent=2)[:500])
