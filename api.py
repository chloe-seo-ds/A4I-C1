#!/usr/bin/env python3
"""
FastAPI backend for Education Insights Chat UI
Connects to Cloud Run deployed agent
"""

import os
import requests
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(title="Education Insights API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloud Run service configuration
CLOUD_RUN_BASE_URL = "https://my-agent-service-191692372619.us-central1.run.app"
AGENT_APP_NAME = "my-agent"

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default-user"
    session_id: Optional[str] = None  # Let agent auto-generate if not provided

class ChatResponse(BaseModel):
    response: str
    user_type: Optional[str] = None
    status: str = "success"

@app.on_event("startup")
async def startup_event():
    """Check connection to Cloud Run service"""
    print("\n" + "="*70)
    print("🚀 Connecting to Cloud Run Agent Service...")
    print("="*70)
    print(f"   URL: {CLOUD_RUN_BASE_URL}")
    print(f"   App: {AGENT_APP_NAME}")
    
    # Try to ping the service
    try:
        response = requests.get(f"{CLOUD_RUN_BASE_URL}/health", timeout=5)
        print(f"✅ Service is reachable!")
    except Exception as e:
        print(f"⚠️  Could not reach health endpoint: {e}")
        print(f"   (This is OK if the service doesn't have /health)")
    
    print("="*70 + "\n")

@app.get("/")
async def root():
    """Serve the chat UI"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Error: static/index.html not found</h1>", status_code=404)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cloud_run_url": CLOUD_RUN_BASE_URL,
        "agent_app": AGENT_APP_NAME
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat endpoint - sends message to Cloud Run agent and returns response
    """
    try:
        print(f"\n📨 User: {message.message}")
        print(f"   Calling Cloud Run service...")
        
        # Build the request to the Cloud Run service
        # The ADK dev-ui typically exposes an API at /api/agent/chat or similar
        
        # Try different possible endpoints
        endpoints_to_try = [
            f"{CLOUD_RUN_BASE_URL}/api/agent/chat",
            f"{CLOUD_RUN_BASE_URL}/api/chat",
            f"{CLOUD_RUN_BASE_URL}/chat",
            f"{CLOUD_RUN_BASE_URL}/query",
        ]
        
        payload = {
            "message": message.message,
            "user_id": message.user_id,
            "session_id": message.session_id,
            "app": AGENT_APP_NAME
        }
        
        response_data = None
        successful_endpoint = None
        
        for endpoint in endpoints_to_try:
            try:
                print(f"   Trying: {endpoint}")
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    successful_endpoint = endpoint
                    print(f"   ✅ Success with endpoint: {endpoint}")
                    break
                else:
                    print(f"   ❌ Status {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️  Timeout")
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        if response_data is None:
            # If all endpoints failed, provide helpful error
            raise HTTPException(
                status_code=500,
                detail=f"Could not connect to agent service. Tried endpoints: {endpoints_to_try}"
            )
        
        # Extract response text
        if isinstance(response_data, dict):
            response_text = response_data.get("response", 
                                             response_data.get("output",
                                             response_data.get("message", str(response_data))))
        else:
            response_text = str(response_data)
        
        print(f"🤖 Agent response: {len(response_text)} chars")
        
        # Detect user type from message
        msg_lower = message.message.lower()
        user_type = None
        if "parent" in msg_lower:
            user_type = "parent"
        elif "teacher" in msg_lower or "educator" in msg_lower:
            user_type = "educator"
        elif "official" in msg_lower or "board" in msg_lower:
            user_type = "official"
        
        return ChatResponse(
            response=response_text,
            user_type=user_type,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.getenv("PORT", "8080"))
    
    print(f"🌐 Starting Education Insights API on port {port}...")
    print(f"📊 Chat UI: http://localhost:{port}")
    print(f"🔧 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
