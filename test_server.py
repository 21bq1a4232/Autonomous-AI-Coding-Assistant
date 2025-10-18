#!/usr/bin/env python3
"""
Test script to verify the MCP server is working
"""

import subprocess
import sys
import os
import json
import time

def test_server():
    """Test if the server starts and responds correctly"""
    print("🧪 Testing MCP Server...")
    
    # Change to server directory
    server_dir = "mcp-server"
    if not os.path.exists(server_dir):
        print("❌ Server directory not found")
        return False
    
    try:
        # Start server in stdio mode
        process = subprocess.Popen(
            [sys.executable, "server.py", "--stdio"],
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "WORKSPACE_PATH": "."}
        )
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Server exited early")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("📤 Sending tools/list request...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Read initialize response first
        try:
            init_response_line = process.stdout.readline()
            if init_response_line:
                init_response = json.loads(init_response_line)
                print(f"✅ Initialize response: {init_response}")
            else:
                print("❌ No initialize response from server")
                return False
        except Exception as e:
            print(f"❌ Error reading initialize response: {e}")
            return False
        
        # Wait for tools response
        time.sleep(2)
        
        # Try to read tools response
        try:
            tools_response_line = process.stdout.readline()
            if tools_response_line:
                tools_response = json.loads(tools_response_line)
                print(f"✅ Tools response: {tools_response}")
                
                if "result" in tools_response:
                    if "tools" in tools_response["result"]:
                        tools = tools_response["result"]["tools"]
                        print(f"✅ Found {len(tools)} tools")
                        for tool in tools:
                            print(f"  - {tool.get('name', 'unknown')}")
                        return True
                    else:
                        print("❌ No tools in result")
                        print(f"Available keys: {list(tools_response['result'].keys())}")
                        return False
                else:
                    print("❌ No result in tools response")
                    return False
            else:
                print("❌ No tools response from server")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading response: {e}")
            return False
        finally:
            process.terminate()
            process.wait()
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    if success:
        print("\n🎉 Server test passed!")
    else:
        print("\n💥 Server test failed!")
        sys.exit(1)
