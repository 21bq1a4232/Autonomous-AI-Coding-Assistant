# Autonomous AI Coding Assistant

A Claude Code-like AI assistant powered by Ollama and MCP (Model Context Protocol). Features intelligent code assistance, file operations, command history, and autocomplete.

## ✨ Key Features

### 🎯 Claude Code-Inspired UX
- **Command History**: Press ↑/↓ to navigate previous commands
- **Smart Autocomplete**: Type `/` to see filtered command suggestions
- **Session Memory**: Remembers files and context during conversation
- **Intelligent Planning**: Breaks down tasks into smart, executable steps

### 🔧 Core Capabilities
- **File Operations**: Read, write, edit files with validation
- **Code Search**: Pattern matching across your codebase
- **Project Analysis**: Auto-detect project types and structure
- **Safe Command Execution**: Security-checked shell commands
- **Directory Management**: Create and navigate directories

### 🛡️ Security
- **Path Validation**: Prevents directory traversal attacks
- **Command Safety**: Blocks dangerous operations
- **Workspace Isolation**: All operations confined to workspace

### 💻 Advanced Commands
- `/model` - Switch between Ollama models
- `/session` - View session memory
- `/history` - See command history
- `/context` - Manage context length
- `/clear` - Clear screen
- `/help` - Show all commands

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   MCP Server        │         │   Client             │
│   (Port 8000)       │◄───────►│   (Interactive CLI)  │
│                     │   HTTP/ │                      │
│ • File tools        │   SSE   │ • Command history    │
│ • Code search       │         │ • Autocomplete       │
│ • Project analysis  │         │ • Session memory     │
│ • Security checks   │         │ • Rich UI            │
└─────────────────────┘         └──────────────────────┘
           │                              │
           │                              │
           ▼                              ▼
    FastMCP Protocol              Ollama AI Models
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed with at least one model

### Installation

1. **Setup dependencies**:
   ```bash
   python setup.py
   ```

2. **Install Ollama models**:
   ```bash
   ollama pull mistral-nemo:12b-instruct-2407-q2_K
   # or any other model you prefer
   ollama pull llama3.2
   ```

3. **Start the MCP server** (Terminal 1):
   ```bash
   ./start_server.sh
   # Or manually:
   cd mcp-server && python3 server.py
   ```

4. **Start the client** (Terminal 2):
   ```bash
   ./start_client.sh
   # Or manually:
   cd mcp-client && python3 client.py
   ```

## 📋 Available Tools

### File Operations
- `read_file(path)` - Read file contents with metadata
- `write_file(path, content)` - Create or update files
- `edit_file(path, search, replace)` - Search and replace in files
- `get_file_info(path)` - Get detailed file information

### Directory Operations
- `list_files(path)` - List directory contents
- `create_directory(path)` - Create directories
- `analyze_project(path)` - Analyze project structure

### Code Operations
- `search_code(query, path, file_pattern)` - Search for code patterns
- `execute_command(command)` - Execute shell commands safely

## 🔒 Security Measures

### Path Validation
- All file paths are validated to prevent directory traversal
- Paths are sanitized to remove `../` and similar patterns
- Operations are confined to the workspace directory

### Command Safety
- Dangerous commands are blocked (rm -rf, mkfs, etc.)
- Commands are executed with timeouts
- All operations are logged and validated

### Input Sanitization
- All user inputs are validated before processing
- File contents are checked for binary data
- Command arguments are sanitized

## 🎯 Usage Examples

### Interactive Session
```
👤 You (mistral-nemo) list files in this directory
🤖 [Plans and executes list_files]
📁 Found 10 items:
   📄 client.py
   📄 requirements.txt
   ...

👤 You (mistral-nemo) read client.py and explain the main components
🤖 [Reads file and analyzes]
📄 client.py contains...

👤 You (mistral-nemo) create a test file
🤖 [Plans: create test.py with basic structure]
✅ Created test.py
```

### Using Commands
```
👤 You (mistral-nemo) /model
📦 Available Models:
1. mistral-nemo:12b-instruct-2407-q2_K ✓
2. llama3.2
3. codellama

👤 You (mistral-nemo) /session
📋 Session Memory
📄 Files Read:
  • client.py (15,230 chars)
  • server.py (8,542 chars)

👤 You (mistral-nemo) /history
📜 Command History:
  1. list files in this directory
  2. read client.py
  3. create a test file
```

### Smart Planning
```
User: Add error handling to all file operations
Assistant:
📋 Plan:
  1. 🔓 Search for file operation functions
  2. 🔓 Read each file
  3. 🔒 Edit files to add try-catch blocks
  4. 🔒 Test changes

🚀 Execute? (Y/n)
```

## 🛠️ Development

### Project Structure
```
coding-assistant/
├── mcp-client/          # Client application
│   ├── client.py       # Main client with Rich UI
│   ├── requirements.txt
│   └── README.md
├── mcp-server/         # MCP server
│   ├── server.py       # FastMCP server with tools
│   ├── requirements.txt
│   └── README.md
├── setup.py            # Setup script
└── README.md           # This file
```

### Adding New Tools

1. **Add tool to server** (`mcp-server/server.py`):
   ```python
   @mcp.tool()
   def my_new_tool(param: str) -> dict:
       """Description of the tool"""
       try:
           # Tool implementation
           return {"status": "success", "result": "..."}
       except Exception as e:
           return {"status": "error", "message": str(e)}
   ```

2. **Update client** if needed for special handling

### Error Handling

The system includes comprehensive error handling:
- **Connection errors**: Automatic retry with exponential backoff
- **Tool errors**: Graceful degradation with user feedback
- **Timeout errors**: Clear timeout messages
- **Security errors**: Detailed security violation messages

## 🔧 Configuration

### Environment Variables
- `WORKSPACE_PATH`: Set the workspace directory (default: current directory)

### Model Configuration
- Change models using `/model` command in the client
- Models are loaded from Ollama automatically

## 🐛 Troubleshooting

### Common Issues

1. **"Cannot connect to server at http://localhost:8000"**
   - Make sure the MCP server is running first
   - Run: `./start_server.sh` or `cd mcp-server && python3 server.py`
   - Check if port 8000 is already in use

2. **"Ollama not available"**
   - Install Ollama from https://ollama.ai/
   - Pull at least one model: `ollama pull mistral-nemo:12b-instruct-2407-q2_K`
   - Ensure Ollama service is running

3. **"Module not found" errors**
   - Run the setup script: `python setup.py`
   - Or install manually:
     ```bash
     cd mcp-server && pip install -r requirements.txt
     cd ../mcp-client && pip install -r requirements.txt
     ```

4. **"Tool execution timed out"**
   - Some operations may take longer than expected
   - The server will retry with exponential backoff

5. **Command history not working**
   - Ensure `prompt_toolkit` is installed
   - Try reinstalling: `pip install prompt_toolkit>=3.0.0`

### Custom Configuration

**Change MCP Server Port:**
Edit `mcp-server/server.py` line 337:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here
```

Then set the env variable:
```bash
export MCP_SERVER_URL="http://localhost:YOUR_PORT"
./start_client.sh
```

**Change Workspace:**
```bash
export WORKSPACE_PATH="/path/to/your/workspace"
./start_server.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/fastmcp/fastmcp) for the MCP server framework
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal UI
- [Ollama](https://ollama.ai/) for AI model integration
