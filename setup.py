#!/usr/bin/env python3
"""
Setup script for the Autonomous AI Coding Assistant
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Setup the coding assistant"""
    print("🚀 Setting up Autonomous AI Coding Assistant")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("mcp-client").exists() or not Path("mcp-server").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install server dependencies
    print("\n📦 Installing server dependencies...")
    if not run_command("cd mcp-server && pip install -r requirements.txt", "Server dependencies installation"):
        print("⚠️  Server dependencies installation failed, but continuing...")
    
    # Install client dependencies
    print("\n📦 Installing client dependencies...")
    if not run_command("cd mcp-client && pip install -r requirements.txt", "Client dependencies installation"):
        print("⚠️  Client dependencies installation failed, but continuing...")
    
    # Check if Ollama is installed
    print("\n🤖 Checking for Ollama...")
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed")
        else:
            print("⚠️  Ollama not found. Please install Ollama from https://ollama.ai/")
    except:
        print("⚠️  Could not check Ollama installation")
    
    print("\n🎉 Setup completed!")
    print("\nTo run the assistant:")
    print("  cd mcp-client")
    print("  python client.py")
    print("\nMake sure Ollama is running and you have a model installed:")
    print("  ollama pull mistral-nemo:12b-instruct-2407-q2_K")

if __name__ == "__main__":
    main()
