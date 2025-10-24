#!/usr/bin/env python3
"""
FastAPI backend for Education Insights Chat UI
Runs multi-agent system directly
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import the agent system
from agents.root_agent import create_root_agent
from agents.config import get_config
from main import create_runner_state

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize agent system
print("🚀 Initializing Education Insights Agent System...")
config = get_config()
root_agent = create_root_agent(
    project_id=config.project_id,
    dataset=config.bigquery_dataset
)
print(f"✅ Agents initialized for project: {config.project_id}")

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default-user"
    user_role: Optional[str] = "parent"  # parent, educator, policymaker
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_type: Optional[str] = None
    status: str = "success"

@app.on_event("startup")
async def startup_event():
    """Startup message"""
    print("\n" + "="*70)
    print("✅ Education Insights Agent System Ready")
    print("="*70)
    print(f"   Project: {config.project_id}")
    print(f"   Dataset: {config.bigquery_dataset}")
    print(f"   Model: {config.model_name}")
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
        "agent": "ready",
        "project": config.project_id,
        "dataset": config.bigquery_dataset
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat endpoint - runs multi-agent system to answer education queries
    """
    try:
        print(f"\n📨 User ({message.user_role}): {message.message}")
        print(f"   Processing with Education Insights Agent System...")
        
        # Import the BigQuery tools
        from tools.bigquery_tools import (
            find_high_need_low_tech_spending,
            find_high_graduation_low_funding,
            find_strong_stem_low_class_size,
            get_school_data
        )
        
        # Create a mock context for tools (inheriting from dict for __setitem__ support)
        class MockState(dict):
            def __init__(self):
                super().__init__()
                self['project_id'] = config.project_id
                self['bigquery_dataset'] = config.bigquery_dataset
            
            def get(self, key, default=None):
                return super().get(key, default)
        
        class MockContext:
            def __init__(self):
                self.state = MockState()
        
        tool_context = MockContext()
        
        # Analyze the query and call appropriate tool
        query_lower = message.message.lower()
        response_text = None
        
        # Check for research question patterns
        if "low-income" in query_lower and ("technology spending" in query_lower or "tech spending" in query_lower):
            print("   → Q1: High need + low tech spending")
            result = find_high_need_low_tech_spending(limit=5, tool_context=tool_context)
            if result['status'] == 'success':
                response_text = f"**🎯 Grant Priority Schools** (High Low-Income % + Low Tech Spending)\n\n{result['summary']}"
            else:
                response_text = result.get('message', 'No data found.')
                
        elif ("high graduation" in query_lower or "graduation rate" in query_lower) and ("low funding" in query_lower or "below-average funding" in query_lower or "despite" in query_lower):
            print("   → Q2: High graduation + low funding")
            result = find_high_graduation_low_funding(limit=10, tool_context=tool_context)
            if result['status'] == 'success':
                response_text = f"**⭐ High-Performing High-Need Schools**\n\n{result['summary']}"
            else:
                response_text = result.get('message', 'No data found.')
                
        elif "stem" in query_lower and ("class size" in query_lower or "small class" in query_lower):
            print("   → Q3: STEM programs + small classes")
            result = find_strong_stem_low_class_size(limit=10, tool_context=tool_context)
            if result['status'] == 'success':
                response_text = f"**🔬 STEM Excellence with Small Classes**\n\n{result['summary']}"
            else:
                response_text = result.get('message', 'No data found.')
        
        # If no specific pattern matched, provide helpful guidance
        if response_text is None:
            print("   → General query")
            response_text = f"""I can help you with these specific research questions about California schools (2018 data):

**1. Grant Priority Schools** 🎯
Ask: "Identify schools with highest low-income students and lowest tech spending"

**2. High-Performing Despite Challenges** ⭐  
Ask: "Find schools with high graduation rates despite below-average funding"

**3. STEM Excellence** 🔬
Ask: "Find schools with strong STEM programs and low class sizes"

**Your question:** "{message.message}"

Try rephrasing your question to match one of these research areas, or ask about a specific county, district, or school!"""
        
        print(f"✅ Response generated ({len(response_text)} chars)")
        
        return ChatResponse(
            response=response_text,
            user_type=message.user_role,
            status="success"
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response=f"I apologize, but I encountered an error processing your request: {str(e)}",
            status="error"
        )

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.getenv("PORT", "8080"))
    
    print(f"🌐 Starting Education Insights API on port {port}...")
    print(f"📊 Chat UI: http://localhost:{port}")
    print(f"🔧 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
