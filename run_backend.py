#!/usr/bin/env python3
"""
Startup script to run the Azure RAG backend server.

Run with: python run_backend.py
"""

import uvicorn
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("Starting Azure RAG Backend Server...")
    print("API will be available at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
