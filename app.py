"""Root Web Application Runner for AI Finance Controller Copilot."""
import argparse
import sys
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch AI Finance Controller Web Server & Copilot")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"Starting AI Finance Controller Dashboard on http://{args.host}:{args.port}")
    uvicorn.run("chat.server:app", host=args.host, port=args.port, reload=args.reload)
