import uvicorn
import os

if __name__ == "__main__":
    print("\n" + "="*60)
    print("      🚀 AI BOT - DEVELOPMENT SANDBOX (PORT 8002)")
    print("="*60)
    print("⚠️ This server is isolated. Edits here will NOT crash your main bot.")
    print("🔗 API URL: http://127.0.0.1:8002")
    print("="*60 + "\n")
    
    # Run from the current directory, point to the Backend_sandbox.main:app
    uvicorn.run("Backend_sandbox.main:app", host="127.0.0.1", port=8002, reload=True)
