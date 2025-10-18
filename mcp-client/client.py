#!/usr/bin/env python3
"""
Autonomous AI Coding Assistant - WORKING VERSION
"""

import asyncio
import json
import os
import subprocess
import sys
import traceback
from typing import Optional
from pathlib import Path
import ollama
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML

console = Console()

class CommandCompleter(Completer):
    """Custom completer for slash commands"""

    def __init__(self):
        self.commands = [
            ("/model", "Switch AI model"),
            ("/clear", "Clear screen"),
            ("/session", "Show session memory"),
            ("/context", "Show/set context length"),
            ("/history", "Show command history"),
            ("/help", "Show help"),
            ("/quit", "Exit assistant"),
        ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only complete if user typed /
        if text.startswith('/'):
            word = text[1:].lower()  # Remove / and lowercase

            for cmd, description in self.commands:
                if cmd[1:].startswith(word):  # Match without /
                    yield Completion(
                        cmd[len(text):],  # Only complete the remaining part
                        display=cmd,
                        display_meta=description
                    )

class MCPClient:
    """MCP Client supporting both stdio and HTTP modes"""

    def __init__(self, server_path: str = None, workspace: str = ".", http_url: str = None):
        self.server_path = server_path
        self.workspace = workspace
        self.http_url = http_url
        self.stdio_context = None
        self.http_context = None
        self.client = None
        self.mode = "http" if http_url else "stdio"

    async def start(self):
        """Start MCP client in either stdio or HTTP mode"""
        if self.mode == "http":
            return await self._start_http()
        else:
            return await self._start_stdio()

    async def _start_stdio(self):
        """Start MCP server as subprocess and connect via stdio"""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        try:
            if not self.server_path:
                console.print("[red]❌ Server path required for stdio mode[/red]")
                return False

            # Start server as subprocess
            server_params = StdioServerParameters(
                command="python3",
                args=[self.server_path],
                env={**dict(os.environ), "WORKSPACE_PATH": self.workspace}
            )

            # Connect via stdio using context manager properly
            self.stdio_context = stdio_client(server_params)
            read_stream, write_stream = await self.stdio_context.__aenter__()

            # Create client session
            self.client = ClientSession(read_stream, write_stream)
            await self.client.__aenter__()

            # Initialize the session
            await self.client.initialize()

            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to start MCP server: {e}[/red]")
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False

    async def _start_http(self):
        """Connect to standalone HTTP MCP server"""
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        try:
            # Connect to HTTP server using SSE
            self.http_context = sse_client(self.http_url)
            read_stream, write_stream = await self.http_context.__aenter__()

            # Create client session
            self.client = ClientSession(read_stream, write_stream)
            await self.client.__aenter__()

            # Initialize the session
            await self.client.initialize()

            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to connect to HTTP server at {self.http_url}: {e}[/red]")
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool"""
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            result = await self.client.call_tool(tool_name, arguments)

            # Parse FastMCP result format
            if hasattr(result, 'content') and result.content:
                first_content = result.content[0]
                if hasattr(first_content, 'text'):
                    try:
                        return json.loads(first_content.text)
                    except:
                        return {"status": "success", "content": first_content.text}

            return {"status": "success", "result": str(result)}

        except Exception as e:
            return {"status": "error", "message": f"Tool call failed: {str(e)}"}

    async def list_tools(self) -> list:
        """List available tools"""
        if not self.client:
            return []

        try:
            result = await self.client.list_tools()
            if hasattr(result, 'tools'):
                return [{"name": tool.name, "description": tool.description or ""} for tool in result.tools]
            return []
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to list tools: {e}[/yellow]")
            return []

    async def close(self):
        """Close the connection"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except:
                pass
        if self.stdio_context:
            try:
                await self.stdio_context.__aexit__(None, None, None)
            except:
                pass
        if self.http_context:
            try:
                await self.http_context.__aexit__(None, None, None)
            except:
                pass

class AutonomousCodingAgent:
    def __init__(self, default_model="mistral-nemo:12b-instruct-2407-q2_K"):
        self.client = None
        self.available_tools = []
        self.current_model = default_model
        self.available_models = []
        self.conversation_history = []
        
        # Session memory for files and context
        self.session_memory = {
            "files_read": {},  # filename -> {content, summary, timestamp}
            "project_context": {},  # project analysis results
            "conversation_context": [],  # key conversation points
            "code_snippets": {},  # important code snippets
        }
    
    def add_file_to_memory(self, filename: str, content: str, summary: str = None):
        """Add a file to session memory"""
        import time
        
        # Generate summary if not provided
        if not summary:
            summary = self.generate_file_summary(content, filename)
        
        self.session_memory["files_read"][filename] = {
            "content": content,
            "summary": summary,
            "timestamp": time.time(),
            "size": len(content),
            "lines": len(content.split('\n'))
        }
        
        console.print(f"[dim]📝 Added {filename} to session memory ({len(content)} chars)[/dim]")
    
    def generate_file_summary(self, content: str, filename: str) -> str:
        """Generate a summary of file content"""
        try:
            # Create a concise summary prompt
            summary_prompt = f"""Analyze this file and provide a concise summary (2-3 sentences):

File: {filename}
Content: {content[:1000]}...

Focus on:
- What this file does
- Key functions/classes
- Main purpose

Keep it brief and technical."""

            response = ollama.chat(
                model=self.current_model,
                messages=[{"role": "user", "content": summary_prompt}]
            )
            return response['message']['content'].strip()
        except:
            return f"File: {filename} ({len(content)} characters)"
    
    def get_session_context(self) -> str:
        """Get current session context for AI"""
        context_parts = []
        
        # Add project context
        if self.session_memory["project_context"]:
            context_parts.append(f"Project: {self.session_memory['project_context']}")
        
        # Add files in memory
        if self.session_memory["files_read"]:
            context_parts.append("Files in session:")
            for filename, info in self.session_memory["files_read"].items():
                context_parts.append(f"- {filename}: {info['summary']}")
        
        # Add recent conversation context
        if self.session_memory["conversation_context"]:
            context_parts.append("Recent context:")
            for ctx in self.session_memory["conversation_context"][-3:]:  # Last 3 items
                context_parts.append(f"- {ctx}")
        
        return "\n".join(context_parts) if context_parts else "No session context yet."
    
    def add_conversation_context(self, context: str):
        """Add important conversation context"""
        self.session_memory["conversation_context"].append(context)
        # Keep only last 10 items
        if len(self.session_memory["conversation_context"]) > 10:
            self.session_memory["conversation_context"] = self.session_memory["conversation_context"][-10:]
    
    def show_session_memory(self):
        """Display current session memory"""
        console.print("\n[bold cyan]📋 Session Memory[/bold cyan]\n")
        
        # Files in memory
        if self.session_memory["files_read"]:
            files_table = Table(title="📄 Files Read", box=box.ROUNDED)
            files_table.add_column("File", style="cyan")
            files_table.add_column("Size", justify="right")
            files_table.add_column("Lines", justify="right") 
            files_table.add_column("Summary", style="dim")
            
            for filename, info in self.session_memory["files_read"].items():
                files_table.add_row(
                    filename,
                    f"{info['size']:,} chars",
                    f"{info['lines']:,}",
                    info['summary'][:50] + "..." if len(info['summary']) > 50 else info['summary']
                )
            console.print(files_table)
        else:
            console.print("[dim]No files in memory yet[/dim]")
        
        # Project context
        if self.session_memory["project_context"]:
            console.print(f"\n[bold]🏗️  Project Context:[/bold] {self.session_memory['project_context']}")
        
        # Conversation context
        if self.session_memory["conversation_context"]:
            console.print(f"\n[bold]💬 Recent Context:[/bold]")
            for i, ctx in enumerate(self.session_memory["conversation_context"][-5:], 1):
                console.print(f"  {i}. {ctx}")
        
        console.print()
    
    def load_available_models(self):
        """Load Ollama models"""
        try:
            # Check if Ollama is available
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                console.print("[yellow]⚠️  Ollama not available, using default model[/yellow]")
                self.available_models = [self.current_model]
                return
            
            console.print("[dim]Loading models from Ollama...[/dim]")
            
            # Use subprocess instead of ollama.list() to avoid hanging
            models_output = result.stdout.strip()
            if not models_output:
                self.available_models = [self.current_model]
                console.print(f"[cyan]📦 Found {len(self.available_models)} models[/cyan]")
                return
            
            # Parse the ollama list output
            model_names = []
            for line in models_output.split('\n')[1:]:  # Skip header
                if line.strip():
                    # Extract model name (first column)
                    parts = line.split()
                    if parts:
                        model_names.append(parts[0])
            
            self.available_models = model_names if model_names else [self.current_model]
            console.print(f"[cyan]📦 Found {len(self.available_models)} models[/cyan]")
            
        except subprocess.TimeoutExpired:
            console.print("[yellow]⚠️  Ollama timeout, using default model[/yellow]")
            self.available_models = [self.current_model]
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load models: {e}[/yellow]")
            self.available_models = [self.current_model]
    
    def list_models(self):
        """Display models"""
        table = Table(title="📦 Available Models", box=box.ROUNDED)
        table.add_column("№", style="cyan", justify="center")
        table.add_column("Model", style="green")
        table.add_column("Status", justify="center")
        
        for i, model in enumerate(self.available_models, 1):
            status = "✓" if model == self.current_model else ""
            table.add_row(str(i), model, status)
        
        console.print(table)
    
    def change_model(self):
        """Change model"""
        self.list_models()
        choice = Prompt.ask("\n[cyan]Select model number[/cyan]")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(self.available_models):
                self.current_model = self.available_models[idx]
                console.print(f"[green]✅ Switched to: {self.current_model}[/green]\n")
                return True
        return False
    
    async def plan_task(self, user_request: str) -> dict:
        """Plan task using AI"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Planning...", total=None)
            
            tools_list = ", ".join([t.get("name", "") for t in self.available_tools])
            
            # Get session context for intelligent planning
            session_context = self.get_session_context()
            
            planning_prompt = f"""User request: "{user_request}"

SESSION CONTEXT:
{session_context}

You are an intelligent AI assistant. Create a SMART execution plan using the context above.

INTELLIGENT PLANNING RULES:
1. If user asks to "list files" or "show files", use list_files(path=".")
2. If user mentions "the .py file" but you don't know which one, list files FIRST to find Python files
3. If user asks about files already in session memory, reference them by exact name
4. Be SPECIFIC with file paths - never use generic names like "file_name" or "filename"
5. If user says "read the .py file" and multiple .py files exist, list files first to identify them
6. Use session context to avoid redundant operations
7. Break complex requests into logical steps

Return ONLY valid JSON:
{{
  "understanding": "specific understanding of what user wants",
  "steps": [
    {{
      "step": 1,
      "action": "specific description of this step",
      "tool": "exact_tool_name",
      "arguments": {{"exact_param": "specific_value"}},
      "needs_approval": false
    }}
  ]
}}

Available tools: {tools_list}

TOOL SIGNATURES:
- read_file(path: str) - Read file content
- write_file(path: str, content: str) - Write/create file  
- edit_file(path: str, search: str, replace: str) - Edit file
- list_files(path: str = ".") - List directory contents
- execute_command(command: str) - Run shell command
- analyze_project(path: str = ".") - Analyze project structure
- search_code(query: str, path: str = ".", file_pattern: str = "*.py") - Search code
- get_file_info(path: str) - Get file information
- create_directory(path: str) - Create directory

APPROVAL SETTINGS:
- needs_approval: true for write_file, edit_file, execute_command, create_directory
- needs_approval: false for read_file, list_files, get_file_info, analyze_project, search_code

Be intelligent and specific. Use exact file names when known."""

            try:
                response = ollama.chat(
                    model=self.current_model,
                    messages=[{"role": "user", "content": planning_prompt}],
                    format="json"
                )
                plan = json.loads(response['message']['content'])
                progress.update(task, completed=True)
                return plan
            except Exception as e:
                console.print(f"[red]Planning failed: {e}[/red]")
                return {"understanding": user_request, "steps": []}
    
    def display_plan(self, plan: dict):
        """Display plan"""
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Step", style="cyan", justify="right", width=5)
        table.add_column("Action", style="white")
        table.add_column("Approval", justify="center", width=15)
        
        for step in plan.get('steps', []):
            approval = "[yellow]🔒[/yellow]" if step.get('needs_approval') else "[green]🔓[/green]"
            table.add_row(f"{step['step']}.", step['action'], approval)
        
        console.print("\n")
        console.print(Panel(
            f"[bold cyan]📋 Task:[/bold cyan] {plan.get('understanding')}\n\n{table}",
            title="[bold magenta]Plan[/bold magenta]",
            border_style="magenta",
            box=box.DOUBLE
        ))
        console.print("\n")
    
    def ask_approval(self, action: str, details: str) -> bool:
        """Ask approval"""
        console.print("\n")
        console.print(Panel(details, title=f"[bold yellow]{action}[/bold yellow]", border_style="yellow"))
        return Confirm.ask("\n[bold cyan]✓ Proceed?[/bold cyan]", default=True)
    
    async def execute_step(self, step: dict, step_num: int, total: int) -> dict:
        """Execute one step with enhanced error handling"""
        action = step.get('action')
        tool = step.get('tool')
        arguments = step.get('arguments', {})
        needs_approval = step.get('needs_approval', True)
        
        console.print(f"\n[bold cyan]⚙️  Step {step_num}/{total}:[/bold cyan] {action}")
        
        # Validate tool exists
        if tool not in [t.get('name', '') for t in self.available_tools]:
            console.print(f"[red]❌ Tool '{tool}' not available[/red]")
            return {"status": "error", "message": f"Tool '{tool}' not found"}
        
        # Ask approval for sensitive operations
        if needs_approval and tool in ["write_file", "execute_command", "edit_file"]:
            details = f"[yellow]Tool:[/yellow] {tool}\n"
            
            if tool == "write_file":
                content = arguments.get('content', '')
                preview = content[:300] + "..." if len(content) > 300 else content
                syntax = Syntax(preview, "python", theme="monokai")
                console.print(f"[yellow]File:[/yellow] {arguments.get('path')}\n")
                console.print(syntax)
                
                if not Confirm.ask("\n[cyan]✓ Create file?[/cyan]", default=True):
                    return {"status": "skipped"}
            
            elif tool == "execute_command":
                details += f"\n[yellow]Command:[/yellow] {arguments.get('command')}"
                if not self.ask_approval(action, details):
                    return {"status": "skipped"}
        
        # Execute with timeout
        try:
            with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), console=console) as progress:
                task_p = progress.add_task(f"▶️  Executing...", total=None)
                
                # Add timeout for tool execution
                result = await asyncio.wait_for(
                    self.client.call_tool(tool, arguments),
                    timeout=60.0
                )
                progress.update(task_p, completed=True)
                
                # Handle MCP error format
                if isinstance(result, dict) and result.get('isError'):
                    error_msg = "Unknown error"
                    if 'content' in result and isinstance(result['content'], list):
                        for item in result['content']:
                            if item.get('type') == 'text':
                                error_msg = item.get('text', error_msg)
                                break
                    console.print(f"[red]❌ {error_msg}[/red]")
                    return {"status": "error", "message": error_msg}
                
                # Display result based on tool type
                if isinstance(result, dict):
                    if result.get('status') == 'success':
                        console.print(f"[green]✅ Done[/green]")
                        
                        # Handle different tool types intelligently
                        if tool == 'list_files':
                            # Parse and display file listing nicely
                            if 'files' in result:
                                files = result['files']
                                console.print(f"\n[cyan]📁 Found {len(files)} items:[/cyan]")
                                for file_info in files[:10]:  # Show first 10
                                    name = file_info.get('name', 'unknown')
                                    file_type = file_info.get('type', 'unknown')
                                    icon = "📁" if file_type == 'directory' else "📄"
                                    console.print(f"   {icon} {name}")
                                if len(files) > 10:
                                    console.print(f"   [dim]... and {len(files) - 10} more[/dim]")
                                
                                # Add directory listing to session context
                                file_names = [f['name'] for f in files if f.get('type') != 'directory']
                                if file_names:
                                    self.add_conversation_context(f"Directory contains files: {', '.join(file_names[:5])}")
                            elif 'content' in result:
                                # Handle simple string list format
                                files_text = result['content']
                                console.print(f"\n[cyan]📁 Directory contents:[/cyan]")
                                console.print(f"[dim]{files_text}[/dim]")
                                # Extract file names for context
                                lines = files_text.split('\n')
                                file_names = [line.strip() for line in lines if line.strip() and not line.startswith('total')]
                                if file_names:
                                    self.add_conversation_context(f"Directory contains: {', '.join(file_names[:5])}")
                        
                        elif tool == 'read_file':
                            # Handle file reading with memory storage
                            if 'content' in result:
                                content = result['content']
                                filename = arguments.get('path', 'unknown_file')
                                
                                # Add to session memory
                                self.add_file_to_memory(filename, content)
                                
                                # Show preview with syntax highlighting
                                preview = content[:500] + "..." if len(content) > 500 else content
                                file_ext = filename.split('.')[-1] if '.' in filename else 'text'
                                syntax_lang = 'python' if file_ext in ['py'] else file_ext
                                syntax = Syntax(preview, syntax_lang, theme="monokai", line_numbers=True)
                                console.print(f"\n[cyan]📄 {filename} content:[/cyan]")
                                console.print(syntax)
                                console.print(f"\n[dim]📝 Added to session memory ({len(content)} chars)[/dim]")
                        
                        elif tool == 'execute_command':
                            # Display command output
                            if 'output' in result:
                                output = result['output']
                                console.print(f"\n[cyan]💻 Command output:[/cyan]")
                                console.print(f"[dim]{output}[/dim]")
                        
                        # Display other result info
                        if 'path' in result and tool not in ['read_file', 'list_files']:
                            console.print(f"   [cyan]📁 {result['path']}[/cyan]")
                        if 'changes' in result:
                            console.print(f"   [cyan]📝 {result['changes']} changes made[/cyan]")
                        if 'output' in result and tool not in ['read_file', 'execute_command', 'list_files']:
                            console.print(f"   [cyan]💬 {result['output']}[/cyan]")
                            
                        return {"status": "success", "result": result}
                            
                    elif result.get('status') == 'error':
                        console.print(f"[red]❌ {result.get('message')}[/red]")
                        return result
                    else:
                        console.print(f"[yellow]⚠️  {result.get('message', 'Unknown status')}[/yellow]")
                        return {"status": "success", "result": result}
                else:
                    # Handle string result
                    console.print(f"[green]✅ Done[/green]")
                    console.print(f"   [cyan]💬 {str(result)}[/cyan]")
                    return {"status": "success", "output": str(result)}
        except asyncio.TimeoutError:
            console.print(f"[red]❌ Tool execution timed out[/red]")
            return {"status": "error", "message": "Tool execution timed out"}
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            return {"status": "error", "message": str(e)}
    
    async def execute_task(self, user_request: str):
        """Execute full task"""
        # Check if this is a simple conversation that doesn't need tools
        if self.is_simple_conversation(user_request):
            await self.handle_conversation(user_request)
            return
            
        # Analyze context for complex tasks
        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), console=console) as progress:
            task = progress.add_task("🔍 Analyzing...", total=None)
            try:
                context = await self.client.call_tool("analyze_project", {"path": "."})
                if isinstance(context, str):
                    context = json.loads(context)
                
                # Save project context to memory
                self.session_memory["project_context"] = context
                
                progress.update(task, completed=True)
                console.print(f"[cyan]📦 Project:[/cyan] {context.get('project_type', 'unknown')}")
                console.print(f"[cyan]📊 Files:[/cyan] {context.get('total_files', 0)}\n")
            except:
                progress.update(task, completed=True)
        
        # Plan
        plan = await self.plan_task(user_request)
        if not plan.get('steps'):
            console.print("[red]❌ Could not create plan[/red]\n")
            return
        
        # Display
        self.display_plan(plan)
        
        # Confirm
        if not Confirm.ask("[bold green]🚀 Execute?[/bold green]", default=True):
            console.print("[yellow]❌ Cancelled[/yellow]\n")
            return
        
        # Execute
        results = []
        total = len(plan['steps'])
        
        console.print("\n")
        console.print(Panel(f"Executing {total} steps...", border_style="cyan", box=box.DOUBLE))
        
        for step in plan['steps']:
            result = await self.execute_step(step, step['step'], total)
            results.append(result)
            
            if result.get('status') == 'error':
                if not Confirm.ask("\n[yellow]Error. Continue?[/yellow]", default=False):
                    break
        
        # Summary
        success = sum(1 for r in results if r.get('status') == 'success')
        console.print("\n")
        console.print(Panel(
            f"[green]✅ Completed {success}/{total} steps[/green]",
            title="[bold green]Summary[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))
        console.print("\n")
    
    def is_simple_conversation(self, user_request: str) -> bool:
        """Check if request is simple conversation vs coding task"""
        simple_keywords = [
            'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'what are you', 'who are you', 'thanks', 'thank you', 'bye', 'goodbye',
            'what can you do', 'help me understand', 'explain', 'tell me about'
        ]
        
        # Questions about files in memory should be simple conversations
        memory_questions = [
            'what does', 'how does', 'explain the', 'what is', 'can you explain',
            'what are the', 'how do', 'why does', 'where is', 'what happens'
        ]
        
        coding_keywords = [
            'create', 'write', 'build', 'make', 'develop', 'code', 'implement', 'fix', 'debug',
            'install', 'run', 'execute', 'test', 'read', 'open', 'show', 'display', 
            'list', 'find', 'search', 'analyze', 'check'
        ]
        
        request_lower = user_request.lower()
        
        # Check for simple conversation patterns
        for keyword in simple_keywords:
            if keyword in request_lower:
                return True
        
        # Check if asking about files already in memory
        if self.session_memory["files_read"]:
            for filename in self.session_memory["files_read"].keys():
                if filename.lower() in request_lower:
                    # If asking about a file in memory, treat as conversation
                    for mem_q in memory_questions:
                        if mem_q in request_lower:
                            return True
                
        # Check for coding keywords - if found, it's not simple
        for keyword in coding_keywords:
            if keyword in request_lower:
                return False
                
        # If request is very short and doesn't contain coding terms, treat as simple
        return len(user_request.split()) <= 5
    
    async def handle_conversation(self, user_request: str):
        """Handle simple conversation without tools"""
        try:
            # Get session context
            session_context = self.get_session_context()
            
            # Build intelligent context-aware prompt
            context_prompt = f"""You are an intelligent AI coding assistant with memory of our session.

SESSION CONTEXT:
{session_context}

USER REQUEST: "{user_request}"

Instructions:
- If greeting, greet back and mention what files/context you remember from this session
- If asking about files you've read, use the session context to provide detailed answers
- If asking "what files did you see" or similar, list the specific files from session context
- If asking about code/files, reference what you know from session memory with specific details
- If asking what you can do, explain your coding capabilities
- Be conversational, helpful, and use the session context intelligently
- Give specific answers based on what you actually know from the session

Keep responses informative and reference specific files/context when relevant."""

            response = ollama.chat(
                model=self.current_model,
                messages=[{"role": "user", "content": context_prompt}]
            )
            
            ai_response = response['message']['content']
            
            # Add to conversation context
            self.add_conversation_context(f"User: {user_request} | Assistant: {ai_response[:100]}...")
            
            console.print(f"\n[bold green]🤖 Assistant:[/bold green] {ai_response}\n")
            
        except Exception as e:
            console.print(f"[red]❌ Error generating response: {e}[/red]\n")
    
    async def interactive_mode(self):
        """Main loop"""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🤖 Autonomous AI Coding Assistant[/bold cyan]\n\n"
            "[dim]Commands: /model /clear /help /session /history /context /quit[/dim]\n"
            "[dim]Tip: Press ↑↓ for history, type / for commands[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        console.print("\n")

        # Create prompt session with history and completion
        session = PromptSession(
            history=InMemoryHistory(),
            completer=CommandCompleter(),
            complete_while_typing=True
        )

        while True:
            try:
                # Get input with prompt_toolkit (supports history and completion)
                model_name = self.current_model.split(':')[0]
                user_input_raw = await session.prompt_async(
                    HTML(f'<cyan><b>👤 You</b></cyan> <dim>({model_name})</dim> ')
                )
                user_input = user_input_raw.strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    cmd = user_input[1:].lower()
                    
                    if cmd in ['quit', 'exit', 'q']:
                        console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                        break
                    elif cmd == 'model':
                        self.change_model()
                        continue
                    elif cmd == 'clear':
                        console.clear()
                        console.print("[green]🗑️  Cleared[/green]\n")
                        continue
                    elif cmd == 'session':
                        self.show_session_memory()
                        continue
                    elif cmd == 'history':
                        console.print("\n[bold cyan]📜 Command History[/bold cyan]\n")
                        history_items = list(session.history.load_history_strings())
                        if history_items:
                            for i, item in enumerate(history_items[-20:], 1):  # Show last 20
                                console.print(f"  {i}. {item}")
                        else:
                            console.print("[dim]No history yet[/dim]")
                        console.print()
                        continue
                    elif cmd.startswith('context'):
                        # Show or set context length
                        console.print("\n[bold cyan]📏 Context Management[/bold cyan]")
                        console.print("[dim]Context length management coming soon...[/dim]\n")
                        continue
                    elif cmd == 'help':
                        console.print("\n[bold]Commands:[/bold]")
                        console.print("  /model    - Switch AI model")
                        console.print("  /clear    - Clear screen")
                        console.print("  /session  - Show session memory")
                        console.print("  /history  - Show command history")
                        console.print("  /context  - Manage context length")
                        console.print("  /help     - Show this help")
                        console.print("  /quit     - Exit assistant\n")
                        console.print("[dim]Tips:[/dim]")
                        console.print("  • Press ↑/↓ to navigate command history")
                        console.print("  • Type / to see available commands\n")
                        continue
                    else:
                        console.print(f"[red]Unknown command: /{cmd}[/red]")
                        console.print("[dim]Type /help for available commands[/dim]\n")
                        continue
                
                await self.execute_task(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except EOFError:
                console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except Exception as e:
                console.print(f"[red]❌ {e}[/red]\n")
    
    async def run(self, http_url: str = None):
        """Start agent"""
        console.clear()
        console.print(Panel.fit(
            "[bold magenta]🚀 Autonomous Coding Assistant[/bold magenta]",
            border_style="magenta",
            box=box.DOUBLE
        ))
        console.print("\n")

        # Get workspace using prompt_toolkit
        workspace_session = PromptSession()
        try:
            workspace = await workspace_session.prompt_async(
                HTML('<cyan>📁 Workspace</cyan> <dim>(default: .)</dim>: ')
            )
            workspace = workspace.strip() or "."
        except (EOFError, KeyboardInterrupt):
            workspace = "."
            console.print("[dim]Using current directory[/dim]")

        # Determine connection mode
        if http_url:
            # HTTP mode - connect to standalone server
            console.print(f"[cyan]🌐 Connecting to HTTP server: {http_url}[/cyan]")
            console.print("\n")
            self.client = MCPClient(workspace=workspace, http_url=http_url)
        else:
            # Stdio mode - auto-start server
            client_dir = Path(__file__).parent.resolve()
            project_root = client_dir.parent
            server_path = project_root / "mcp-server" / "server.py"

            if not server_path.exists():
                console.print(f"[red]❌ Server not found at: {server_path}[/red]")
                return

            console.print(f"[dim]Starting MCP server: {server_path.name}[/dim]")
            console.print("\n")
            self.client = MCPClient(server_path=str(server_path), workspace=workspace)
        
        try:
            with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), console=console) as progress:
                task = progress.add_task("🔗 Connecting...", total=None)

                # Connect to server
                if not await self.client.start():
                    console.print("[red]❌ Failed to connect to MCP server[/red]")
                    return

                # Load tools
                progress.update(task, description="📋 Loading tools...")
                self.available_tools = await self.client.list_tools()

                # Complete progress
                progress.update(task, description="✅ Connected")
                progress.update(task, completed=True)
            
            # Load models outside progress context to avoid conflicts
            self.load_available_models()
            
            info_table = Table(box=box.SIMPLE, show_header=False)
            info_table.add_column("Item", style="cyan")
            info_table.add_column("Value", style="white")
            info_table.add_row("Workspace", workspace)
            info_table.add_row("Tools", str(len(self.available_tools)))
            info_table.add_row("Model", self.current_model)
            
            console.print("\n")
            console.print(Panel(info_table, title="[green]✅ Connected[/green]", border_style="green"))
            
            await self.interactive_mode()

        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
        finally:
            if self.client:
                await self.client.close()

async def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Coding Assistant")
    parser.add_argument(
        "--http",
        type=str,
        default=None,
        metavar="URL",
        help="Connect to HTTP MCP server (e.g., http://localhost:8000). Default: stdio mode (auto-start server)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistral-nemo:12b-instruct-2407-q2_K",
        help="Default Ollama model to use"
    )

    args = parser.parse_args()

    agent = AutonomousCodingAgent(default_model=args.model)
    await agent.run(http_url=args.http)

if __name__ == "__main__":
    asyncio.run(main())