#!/usr/bin/env python3
"""
MCP Server using FastMCP - Simple and Clean
"""

from fastmcp import FastMCP
import os
from pathlib import Path
import subprocess
import json
import re

# Initialize FastMCP server
mcp = FastMCP("Code Assistant Server")

WORKSPACE = os.getenv("WORKSPACE_PATH", os.getcwd())

def validate_path(path: str) -> Path:
    """Validate and sanitize file paths to prevent directory traversal"""
    # Remove any path traversal attempts
    clean_path = re.sub(r'\.\./', '', path)
    clean_path = re.sub(r'\.\.\\', '', clean_path)
    
    full_path = Path(WORKSPACE) / clean_path
    
    # Ensure the path is within the workspace
    try:
        full_path.resolve().relative_to(Path(WORKSPACE).resolve())
    except ValueError:
        raise ValueError(f"Path {path} is outside workspace")
    
    return full_path

def is_safe_command(command: str) -> bool:
    """Check if command is safe to execute"""
    dangerous_patterns = [
        r'rm\s+-rf',
        r'mkfs',
        r'format',
        r'dd\s+if=',
        r'>\s*/dev/',
        r'chmod\s+777',
        r'chown\s+root',
        r'sudo',
        r'su\s+',
        r'passwd',
        r'useradd',
        r'userdel'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    return True

@mcp.tool()
def read_file(path: str) -> dict:
    """Read contents of a file"""
    try:
        file_path = validate_path(path)
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {path}"}
        
        content = file_path.read_text()
        return {
            "status": "success",
            "path": str(file_path),
            "content": content,
            "lines": len(content.split('\n')),
            "size": len(content)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def write_file(path: str, content: str) -> dict:
    """Write or create a file"""
    try:
        file_path = validate_path(path)
        exists = file_path.exists()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        
        return {
            "status": "success",
            "action": "updated" if exists else "created",
            "path": str(file_path),
            "size": len(content)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def edit_file(path: str, search: str, replace: str) -> dict:
    """Edit existing file with search and replace"""
    try:
        file_path = validate_path(path)
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {path}"}
        
        content = file_path.read_text()
        if search not in content:
            return {"status": "error", "message": "Search text not found in file"}
        
        new_content = content.replace(search, replace)
        changes_count = content.count(search)
        
        # Actually apply the changes
        file_path.write_text(new_content)
        
        return {
            "status": "success",
            "path": str(file_path),
            "search": search,
            "replace": replace,
            "changes": changes_count,
            "size": len(new_content)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def list_files(path: str = ".") -> dict:
    """List files in directory"""
    try:
        dir_path = validate_path(path)
        files = []
        for item in dir_path.iterdir():
            files.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
        
        return {
            "status": "success",
            "path": str(dir_path),
            "files": files,
            "count": len(files)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def execute_command(command: str) -> dict:
    """Execute a shell command with safety checks"""
    try:
        # Check if command is safe
        if not is_safe_command(command):
            return {"status": "error", "message": "Command contains potentially dangerous operations"}
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE
        )
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def analyze_project(path: str = ".") -> dict:
    """Analyze project structure and detect project type"""
    try:
        project_path = validate_path(path)
        files = list(project_path.glob("*"))
        file_names = [f.name for f in files]
        
        # Detect project type
        project_type = "unknown"
        if "package.json" in file_names:
            project_type = "nodejs"
        elif "requirements.txt" in file_names or "setup.py" in file_names:
            project_type = "python"
        elif "pom.xml" in file_names:
            project_type = "java"
        elif "go.mod" in file_names:
            project_type = "go"
        elif "Cargo.toml" in file_names:
            project_type = "rust"
        
        # Count files by extension
        extensions = {}
        for f in project_path.rglob("*"):
            if f.is_file():
                ext = f.suffix or "no_extension"
                extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            "status": "success",
            "path": str(project_path),
            "project_type": project_type,
            "total_files": sum(extensions.values()),
            "file_types": extensions,
            "main_files": file_names[:20]
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def search_code(query: str, path: str = ".", file_pattern: str = "*.py") -> dict:
    """Search for code patterns in files"""
    try:
        search_path = validate_path(path)
        results = []
        
        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    if query.lower() in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if query.lower() in line.lower():
                                results.append({
                                    "file": str(file_path.relative_to(search_path)),
                                    "line": i + 1,
                                    "content": line.strip(),
                                    "context": lines[max(0, i-2):i+3]
                                })
                except Exception:
                    continue
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_file_info(path: str) -> dict:
    """Get detailed information about a file"""
    try:
        file_path = validate_path(path)
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {path}"}
        
        stat = file_path.stat()
        content = file_path.read_text()
        lines = content.split('\n')
        
        return {
            "status": "success",
            "path": str(file_path),
            "size": stat.st_size,
            "lines": len(lines),
            "modified": stat.st_mtime,
            "extension": file_path.suffix,
            "is_binary": b'\x00' in content.encode('utf-8', errors='ignore')
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def create_directory(path: str) -> dict:
    """Create a directory"""
    try:
        dir_path = validate_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return {
            "status": "success",
            "path": str(dir_path),
            "action": "created"
        }
    except ValueError as e:
        return {"status": "error", "message": f"Security error: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    from starlette.routing import Route
    from starlette.responses import JSONResponse

    # Health check endpoint
    async def health_check(request):
        return JSONResponse({
            "status": "healthy",
            "service": "code-assistant-mcp-server",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def get_root(request):
        return JSONResponse({
            "name": "Code Assistant MCP Server",
            "version": "1.0.0",
            "endpoints": {
                "/": "Server info",
                "/health": "Health check",
                "/sse": "MCP communication endpoint"
            }
        })

    # Get the SSE app
    app = mcp.sse_app()

    # Add custom routes
    app.router.routes.extend([
        Route("/health", health_check, methods=["GET"]),
        Route("/", get_root, methods=["GET"]),
    ])

    # Run as web service
    print("🚀 Starting Code Assistant MCP Server on http://localhost:8000")
    print("📡 SSE endpoint: http://localhost:8000/sse")
    uvicorn.run(app, host="0.0.0.0", port=8000)