"""Frontend development server launcher."""
import subprocess
import os
import sys
from pathlib import Path

def start_frontend():
    """Start the Next.js frontend development server."""
    # Get the project root (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent.parent
    frontend_dir = project_root / "monopoly-dashboard"
    
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        sys.exit(1)
    
    print("🚀 Starting Next.js frontend on port 3000...")
    print(f"📁 Directory: {frontend_dir}")
    print("")
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing dependencies first...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        print("")
    
    try:
        subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
        sys.exit(0)


def start_full_stack():
    """Start both backend and frontend servers."""
    import asyncio
    import signal
    
    # Get the project root
    project_root = Path(__file__).parent.parent.parent.parent
    frontend_dir = project_root / "monopoly-dashboard"
    
    print("🎲 Starting Monopoly Agents Full Stack")
    print("=" * 50)
    print("")
    
    # Check if frontend exists
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        sys.exit(1)
    
    # Install frontend dependencies if needed
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        print("")
    
    processes = []
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down all services...")
        for proc in processes:
            proc.terminate()
        print("👋 All services stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend (using the dev server)
        print("🔧 Starting backend on port 8080...")
        from scripts.python.server import dev
        backend_proc = subprocess.Popen(
            [sys.executable, "-c", "from scripts.python.server import dev; dev()"],
            cwd=project_root / "agents"
        )
        processes.append(backend_proc)
        
        # Wait a bit for backend to start
        import time
        time.sleep(2)
        
        # Start frontend
        print("🎨 Starting frontend on port 3000...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir
        )
        processes.append(frontend_proc)
        
        print("")
        print("=" * 50)
        print("✅ Full stack is running!")
        print("")
        print("📊 Dashboard:  http://localhost:3000")
        print("🔌 API:        http://localhost:8080/api")
        print("🌐 WebSocket:  ws://localhost:8080/ws")
        print("")
        print("Press Ctrl+C to stop all services")
        print("=" * 50)
        print("")
        
        # Wait for processes
        for proc in processes:
            proc.wait()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        for proc in processes:
            proc.terminate()
        sys.exit(1)


if __name__ == "__main__":
    start_frontend()
