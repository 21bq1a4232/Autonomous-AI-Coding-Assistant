#!/usr/bin/env python3
"""
Simple test to check if FastMCP server works
"""

import asyncio
import sys
import os
sys.path.append('mcp-server')

from server import mcp

async def test_server():
    """Test the server directly"""
    print("🧪 Testing FastMCP server directly...")
    
    try:
        # Get tools
        tools = await mcp.get_tools()
        print(f"✅ Found {len(tools)} tools:")
        for name, tool in tools.items():
            print(f"  - {name}: {tool.description or 'No description'}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    if success:
        print("\n🎉 Server test passed!")
    else:
        print("\n💥 Server test failed!")
        sys.exit(1)
