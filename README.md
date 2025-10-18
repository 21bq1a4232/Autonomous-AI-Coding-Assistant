# Autonomous AI Coding Assistant

An intelligent AI coding assistant that works **exactly like Claude Code** - using pure AI intelligence with zero hardcoded patterns.

## Philosophy

> "Trust the brain, not the patterns."

This agent uses **pure AI intelligence** to understand natural language requests and execute coding tasks autonomously. No regex patterns, no hardcoded rules, no predefined responses - just the model's brain.

## Features

### 🧠 Pure AI Intelligence
- **Zero hardcoded patterns** - All understanding comes from the AI model
- **Natural language processing** - Ask anything naturally, the AI figures it out
- **Context-aware planning** - Uses session memory to make intelligent decisions
- **Adaptive execution** - Works with any Ollama model, automatically detects capabilities

### 🚀 Autonomous Execution
- **Read-only operations execute automatically** - No confirmation needed for listing files, reading code, searching, analyzing
- **Safe write operations** - Asks approval for file creation, edits, command execution
- **Intelligent post-processing** - Analyzes results and provides natural language explanations

### 💾 Session Memory
- **File tracking** - Remembers files read during the session
- **Project context** - Understands project type and structure
- **Conversation history** - Maintains context across requests
- **Smart optimization** - Avoids redundant file reads

## Architecture

```
User Request
    ↓
🧠 AI Planning (Pure Intelligence)
    ├─ Understands intent naturally
    ├─ Checks session memory
    ├─ Chooses appropriate tools
    └─ Creates execution plan
    ↓
Execute Plan
    ├─ Read-only: Auto-execute
    └─ Write ops: Ask approval
    ↓
📊 Post-Processing
    └─ AI explains results naturally
```

## Quick Start

### Prerequisites

1. **Ollama** installed with at least one model:
```bash
# Recommended models
ollama pull qwen2.5-coder:32b-instruct-q4_K_M  # Best for coding (32B)
ollama pull qwen2.5:14b-instruct-q4_K_M        # Good balance (14B)
ollama pull llama3.2:7b-instruct-q4_K_M        # Smaller option (7B)
```

2. **Python 3.8+** with dependencies:
```bash
pip install -r requirements.txt
```

### Running the Agent

**Stdio Mode (Default)** - Client auto-starts server:
```bash
./start_client.sh
```

**HTTP Mode** - Server runs separately:
```bash
# Terminal 1: Start server
./start_server.sh

# Terminal 2: Connect client
./start_client_http.sh
```

## Usage Examples

The agent understands natural language completely. Here are some examples:

### Read-Only Operations (Execute Automatically)

```bash
You: what directory am i in

🧠 Thinking...
📋 Plan: List files in current directory
🔓 All operations are read-only - executing automatically

⚙️  Step 1/1: List files in current directory
✅ Done
📁 Found 11 items...

💡 You're in the Autonomous-AI-Coding-Assistant project directory.
```

```bash
You: read client.py and explain what it does

🧠 Thinking...
📋 Plan: Read client.py and provide analysis
🔓 All operations are read-only - executing automatically

⚙️  Step 1/1: Read file client.py
✅ Done
📄 client.py content: [syntax highlighted preview]
📝 Added to session memory (35,234 chars)

💡 client.py implements the AutonomousCodingAgent class with pure AI
intelligence. It uses Ollama models to understand requests naturally,
plan tasks, and execute them autonomously...
```

```bash
You: search for the MCPClient class

🧠 Thinking...
📋 Plan: Search codebase for MCPClient
🔓 All operations are read-only - executing automatically

⚙️  Step 1/1: Search for 'MCPClient' in .
✅ Done
🔍 Found in mcp-client/client.py:61
```

### Write Operations (Ask for Approval)

```bash
You: generate a django project on movie recommendations

🧠 Thinking...

📋 Plan:
1. Create project directory structure 🔒
2. Write manage.py and settings.py 🔒
3. Create movies app with models 🔒
4. Write views and templates 🔒

🚀 Execute plan? [y/n]
```

## How It Works

### 1. Pure AI Planning

Instead of hardcoded patterns, the AI model receives:
- User request
- Session memory (files read, project context, conversation history)
- Available tools
- Minimal instructions

The AI brain naturally understands what to do and creates a plan.

### 2. Autonomous Execution

**Read-only operations** (safe):
- `list_files` - List directory contents
- `read_file` - Read file content
- `search_code` - Search for patterns
- `analyze_project` - Analyze project structure
- `get_file_info` - Get file information

→ **Execute automatically without asking**

**Write operations** (need approval):
- `write_file` - Create/write files
- `edit_file` - Edit existing files
- `execute_command` - Run shell commands
- `create_directory` - Create directories

→ **Ask for user approval**

### 3. Intelligent Post-Processing

After execution, the AI analyzes:
- What the user asked
- What was executed
- Files in session memory
- Project context

Then provides natural language explanation of results.

## Model Requirements

The agent works with **any Ollama model**, but intelligence varies:

| Model Size | Performance | Recommendation |
|------------|-------------|----------------|
| **32B+** | Excellent - handles complex tasks naturally | ✅ Recommended |
| **14-20B** | Good - reliable for most tasks | ✅ Good choice |
| **7-14B** | Decent - works for simple tasks | ⚠️ Basic use |
| **<7B** | Limited - may struggle with planning | ❌ Not recommended |

**Best models tested:**
- `qwen2.5-coder:32b-instruct-q4_K_M` - Best for coding (16GB VRAM)
- `qwen2.5:14b-instruct-q4_K_M` - Good balance (8GB VRAM)
- `llama3.2:7b-instruct-q4_K_M` - Minimal option (4GB VRAM)

## Commands

Once running, you can use these slash commands:

- `/model` - Switch AI model
- `/clear` - Clear screen
- `/session` - Show session memory (files read, context)
- `/history` - Show command history
- `/context` - Manage context length
- `/help` - Show help
- `/quit` - Exit assistant

## Session Memory

The agent maintains intelligent session memory:

```bash
You: /session

📋 Session Memory

📄 Files Read
┌────────────┬──────────┬────────┬──────────────────────────┐
│ File       │ Size     │ Lines  │ Summary                  │
├────────────┼──────────┼────────┼──────────────────────────┤
│ client.py  │ 35,234   │ 992    │ Autonomous AI agent with │
│            │          │        │ Ollama integration       │
└────────────┴──────────┴────────┴──────────────────────────┘

💬 Recent Context:
  1. User asked about project structure
  2. Read client.py and explained architecture
  3. Analyzed MCP server tools
```

The AI uses this memory to:
- Avoid re-reading files
- Understand project context
- Answer questions about files already seen
- Make contextual decisions

## Project Structure

```
Autonomous-AI-Coding-Assistant/
├── mcp-client/              # AI agent client
│   ├── client.py           # Main agent implementation
│   └── README.md           # Client documentation
├── mcp-server/              # MCP tool server
│   ├── server.py           # FastMCP server with 9 tools
│   └── README.md           # Server documentation
├── start_client.sh          # Start client (stdio mode)
├── start_server.sh          # Start server (HTTP mode)
├── start_client_http.sh     # Start client (HTTP mode)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Connection Modes

### Stdio Mode (Default)
- Client automatically starts server as subprocess
- Simple single-command startup
- Communication via stdin/stdout

```bash
./start_client.sh
```

### HTTP/SSE Mode
- Server runs independently
- Multiple clients can connect
- Communication via HTTP + Server-Sent Events

```bash
# Terminal 1
./start_server.sh

# Terminal 2
./start_client_http.sh
```

See [CONNECTION_MODES.md](CONNECTION_MODES.md) for details.

## Documentation

- **[PURE_AI_ARCHITECTURE.md](PURE_AI_ARCHITECTURE.md)** - How the pure AI system works
- **[AUTONOMOUS_EXECUTION.md](AUTONOMOUS_EXECUTION.md)** - Autonomous execution explained
- **[CONNECTION_MODES.md](CONNECTION_MODES.md)** - Stdio vs HTTP modes
- **[mcp-client/README.md](mcp-client/README.md)** - Client architecture
- **[mcp-server/README.md](mcp-server/README.md)** - Server tools

## Key Differences from Pattern-Based Assistants

| Traditional Assistants | This Agent (Pure AI) |
|------------------------|---------------------|
| 250+ lines of regex patterns | Zero hardcoded patterns |
| Hardcoded intent detection | AI understands naturally |
| Fixed response templates | AI generates responses |
| Limited to predefined commands | Handles any natural language |
| Constant maintenance needed | Zero maintenance |
| Works only with specific phrases | Works with any phrasing |

## Examples of Natural Language Understanding

The AI understands these naturally (and infinite variations):

```bash
✅ "what directory am i in"
✅ "list files"
✅ "read client.py"
✅ "search for the MCPClient class"
✅ "analyze this project"
✅ "what's the purpose of server.py"
✅ "generate a django project on X"
✅ "create a REST API for Y"
✅ "fix the bug in Z"
✅ "add error handling"
✅ "refactor the database models"
```

**No patterns needed!** The AI brain understands everything.

## Comparison to Claude Code

This agent uses the **same philosophy as Claude Code**:

| Feature | This Agent | Claude Code |
|---------|-----------|-------------|
| Pattern matching | ❌ None | ❌ None |
| Hardcoded rules | ❌ None | ❌ None |
| Natural language | ✅ Full | ✅ Full |
| Context awareness | ✅ Yes | ✅ Yes |
| Memory | ✅ Session | ✅ Conversation |
| Approach | 🧠 Pure AI | 🧠 Pure AI |

## Requirements

- Python 3.8+
- Ollama with at least one model installed
- 4GB+ VRAM (more is better)
- Linux/macOS/Windows with WSL

## Troubleshooting

### Model not generating valid plans
- Use a larger model (14B+ recommended)
- Try qwen2.5-coder models (specialized for coding)
- Check model is working: `ollama run <model> "test"`

### "Tool 'X' not available" errors
- Check MCP server is running
- Verify tools loaded: `/session` command shows tools
- Restart client: `./start_client.sh`

### Slow responses
- Use smaller model (7-14B range)
- Use quantized models (q4_K_M or q5_K_M)
- Ensure adequate VRAM available

## Contributing

This is a pure AI agent - improvements come from:
1. Using better/larger models
2. Enhancing session memory system
3. Adding more MCP tools
4. Improving the minimal AI prompts

**No pattern matching to maintain!**

## License

MIT License - See LICENSE file

## Credits

Built with:
- [Ollama](https://ollama.ai/) - Local LLM hosting
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) - Interactive CLI

Inspired by [Claude Code](https://claude.com/claude-code) - The best AI coding assistant.
