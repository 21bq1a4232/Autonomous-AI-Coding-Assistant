# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-10-18

### 🎉 Major Refactor - Claude Code-Like Experience

This release completely refactors the architecture to work like Claude Code with proper MCP server-client separation.

### ✨ Added

#### Architecture Changes
- **Standalone MCP Server**: Server now runs as independent HTTP/SSE service on port 8000
- **HTTP/SSE Client**: Replaced subprocess stdio with proper HTTP client using aiohttp
- **Health Check Endpoint**: Added `/health` endpoint for server monitoring
- **Server Info Endpoint**: Added `/` endpoint with server information

#### User Experience
- **Command History**: Press ↑/↓ to navigate through previous commands
- **Smart Autocomplete**: Type `/` to see filtered command suggestions with descriptions
- **Real-time Completion**: Commands autocomplete as you type
- **Command Filtering**: Autocomplete filters commands based on what you type
- **Session Memory Display**: View files and context stored during conversation
- **Command History View**: New `/history` command to see past commands

#### New Commands
- `/history` - View command history (last 20 commands)
- `/context` - Manage context length (placeholder for future enhancement)
- Enhanced `/help` with usage tips

#### Configuration
- **config.yaml**: Centralized configuration file for all settings
- **Environment Variables**: Support for `MCP_SERVER_URL` and `WORKSPACE_PATH`
- **Startup Scripts**: Easy launch scripts for server and client
  - `start_server.sh` - Launch MCP server
  - `start_client.sh` - Launch client

#### Dependencies
- Added `prompt_toolkit>=3.0.0` for advanced input handling
- Added `aiohttp>=3.9.0` for HTTP client
- Added `starlette>=0.27.0` for server routing

### 🔧 Changed

#### Breaking Changes
- Server must now be started separately before running client
- Changed from subprocess stdio communication to HTTP/SSE
- Removed hardcoded Mac path, now uses relative path detection
- Workspace prompt now uses prompt_toolkit instead of rich.prompt

#### Client Improvements
- Better error messages when server is not running
- Improved connection handling with health checks
- Enhanced user prompts with HTML formatting
- Cleaner command parsing and handling

#### Server Improvements
- Server runs on `0.0.0.0:8000` by default (configurable)
- Better logging and startup messages
- Added custom route support (health, root)
- Improved JSON-RPC response handling

### 🐛 Fixed
- Fixed hardcoded `/Users/pranavkrishnadanda/...` path issue
- Fixed timeout handling for tool execution
- Improved error messages for connection failures
- Better handling of keyboard interrupts

### 📚 Documentation
- Complete README rewrite with new architecture diagram
- Added comprehensive usage examples
- Enhanced troubleshooting section
- Added custom configuration instructions
- Created detailed startup guide

### 🏗️ Technical Improvements
- Separated concerns: Server handles tools, Client handles UI
- Async/await throughout for better performance
- Better type hints and code organization
- Improved error handling and recovery
- More robust connection management

### 🔐 Security
- Maintained all existing security features:
  - Path validation and sanitization
  - Dangerous command blocking
  - Workspace isolation
  - Input validation

### 📝 Configuration Options
New configurable options in `config.yaml`:
- AI models and their settings
- Server host/port
- Client connection settings
- UI theme and preferences
- Command configurations
- Session management
- Planning behavior
- Security rules
- System prompts

## [1.0.0] - Previous Release

### Features
- Basic MCP server with file operations
- Ollama integration for AI
- Rich terminal UI
- Session memory
- Task planning
- Security features

---

## How to Use This Version

### Starting the System

**Terminal 1 - Start Server:**
```bash
./start_server.sh
```

**Terminal 2 - Start Client:**
```bash
./start_client.sh
```

### New Features to Try

1. **Command History**:
   - Type some commands
   - Press ↑ to see previous commands
   - Press ↓ to navigate forward

2. **Autocomplete**:
   - Type `/` and see all available commands
   - Type `/m` and see it filter to `/model`
   - Tab to complete

3. **View History**:
   ```
   /history
   ```

4. **Check Session Memory**:
   ```
   /session
   ```

### Migration from 1.0

If upgrading from version 1.0:

1. Install new dependencies:
   ```bash
   cd mcp-client && pip install -r requirements.txt
   cd ../mcp-server && pip install -r requirements.txt
   ```

2. Start using the new two-process architecture (server + client)

3. No data migration needed - sessions start fresh
