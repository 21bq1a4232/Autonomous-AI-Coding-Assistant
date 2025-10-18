# Connection Modes - Autonomous AI Coding Assistant

This AI Coding Assistant supports **two connection modes** between the client and MCP server:

## 1. Stdio Mode (Default) - Auto-Start Server

**How it works:**
- Client automatically starts the MCP server as a subprocess
- Communication happens via stdin/stdout (stdio)
- Server and client run as a single integrated process
- No network ports needed

**When to use:**
- Default mode for local development
- Simplest setup - just run the client
- Single-user scenarios
- No need for separate server management

**How to start:**
```bash
# Option 1: Use the start script
./start_client.sh

# Option 2: Run directly
cd mcp-client
python3 client.py
```

**Architecture:**
```
┌─────────────────────────────────┐
│  Client (client.py)             │
│                                 │
│  ┌─────────────────────┐        │
│  │ MCP Server          │        │
│  │ (auto-started)      │        │
│  │                     │        │
│  │ stdio communication │        │
│  └─────────────────────┘        │
└─────────────────────────────────┘
```

---

## 2. HTTP/SSE Mode - Standalone Server

**How it works:**
- Server runs independently as a web service
- Client connects to server via HTTP/SSE (Server-Sent Events)
- Server listens on http://localhost:8000/sse
- Multiple clients can connect to the same server

**When to use:**
- Multiple clients need to share the same server
- Server needs to run continuously
- Testing HTTP/SSE connections
- Matching your production architecture pattern

**How to start:**

**Step 1: Start the server**
```bash
# Terminal 1: Start standalone SSE server
./start_server.sh

# Output:
# 🚀 Starting MCP Server in SSE mode...
# 📡 Server will be available at http://localhost:8000/sse
```

**Step 2: Connect client to server**
```bash
# Terminal 2: Connect client to SSE server
./start_client_http.sh

# Or manually:
cd mcp-client
python3 client.py --http http://localhost:8000/sse
```

**Architecture:**
```
┌─────────────────┐         HTTP/SSE          ┌─────────────────┐
│ Client 1        │◄────────────────────────►  │                 │
└─────────────────┘                            │  MCP Server     │
                                               │  (standalone)   │
┌─────────────────┐         HTTP/SSE          │                 │
│ Client 2        │◄────────────────────────►  │  Port 8000/sse  │
└─────────────────┘                            │                 │
                                               └─────────────────┘
```

---

## Implementation Details

### Server (server.py)

**Stdio Mode:**
```python
# Default: when run without flags
python3 server.py
# Uses: mcp.run()
```

**SSE Mode:**
```python
# When run with --sse or --http flag
python3 server.py --sse
# Uses: mcp.sse_app() + uvicorn
```

### Client (client.py)

**Stdio Mode:**
```python
# Default: auto-starts server as subprocess
client = MCPClient(server_path=str(server_path), workspace=workspace)
await client._start_stdio()
# Uses: mcp.client.stdio.stdio_client()
```

**HTTP/SSE Mode:**
```python
# When --http flag provided
client = MCPClient(workspace=workspace, http_url="http://localhost:8000/sse")
await client._start_http()
# Uses: mcp.client.sse.sse_client()
```

---

## Reference Implementation Pattern

This implementation matches the pattern from:
- `oovacha-mcp-services/server_issue_query.py` (line 393: `app = mcp.sse_app()`)
- `oovacha-inline-agent/chat_routes.py` (line 162: `await MCPHttp.create(url=MCP_SSE_URL)`)

**Key similarities:**
1. Server uses `mcp.sse_app()` for HTTP/SSE endpoint
2. Client connects to `/sse` endpoint
3. Supports both standalone and integrated modes
4. Uses FastMCP framework

---

## Quick Reference

| Mode | Server Start | Client Start | Use Case |
|------|-------------|--------------|----------|
| **Stdio** | Auto-started | `./start_client.sh` | Default, single user |
| **HTTP/SSE** | `./start_server.sh` | `./start_client_http.sh` | Multiple clients, testing |

---

## Command Line Arguments

### Client Arguments
```bash
python3 client.py [OPTIONS]

Options:
  --http URL     Connect to HTTP/SSE server at URL
                 Example: --http http://localhost:8000/sse
  --model MODEL  Set default Ollama model
                 Default: mistral-nemo:12b-instruct-2407-q2_K
```

### Server Arguments
```bash
python3 server.py [OPTIONS]

Options:
  --sse          Start in SSE mode (HTTP server)
  --http         Same as --sse (alias)
  (no flags)     Start in stdio mode (default)
```

---

## Environment Variables

- `WORKSPACE_PATH`: Set workspace directory for file operations
  ```bash
  export WORKSPACE_PATH=/path/to/workspace
  ./start_server.sh
  ```

---

## Troubleshooting

### "Connection refused" error
- Make sure server is running: `./start_server.sh`
- Check server URL includes `/sse`: `http://localhost:8000/sse`
- Verify port 8000 is not in use: `lsof -i :8000`

### "No tools available" (Tools: 0)
- Check server started successfully
- Verify client is connecting to correct URL
- In stdio mode, check server.py path is correct

### Server not starting
- Check Python version: `python3 --version` (need 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check if another process is using port 8000
