#!/usr/bin/env python3
"""
Autonomous AI Coding Assistant - WORKING VERSION
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Optional
import ollama

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

class MCPClient:
    """Simple MCP client"""
    
    def __init__(self, server_path: str, workspace: str):
        self.server_path = server_path
        self.workspace = workspace
        self.process = None
        self.request_id = 0
        
    async def start(self):
        """Start the MCP server"""
        # Start server process
        self.process = await asyncio.create_subprocess_exec(
            "python3", self.server_path, "--stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(os.environ), "WORKSPACE_PATH": self.workspace}
        )
        
        # Wait for server to be ready
        await asyncio.sleep(2)
        
        # Initialize MCP connection
        await self.send_request("initialize", {
            "protocolVersion": "2024-11-05", 
            "capabilities": {},
            "clientInfo": {"name": "client", "version": "1.0.0"}
        })
        
        response = await self.read_response()
        if response is None:
            return False
            
        # Send initialized notification (required by MCP protocol)
        await self.send_request("notifications/initialized", None)
        
        return True
    
    async def send_request(self, method: str, params):
        """Send JSON-RPC request"""
        request = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        # Notifications don't have IDs
        if method.startswith("notifications/"):
            if params is not None:
                request["params"] = params
        else:
            self.request_id += 1
            request["id"] = self.request_id
            if params is not None:
                request["params"] = params
                
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()
        
    async def read_response(self) -> Optional[dict]:
        """Read JSON-RPC response"""
        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=10.0)
            if line:
                return json.loads(line.decode())
        except:
            pass
        return None
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool"""
        await self.send_request("tools/call", {"name": tool_name, "arguments": arguments})
        response = await self.read_response()
        if response and "result" in response:
            result = response["result"]
            # Handle FastMCP format - extract from content if needed
            if isinstance(result, dict) and "content" in result:
                if isinstance(result["content"], list) and len(result["content"]) > 0:
                    first_content = result["content"][0]
                    if first_content.get("type") == "text":
                        try:
                            # Try to parse as JSON
                            return json.loads(first_content["text"])
                        except:
                            # Return as text if not JSON
                            return {"status": "success", "content": first_content["text"]}
            return result
        return {"status": "error", "message": "No response"}
    
    async def list_tools(self) -> list:
        """List available tools"""
        await self.send_request("tools/list", {})
        response = await self.read_response()
        if response and "result" in response:
            return response["result"].get("tools", [])
        return []
    
    async def close(self):
        """Close the connection"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

class AutonomousCodingAgent:
    def __init__(self, default_model="mistral-nemo:12b-instruct-2407-q2_K"):
        self.client = None
        self.available_tools = []
        self.current_model = default_model
        self.available_models = []
        self.conversation_history = []
    
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
            
            planning_prompt = f"""User request: "{user_request}"

Create an execution plan. Return ONLY valid JSON:
{{
  "understanding": "what user wants",
  "steps": [
    {{
      "step": 1,
      "action": "description",
      "tool": "tool_name",
      "arguments": {{}},
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

IMPORTANT: Set "needs_approval" to true ONLY for:
- write_file, edit_file (file modifications)
- execute_command (running commands)
- create_directory (creating directories)

Set "needs_approval" to false for safe operations like:
- read_file, list_files, get_file_info (reading)
- analyze_project, search_code (analysis)

Use EXACT parameter names from signatures above. Be specific. Think step by step."""

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
                        
                        # Display file content for read operations
                        if tool == 'read_file' and 'content' in result:
                            content = result['content']
                            # Show first 500 chars with syntax highlighting
                            preview = content[:500] + "..." if len(content) > 500 else content
                            syntax = Syntax(preview, "python", theme="monokai", line_numbers=True)
                            console.print(f"\n[cyan]📄 File content:[/cyan]")
                            console.print(syntax)
                            console.print(f"\n[dim]Total length: {len(content)} characters[/dim]")
                        
                        # Display other result info
                        if 'path' in result:
                            console.print(f"   [cyan]📁 {result['path']}[/cyan]")
                        if 'changes' in result:
                            console.print(f"   [cyan]📝 {result['changes']} changes made[/cyan]")
                        if 'output' in result and tool != 'read_file':
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
        
        coding_keywords = [
            'create', 'write', 'build', 'make', 'develop', 'code', 'implement', 'fix', 'debug',
            'file', 'function', 'class', 'variable', 'install', 'run', 'execute', 'test',
            'read', 'open', 'show', 'display', 'list', 'find', 'search', 'analyze', 'check'
        ]
        
        request_lower = user_request.lower()
        
        # Check for simple conversation patterns
        for keyword in simple_keywords:
            if keyword in request_lower:
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
            response = ollama.chat(
                model=self.current_model,
                messages=[{
                    "role": "user", 
                    "content": f"""You are a helpful AI coding assistant. The user said: "{user_request}"
                    
Respond naturally and helpfully. If they're greeting you, greet them back and briefly explain what you can help with.
If they're asking what you can do, explain that you're a coding assistant that can help with:
- Creating and editing files
- Running commands  
- Analyzing projects
- Debugging code
- And more coding tasks

Keep your response concise and friendly."""
                }]
            )
            
            ai_response = response['message']['content']
            
            console.print(f"\n[bold green]🤖 Assistant:[/bold green] {ai_response}\n")
            
        except Exception as e:
            console.print(f"[red]❌ Error generating response: {e}[/red]\n")
    
    async def interactive_mode(self):
        """Main loop"""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🤖 Autonomous AI Coding Assistant[/bold cyan]\n\n"
            "[dim]Commands: /model /clear /help /quit[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        console.print("\n")
        
        while True:
            try:
                user_input = Prompt.ask(
                    f"[bold cyan]👤 You[/bold cyan] [dim]({self.current_model.split(':')[0]})[/dim]"
                ).strip()
                
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
                    elif cmd == 'help':
                        console.print("\n[bold]Commands:[/bold]")
                        console.print("  /model - Change model")
                        console.print("  /clear - Clear screen")
                        console.print("  /quit  - Exit\n")
                        continue
                    else:
                        console.print(f"[red]Unknown: /{cmd}[/red]\n")
                        continue
                
                await self.execute_task(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[cyan]👋 Goodbye![/cyan]\n")
                break
            except Exception as e:
                console.print(f"[red]❌ {e}[/red]\n")
    
    async def run(self):
        """Start agent"""
        console.clear()
        console.print(Panel.fit(
            "[bold magenta]🚀 Autonomous Coding Assistant[/bold magenta]",
            border_style="magenta",
            box=box.DOUBLE
        ))
        console.print("\n")
        
        workspace = Prompt.ask("[cyan]📁 Workspace[/cyan]", default=".")
        server_path = "/Users/pranavkrishnadanda/Downloads/agents_with_mcp/coding-assistant/mcp-server/server.py"
        
        # Validate server path
        if not os.path.exists(server_path):
            console.print(f"[red]❌ Server not found at: {server_path}[/red]")
            console.print("[yellow]Please ensure you're running from the correct directory[/yellow]")
            return
        
        console.print("\n")
        self.client = MCPClient(server_path, workspace)
        
        try:
            with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), console=console) as progress:
                task = progress.add_task("🔗 Connecting...", total=None)
                
                # Start server with timeout
                await asyncio.wait_for(self.client.start(), timeout=30.0)
                
                # Load tools with timeout
                progress.update(task, description="📋 Loading tools...")
                self.available_tools = await asyncio.wait_for(
                    self.client.list_tools(), 
                    timeout=10.0
                )
                
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
                
        except asyncio.TimeoutError:
            console.print("[red]❌ Connection timed out[/red]")
            console.print("[yellow]Please check if the server is running correctly[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Connection failed: {e}[/red]")
            console.print("[yellow]Please check the server logs for more details[/yellow]")
        finally:
            if self.client:
                await self.client.close()

async def main():
    agent = AutonomousCodingAgent(default_model="mistral-nemo:12b-instruct-2407-q2_K")
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())