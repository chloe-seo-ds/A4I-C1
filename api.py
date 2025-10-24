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
from agents.config import get_config
from agents.root_agent import create_root_agent

# Import the response formatter
from tools.response_formatter import format_response_with_visualizations, load_maps_api_key

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

# Global variables (lazy initialization on first request)
config = None
root_agent = None
maps_api_key = None

def initialize_system():
    """Initialize the agent system on first request"""
    global config, root_agent, maps_api_key
    if config is None:
        print("🚀 Initializing Education Insights Agent System...")
        config = get_config()
        root_agent = create_root_agent(
            project_id=config.project_id,
            dataset=config.bigquery_dataset
        )
        maps_api_key = load_maps_api_key()
        print(f"✅ Agents initialized for project: {config.project_id}")
        if maps_api_key:
            print(f"✅ Google Maps API key loaded")
        else:
            print("⚠️  Google Maps API key not found - maps will be disabled")

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
    print("="*70 +"\n")

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
    # Don't initialize on health check - just return ready
    return {
        "status": "healthy",
        "agent": "ready"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat endpoint - runs multi-agent system to answer education queries
    """
    try:
        # Initialize system on first request
        initialize_system()
        
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
        query_type = None
        data = []
        
        # Check for research question patterns
        if "low-income" in query_lower and ("technology spending" in query_lower or "tech spending" in query_lower):
            print("   → Q1: High need + low tech spending")
            result = find_high_need_low_tech_spending(limit=5, tool_context=tool_context)
            query_type = "high_need_low_tech"
            
            if result['status'] == 'success':
                data = result.get('data', [])
                state_averages = result.get('state_averages', {})
                # Use the response formatter
                formatted = format_response_with_visualizations(
                    query=message.message,
                    data=data,
                    query_type=query_type,
                    maps_api_key=maps_api_key,
                    state_averages=state_averages
                )
                response_text = formatted['full_response']
            else:
                response_text = result.get('message', 'No data found.')
                
        elif ("high graduation" in query_lower or "graduation rate" in query_lower) and ("low funding" in query_lower or "below-average funding" in query_lower or "despite" in query_lower):
            print("   → Q2: High graduation + low funding")
            result = find_high_graduation_low_funding(limit=10, tool_context=tool_context)
            query_type = "high_grad_low_funding"
            
            if result['status'] == 'success':
                data = result.get('data', [])
                state_averages = result.get('state_averages', {})
                # Use the response formatter
                formatted = format_response_with_visualizations(
                    query=message.message,
                    data=data,
                    query_type=query_type,
                    maps_api_key=maps_api_key,
                    state_averages=state_averages
                )
                response_text = formatted['full_response']
            else:
                response_text = result.get('message', 'No data found.')
                
        elif "stem" in query_lower and ("class size" in query_lower or "small class" in query_lower):
            print("   → Q3: STEM programs + small classes")
            result = find_strong_stem_low_class_size(limit=10, tool_context=tool_context)
            query_type = "stem_excellence"
            
            if result['status'] == 'success':
                data = result.get('data', [])
                state_averages = result.get('state_averages', {})
                # Use the response formatter
                formatted = format_response_with_visualizations(
                    query=message.message,
                    data=data,
                    query_type=query_type,
                    maps_api_key=maps_api_key,
                    state_averages=state_averages
                )
                response_text = formatted['full_response']
            else:
                response_text = result.get('message', 'No data found.')
        
        # If no specific pattern matched, use root_agent for general questions
        if response_text is None:
            print("   → General query - using Root Agent with Gemini")
            
            try:
                # Use the root agent to handle general education questions
                from main import create_runner_state
                
                # Create runner state with context
                state = create_runner_state(
                    query=message.message,
                    user_type=message.user_role
                )
                
                # Run the root agent
                result_state = root_agent.run(state)
                
                # Extract the response
                agent_response = result_state.get('output', '') or result_state.get('response', '')
                
                # Format as HTML
                response_text = f"""<div style="padding: 20px;">
<h2 style="color: #1f2937; margin-bottom: 15px;">🎓 Education Insights</h2>
<div style="background: white; padding: 20px; border-radius: 8px; line-height: 1.6;">
{agent_response.replace(chr(10), '<br>')}
</div>
<p style="margin-top: 15px; color: #6b7280; font-size: 0.9rem;">
💡 <em>Powered by Gemini AI with access to California education data (2018)</em>
</p>
</div>"""
                
            except Exception as e:
                print(f"   ⚠️ Root agent error: {e}")
                # Fallback to helpful message
                response_text = f"""<div style="padding: 20px;">
<h2 style="color: #1f2937; margin-bottom: 15px;">💡 How I Can Help</h2>
<p style="margin-bottom: 20px;">I can help you with education-related questions. Try asking about:</p>

<div style="background: linear-gradient(to right, #dbeafe, #f0f9ff); padding: 15px; border-radius: 8px; margin: 15px 0;">
<p style="color: #1e3a8a;">• Schools with high low-income students and low tech spending</p>
</div>

<div style="background: linear-gradient(to right, #fef3c7, #fef9c3); padding: 15px; border-radius: 8px; margin: 15px 0;">
<p style="color: #78350f;">• Schools with high graduation rates despite low funding</p>
</div>

<div style="background: linear-gradient(to right, #e9d5ff, #f3e8ff); padding: 15px; border-radius: 8px; margin: 15px 0;">
<p style="color: #581c87;">• Schools with strong STEM programs and low class sizes</p>
</div>

<p style="margin-top: 20px; color: #4b5563;"><strong>Your question:</strong> "{message.message}"</p>
<p style="color: #ef4444; margin-top: 10px;">Error: {str(e)}</p>
</div>"""
        
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
