# Autonomous AI Coding Assistant

A powerful AI-powered coding assistant that uses Model Context Protocol (MCP) to provide intelligent code assistance, file operations, and project management capabilities.

## ✨ Features

### 🔧 Core Capabilities
- **File Operations**: Read, write, edit, and manage files with full validation
- **Code Search**: Search for patterns across your codebase
- **Project Analysis**: Automatic detection of project types and structure
- **Safe Command Execution**: Execute shell commands with security checks
- **Directory Management**: Create and navigate directory structures

### 🛡️ Security Features
- **Path Validation**: Prevents directory traversal attacks
- **Command Safety**: Blocks dangerous shell commands
- **Workspace Isolation**: All operations are confined to the workspace
- **Input Sanitization**: All inputs are validated and sanitized

### 🚀 Enhanced User Experience
- **Retry Logic**: Automatic retry for failed connections
- **Timeout Handling**: Prevents hanging operations
- **Rich Feedback**: Beautiful terminal interface with progress indicators
- **Error Recovery**: Graceful handling of errors with helpful messages
- **Tool Validation**: Ensures tools exist before execution

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   MCP Server    │    │   Ollama        │
│   (Rich UI)     │◄──►│   (FastMCP)     │    │   (AI Models)   │
│                 │    │                 │    │                 │
│ • User Interface│    │ • File Ops      │    │ • Code Planning │
│ • Task Planning │    │ • Code Search   │    │ • Suggestions  │
│ • Error Handling│    │ • Security      │    │ • Analysis      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed and running
- At least one AI model (e.g., `mistral-nemo:12b-instruct-2407-q2_K`)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd coding-assistant
   python setup.py
   ```

2. **Install Ollama** (if not already installed):
   ```bash
   # Visit https://ollama.ai/ for installation instructions
   ollama pull mistral-nemo:12b-instruct-2407-q2_K
   ```

3. **Run the assistant**:
   ```bash
   cd mcp-client
   python client.py
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

### Basic File Operations
```
User: Create a new Python file called hello.py with a hello world function
Assistant: [Plans and executes]
✅ Created hello.py with hello world function
```

### Code Search
```
User: Find all functions that use 'requests' library
Assistant: [Searches codebase]
📊 Found 3 matches in 2 files
```

### Project Analysis
```
User: Analyze this project structure
Assistant: [Analyzes project]
📦 Project Type: Python
📊 Files: 15 total
🔍 Main files: main.py, requirements.txt, setup.py
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

1. **"Server path not found"**
   - Ensure you're running from the correct directory
   - Check that `mcp-server/server.py` exists

2. **"Failed to initialize MCP server"**
   - Check that all dependencies are installed
   - Verify Python 3.8+ is being used

3. **"Tool execution timed out"**
   - Some operations may take longer than 60 seconds
   - Check if the operation is actually running

4. **"Command contains potentially dangerous operations"**
   - The command was blocked for security reasons
   - Use safer alternatives or modify the security rules

### Debug Mode
Run with debug output:
```bash
PYTHONPATH=. python -m mcp-client.client
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
