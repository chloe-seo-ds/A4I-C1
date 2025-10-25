#!/usr/bin/env python3
"""
FastAPI backend for Education Insights Chat UI
Runs multi-agent system directly
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
async def chat(
    message: str = Form(...),
    user_role: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Chat endpoint - runs multi-agent system to answer education queries
    Supports multimodal inputs: text + optional image/PDF file
    """
    try:
        # Initialize system on first request
        initialize_system()
        
        file_info = ""
        if file:
            file_info = f" + 📎 {file.filename}"
        
        print(f"\n📨 User ({user_role}): {message}{file_info}")
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
        query_lower = message.lower()
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
                    query=message,
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
                    query=message,
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
                    query=message,
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
            print("   → General query - using Root Agent (ADK)")
            
            try:
                # Use Google Generative AI with API key for general questions
                # Note: Specific research questions use ADK agents via BigQuery tools above
                import google.genai as genai
                
                # Configure with API key (from environment variable)
                # Use vertexai=False to ensure we use Google AI API, not Vertex AI
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY environment variable not set")
                
                client = genai.Client(api_key=api_key, vertexai=False)
                
                # Process uploaded file if present
                file_bytes = None
                file_mime_type = None
                if file:
                    file_bytes = await file.read()
                    file_size_mb = len(file_bytes) / (1024 * 1024)
                    
                    # Check file size limits
                    if file.content_type.startswith('image/') and file_size_mb > 10:
                        raise HTTPException(status_code=400, detail="Image file too large. Max 10MB.")
                    elif file.content_type == 'application/pdf' and file_size_mb > 20:
                        raise HTTPException(status_code=400, detail="PDF file too large. Max 20MB.")
                    
                    # Store file info for Gemini
                    file_mime_type = file.content_type
                    print(f"   → File processed: {file.filename} ({file_size_mb:.2f}MB, {file_mime_type})")
                
                # Create a contextualized prompt for the role
                file_context = ""
                if file:
                    file_context = f"\n\nThe user has attached a file ({file.filename}). Please analyze it in the context of their question."
                
                system_instruction = f"""You are an education expert assistant helping {user_role}s make informed decisions about schools and education.

Provide helpful, practical advice based on education best practices. When asked for school recommendations, provide SPECIFIC school names, locations, and details whenever possible.

Answer questions directly with concrete recommendations and examples. Be specific and actionable.

Keep responses clear, detailed, and tailored to a {user_role}'s perspective.

Note: For data-driven comparisons about California schools (2018 data), I can also provide detailed analytics about:
- Schools with high low-income students and low tech spending
- Schools with high graduation rates despite low funding
- Schools with strong STEM programs and small class sizes{file_context}"""
                
                # Build contents for Gemini (multimodal if file present)
                if file_bytes and file_mime_type:
                    # Multimodal: Create proper content structure
                    import google.genai.types as types
                    
                    # Create parts correctly
                    text_part = types.Part(text=f"{system_instruction}\n\nUser Question: {message}")
                    image_part = types.Part(inline_data=types.Blob(mime_type=file_mime_type, data=file_bytes))
                    
                    contents = [text_part, image_part]
                else:
                    # Text only
                    contents = f"{system_instruction}\n\nUser Question: {message}"
                
                # Generate response using gemini-2.5-flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents
                )
                
                agent_response = response.text
                print(f"   → Gemini 2.5 response length: {len(agent_response)}")
                
                # Format as HTML with clean styling - convert markdown to HTML
                import html
                import re
                
                # Convert markdown to HTML
                formatted_text = agent_response
                
                # Headings: ### text -> styled heading
                formatted_text = re.sub(r'^#### (.*?)$', r'<h4 style="color: #374151; font-size: 1rem; margin: 1rem 0 0.5rem 0; font-weight: 600;">\1</h4>', formatted_text, flags=re.MULTILINE)
                formatted_text = re.sub(r'^### (.*?)$', r'<h3 style="color: #1f2937; font-size: 1.1rem; margin: 1.25rem 0 0.75rem 0; font-weight: 600;">\1</h3>', formatted_text, flags=re.MULTILINE)
                formatted_text = re.sub(r'^## (.*?)$', r'<h2 style="color: #1f2937; font-size: 1.25rem; margin: 1.5rem 0 1rem 0; font-weight: 700;">\1</h2>', formatted_text, flags=re.MULTILINE)
                formatted_text = re.sub(r'^# (.*?)$', r'<h1 style="color: #111827; font-size: 1.5rem; margin: 1.5rem 0 1rem 0; font-weight: 700;">\1</h1>', formatted_text, flags=re.MULTILINE)
                
                # Bold: **text** -> <strong>text</strong>
                formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)
                
                # Italic: *text* -> <em>text</em> (but not if it's part of **)
                formatted_text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', formatted_text)
                
                # Bullet points: * item -> • item
                formatted_text = re.sub(r'^\* ', '• ', formatted_text, flags=re.MULTILINE)
                formatted_text = re.sub(r'\n\* ', '\n• ', formatted_text)
                
                # Numbered lists: enhance spacing
                formatted_text = re.sub(r'^(\d+\.)', r'<strong>\1</strong>', formatted_text, flags=re.MULTILINE)
                
                # Preserve line breaks
                formatted_response = formatted_text.replace('\n', '<br>')
                
                response_text = f"""<div style="padding: 20px;">
<h2 style="color: #1f2937; margin-bottom: 15px;">🎓 Education Insights</h2>
<div style="background: white; padding: 20px; border-radius: 8px; line-height: 1.6; color: #374151;">
{formatted_response}
</div>
<p style="margin-top: 15px; color: #6b7280; font-size: 0.9rem;">
💡 <em>Powered by Gemini AI - Ask me anything about education, schools, or learning!</em>
</p>
</div>"""
                
            except Exception as e:
                print(f"   ⚠️ Gemini error: {e}")
                import traceback
                traceback.print_exc()
                
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

<p style="margin-top: 20px; color: #4b5563;"><strong>Your question:</strong> "{message}"</p>
<p style="color: #ef4444; margin-top: 10px;">Error: {str(e)}</p>
</div>"""
        
        print(f"✅ Response generated ({len(response_text)} chars)")
        
        return ChatResponse(
            response=response_text,
            user_type=user_role,
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

@app.post("/match_schools")
async def match_schools_endpoint(
    message: str = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    School Match Engine endpoint for K-12 school choice.
    
    Parents can:
    1. Upload documents (report cards, IEPs) OR
    2. Provide text description of their child
    
    Returns: Top 10 matched schools with scores and application strategy
    """
    try:
        # Import the school matching tools
        from mcp_servers.tools.student_profile import create_student_profile
        from mcp_servers.tools.school_matcher import (
            match_schools,
            rank_schools,
            generate_school_recommendations
        )
        from mcp_servers.tools.school_enrichment import enrich_multiple_schools
        
        print(f"\n🏫 School Match Request")
        if file:
            print(f"   📎 File: {file.filename} ({file.content_type})")
        if message:
            print(f"   💬 Message: {message[:100]}...")
        
        # Get config
        config_obj = get_config()
        
        # Process uploaded file if present
        file_bytes = None
        mime_type = None
        if file:
            file_bytes = await file.read()
            mime_type = file.content_type
            file_size_mb = len(file_bytes) / (1024 * 1024)
            print(f"   📊 File size: {file_size_mb:.2f}MB")
            
            # Validate file size
            if file_size_mb > 20:
                raise HTTPException(status_code=400, detail="File too large. Max 20MB.")
        
        # Step 1: Create student profile
        print("   🔍 Creating student profile...")
        student_profile = create_student_profile(
            text_input=message if message else None,
            file_bytes=file_bytes,
            mime_type=mime_type,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        if student_profile.get("status") == "error":
            return {
                "status": "error",
                "message": student_profile.get("message", "Failed to create student profile"),
                "html": f"<div style='padding: 20px; color: #ef4444;'>Error: {student_profile.get('message')}</div>"
            }
        
        print(f"   ✅ Profile created: Grade {student_profile.get('grade_entering', 'unknown')}, {student_profile.get('school_level_name', 'unknown')}")
        
        # Step 2: Match schools
        print("   🔎 Matching schools from BigQuery...")
        match_result = match_schools(
            student_profile=student_profile,
            project_id=config_obj.project_id,
            dataset=config_obj.bigquery_dataset,
            limit=20
        )
        
        if match_result.get("status") != "success":
            return {
                "status": "error",
                "message": match_result.get("message", "No schools found"),
                "html": f"<div style='padding: 20px;'><h3>No Schools Found</h3><p>{match_result.get('message')}</p></div>"
            }
        
        print(f"   ✅ Found {len(match_result['schools'])} schools")
        
        # Step 3: Rank schools
        print("   📊 Ranking schools...")
        ranked = rank_schools(
            schools=match_result["schools"],
            student_profile=student_profile
        )
        
        # Step 4: Enrich schools with detailed information (top 10)
        print("   🔍 Enriching top 10 schools with tours, deadlines, and program details...")
        enriched_schools = enrich_multiple_schools(
            schools=ranked[:10],
            api_key=os.getenv("GOOGLE_API_KEY"),
            max_schools=10  # Full enrichment for all top 10
        )
        
        # Step 5: Generate recommendations
        print("   🎯 Generating recommendations...")
        recommendations = generate_school_recommendations(
            ranked_schools=enriched_schools,
            student_profile=student_profile
        )
        
        print(f"   ✅ Top 10 schools ranked and enriched")
        
        # Step 5: Format as compact cards (new layout)
        html_response = _format_school_matches_compact_cards(recommendations)
        
        return {
            "status": "success",
            "html": html_response,
            "data": recommendations,
            "student_profile": student_profile
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "html": f"<div style='padding: 20px; color: #ef4444;'><h3>Error</h3><p>{str(e)}</p></div>"
        }

def _format_school_matches_compact_cards(recommendations: Dict[str, Any]) -> str:
    """
    Format school matches to match Figma design exactly.
    """
    if recommendations.get("status") != "success":
        return f"<div style='padding: 20px;'><p>{recommendations.get('message', 'No recommendations available')}</p></div>"
    
    top_schools = recommendations.get("top_10", [])
    
    # Header with gradient text and action button
    html = f"""
    <div style="padding: 0; margin: 0;">
        <!-- Header -->
        <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h2 style="font-size: 1.5rem; font-weight: 700; background: linear-gradient(to right, #2563eb, #4f46e5, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: flex; align-items: center; gap: 0.5rem; margin: 0 0 0.5rem 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="2" style="flex-shrink: 0;">
                            <path d="M12 3l1.912 5.813a2 2 0 001.272 1.272L21 12l-5.813 1.912a2 2 0 00-1.272 1.272L12 21l-1.912-5.813a2 2 0 00-1.272-1.272L3 12l5.813-1.912a2 2 0 001.272-1.272L12 3z"></path>
                        </svg>
                        Recommended Schools for Your Child
                    </h2>
                    <p style="color: #64748b; margin: 0; font-size: 0.875rem;">Based on your description, here are the top {len(top_schools)} matching schools • Includes both public and charter options</p>
                </div>
                <button onclick="window.location.reload()" style="padding: 0.625rem 1.25rem; background: white; border: 1px solid #cbd5e1; border-radius: 0.5rem; color: #475569; font-size: 0.875rem; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s;"
                        onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                    New Search
                </button>
            </div>
        </div>

        <!-- School Cards Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1rem;">
    """
    
    for i, school in enumerate(top_schools, 1):
        match_score = school.get("match_score", 0)
        school_id = school.get('ncessch', f'school_{i}')
        
        # Determine gradient color (using actual hex values)
        if match_score >= 90:
            color1, color2 = "#10b981", "#22c55e"  # emerald to green
            badge_text = "Match"
        elif match_score >= 80:
            color1, color2 = "#3b82f6", "#06b6d4"  # blue to cyan
            badge_text = "Match"
        elif match_score >= 70:
            color1, color2 = "#f59e0b", "#fb923c"  # amber to orange
            badge_text = "Match"
        else:
            color1, color2 = "#ef4444", "#f43f5e"  # red to rose
            badge_text = "Match"
        
        grad_rate = school.get('graduation_rate')
        grad_display = f"{grad_rate}%" if grad_rate else "N/A"
        
        html += f'''
        <div class="school-card-{school_id}" style="background: white; border-radius: 1rem; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.06); transition: all 0.3s; position: relative; height: 100%;" 
             onmouseover="this.style.boxShadow='0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'"
             onmouseout="this.style.boxShadow='0 2px 4px -1px rgba(0, 0, 0, 0.06)'">
            
            <!-- Match Score Badge (Top Right) -->
            <div style="position: absolute; top: 0.75rem; right: 0.75rem; z-index: 10;">
                <div style="background: linear-gradient(135deg, {color1}, {color2}); color: white; padding: 0.375rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); display: flex; align-items: center; gap: 0.25rem;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                    </svg>
                    {match_score}% {badge_text}
                </div>
            </div>

            <!-- Favorite Button (Top Left) -->
            <button onclick="toggleFavorite(this)" style="position: absolute; top: 0.75rem; left: 0.75rem; z-index: 10; padding: 0.5rem; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(4px); border: none; border-radius: 9999px; cursor: pointer; box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.1); transition: all 0.2s;"
                    onmouseover="this.style.background='white'; this.style.boxShadow='0 4px 6px -1px rgba(0, 0, 0, 0.15)'"
                    onmouseout="this.style.background='rgba(255, 255, 255, 0.9)'; this.style.boxShadow='0 2px 4px -1px rgba(0, 0, 0, 0.1)'">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" class="heart-icon">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                </svg>
            </button>
            
            <!-- Content -->
            <div style="padding: 3.5rem 1.25rem 1.25rem;">
                    <div style="margin-bottom: 1rem;">
                        <h3 style="font-size: 1.125rem; font-weight: 700; color: #0f172a; margin: 0 0 0.5rem 0; line-height: 1.375;">{school.get('school_name', 'Unknown School')}</h3>
                        <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.25rem;">
                            <span style="background: {'#3b82f6' if school.get('charter') == 1 else '#10b981'}; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600;">
                                {'CHARTER' if school.get('charter') == 1 else 'PUBLIC'}
                            </span>
                            <div style="display: flex; align-items: center; gap: 0.25rem; color: #64748b; font-size: 0.875rem;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                                    <circle cx="12" cy="10" r="3"></circle>
                                </svg>
                                {school.get('district_name', 'Unknown District')}
                            </div>
                        </div>
                    </div>

                <!-- Stats Grid -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; padding: 0.75rem 0; border-top: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; margin-bottom: 1rem;">
                    <div>
                        <p style="font-size: 0.75rem; color: #94a3b8; margin: 0 0 0.125rem 0;">Graduation Rate</p>
                        <p style="font-size: 1.125rem; font-weight: 700; color: #0f172a; margin: 0;">{grad_display}</p>
                    </div>
                    <div>
                        <p style="font-size: 0.75rem; color: #94a3b8; margin: 0 0 0.125rem 0;">Students</p>
                        <p style="font-size: 1.125rem; font-weight: 700; color: #0f172a; margin: 0;">{int(school.get('enrollment', 0)):,}</p>
                    </div>
                    <div>
                        <p style="font-size: 0.75rem; color: #94a3b8; margin: 0 0 0.125rem 0;">Funding/Student</p>
                        <p style="font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0;">${int(school.get('per_pupil_total', 0) if school.get('per_pupil_total') else 0):,}</p>
                    </div>
                    <div>
                        <p style="font-size: 0.75rem; color: #94a3b8; margin: 0 0 0.125rem 0;">Low Income</p>
                        <p style="font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0;">{school.get('low_income_pct', 'N/A')}%</p>
                    </div>
                </div>

                <!-- View Details Button -->
                <button onclick="showSchoolDetails('{school_id}')" 
                        style="width: 100%; background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%); color: white; padding: 0.625rem 1rem; border: none; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.2s;"
                        onmouseover="this.style.background='linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%)'; this.style.boxShadow='0 10px 15px -3px rgba(37, 99, 235, 0.4)'"
                        onmouseout="this.style.background='linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)'; this.style.boxShadow='0 4px 6px -1px rgba(37, 99, 235, 0.3)'">
                    View Details
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                </button>
            </div>
            
            <!-- Details Section (Hidden by default) -->
            <div id="details-{school_id}" style="display: none; padding: 1.25rem; border-top: 1px solid #f1f5f9; background: #f8fafc;"></div>
        </div>
        '''
    
    html += '</div></div>'  # Close grid
    
    # Add school data and JavaScript
    import json
    schools_json = json.dumps(top_schools, default=str)
    
    html += f'''
    <script>
        // Set global school data for use by the global functions
        window.schoolsData = {schools_json};
    </script>
    '''
    
    return html

def _format_school_matches_html(recommendations: Dict[str, Any]) -> str:
    """
    Format school recommendations as beautiful HTML.
    """
    if recommendations.get("status") != "success":
        return f"<div style='padding: 20px;'><p>{recommendations.get('message', 'No recommendations available')}</p></div>"
    
    top_schools = recommendations.get("top_10", [])
    strategy = recommendations.get("application_strategy", {})
    
    html = """
    <div style="padding: 20px; max-width: 1200px; margin: 0 auto;">
        <h1 style="color: #1f2937; margin-bottom: 10px;">🏫 Your Personalized School Matches</h1>
        <p style="color: #6b7280; margin-bottom: 30px; font-size: 1.1rem;">
            Found {count} schools matching your child's profile. Here are your top 10 recommendations:
        </p>
    """.format(count=len(top_schools))
    
    # Add application strategy box
    if strategy:
        html += """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="margin-top: 0; font-size: 1.3rem;">📋 Your Application Strategy</h2>
            <p style="font-size: 1.05rem; line-height: 1.6;">{approach}</p>
            <div style="margin-top: 15px;">
                <strong>Next Steps:</strong>
                <ul style="margin-top: 10px;">
        """.format(approach=strategy.get("recommended_approach", ""))
        
        for step in strategy.get("next_steps", [])[:4]:
            html += f"<li style='margin: 8px 0;'>{step}</li>"
        
        html += """
                </ul>
            </div>
        </div>
        """
    
    # Add school cards
    for i, school in enumerate(top_schools, 1):
        match_score = school.get("match_score", 0)
        
        # Determine color based on score
        if match_score >= 85:
            color = "#10b981"
            badge = "🌟 Excellent Match"
        elif match_score >= 70:
            color = "#3b82f6"
            badge = "✅ Good Match"
        elif match_score >= 50:
            color = "#f59e0b"
            badge = "⚠️ Fair Match"
        else:
            color = "#6b7280"
            badge = "💭 Consider"
        
        html += f"""
        <div style="background: white; border-left: 5px solid {color}; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                <div>
                    <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">#{i}</span>
                    <h3 style="margin: 10px 0 5px 0; color: #1f2937; font-size: 1.4rem;">{school.get('school_name', 'Unknown School')}</h3>
                    <p style="color: #6b7280; margin: 0;">
                        📍 {school.get('city_location', 'Unknown')}, CA<br>
                        <span style="font-size: 0.85rem;">District: {school.get('district_name', 'Unknown District')}</span>
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: bold; color: {color};">{match_score}%</div>
                    <div style="color: {color}; font-size: 0.9rem; font-weight: 600;">{badge}</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; padding: 15px; background: #f9fafb; border-radius: 6px;">
                <div>
                    <div style="color: #6b7280; font-size: 0.85rem;">Student-Teacher Ratio</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{school.get('student_teacher_ratio', 'N/A')}:1</div>
                </div>
                <div>
                    <div style="color: #6b7280; font-size: 0.85rem;">Enrollment</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{int(school.get('enrollment', 0))} students</div>
                </div>
        """
        
        # Add graduation rate for high schools
        if school.get('graduation_rate'):
            html += f"""
                <div>
                    <div style="color: #6b7280; font-size: 0.85rem;">Graduation Rate</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{school.get('graduation_rate', 'N/A')}%</div>
                </div>
            """
        
        # Add AP courses if available (only for high schools with valid data)
        ap_courses = school.get('ap_courses', 0)
        if school.get('school_level') == 3 and ap_courses and ap_courses > 0:
            html += f"""
                <div>
                    <div style="color: #6b7280; font-size: 0.85rem;">AP Courses</div>
                    <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{int(ap_courses)} offered</div>
                </div>
            """
        
        html += """
            </div>
            
            <div style="margin-top: 15px;">
                <strong style="color: #1f2937;">Why This School Matches:</strong>
                <ul style="margin-top: 8px; padding-left: 20px;">
        """
        
        for reason in school.get('match_reasoning', [])[:5]:
            html += f"<li style='margin: 5px 0; color: #374151;'>{reason}</li>"
        
        html += f"""
                </ul>
            </div>
            """
        
        # Add enriched information if available
        enrichment = school.get('enrichment', {})
        if enrichment and enrichment.get('status') == 'success':
            # Tours Section
            tours = enrichment.get('tours', [])
            if tours:
                html += """
            <div style="margin-top: 20px; padding: 15px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px;">
                <h4 style="margin: 0 0 10px 0; color: #92400e; font-size: 1rem;">📅 Upcoming Tours & Events</h4>
                """
                for tour in tours[:2]:
                    tour_type = tour.get('type', 'Event')
                    date = tour.get('date', tour.get('schedule', 'TBD'))
                    time = tour.get('time', '')
                    registration = tour.get('registration', 'Contact school')
                    html += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #78350f;">{tour_type}:</strong> {date} {time}<br>
                    <span style="font-size: 0.9rem; color: #92400e;">Registration: {registration}</span>
                </div>
                    """
                html += "</div>"
            
            # Deadlines Section
            deadlines = enrichment.get('deadlines', [])
            if deadlines:
                html += """
            <div style="margin-top: 15px; padding: 15px; background: #fecaca; border-left: 4px solid #ef4444; border-radius: 6px;">
                <h4 style="margin: 0 0 10px 0; color: #7f1d1d; font-size: 1rem;">📋 Important Deadlines</h4>
                """
                for deadline in deadlines[:3]:
                    deadline_type = deadline.get('type', 'Deadline')
                    date = deadline.get('date', 'TBD')
                    notes = deadline.get('notes', '')
                    html += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #991b1b;">{deadline_type}:</strong> {date}<br>
                    <span style="font-size: 0.9rem; color: #7f1d1d;">{notes}</span>
                </div>
                    """
                html += "</div>"
            
            # Requirements Section
            requirements = enrichment.get('requirements', [])
            if requirements:
                html += """
            <div style="margin-top: 15px; padding: 15px; background: #e0e7ff; border-left: 4px solid: #3b82f6; border-radius: 6px;">
                <h4 style="margin: 0 0 10px 0; color: #1e3a8a; font-size: 1rem;">📄 Enrollment Requirements</h4>
                <ul style="margin: 0; padding-left: 20px; color: #1e40af;">
                """
                for req in requirements[:4]:
                    html += f"<li style='margin: 5px 0; font-size: 0.9rem;'>{req}</li>"
                html += """
                </ul>
            </div>
                """
            
            # Programs Section
            programs = enrichment.get('programs', [])
            if programs:
                html += """
            <div style="margin-top: 15px; padding: 15px; background: #d1fae5; border-left: 4px solid #10b981; border-radius: 6px;">
                <h4 style="margin: 0 0 10px 0; color: #065f46; font-size: 1rem;">🎯 Programs & Services</h4>
                """
                for program in programs[:4]:
                    prog_name = program.get('name', 'Program')
                    prog_desc = program.get('description', '')
                    html += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #047857;">{prog_name}:</strong> <span style="font-size: 0.9rem; color: #065f46;">{prog_desc}</span>
                </div>
                    """
                html += "</div>"
            
            # Contact Section
            contact = enrichment.get('contact', {})
            if contact:
                phone = contact.get('phone', '')
                email = contact.get('email', '')
                website = contact.get('website', '')
                hours = contact.get('office_hours', '')
                
                html += f"""
            <div style="margin-top: 15px; padding: 15px; background: #f3f4f6; border-left: 4px solid #6b7280; border-radius: 6px;">
                <h4 style="margin: 0 0 10px 0; color: #374151; font-size: 1rem;">📞 Contact Information</h4>
                <div style="font-size: 0.9rem; color: #4b5563;">
                    {f'<div style="margin: 4px 0;"><strong>Phone:</strong> {phone}</div>' if phone else ''}
                    {f'<div style="margin: 4px 0;"><strong>Email:</strong> {email}</div>' if email else ''}
                    {f'<div style="margin: 4px 0;"><strong>Website:</strong> {website}</div>' if website else ''}
                    {f'<div style="margin: 4px 0;"><strong>Office Hours:</strong> {hours}</div>' if hours else ''}
                </div>
            </div>
                """
        
        html += """
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb;">
                <span style="background: #e0e7ff; color: #3730a3; padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; font-weight: 500;">
                    """ + school.get('admission_type', 'Unknown') + """
                </span>
            </div>
        </div>
        """
    
    html += """
        <div style="margin-top: 40px; padding: 20px; background: #f0f9ff; border-radius: 8px; border: 1px solid #bae6fd;">
            <h3 style="color: #0c4a6e; margin-top: 0;">💡 All Information Provided Above</h3>
            <p style="color: #075985;">Each school card above includes complete details about tours, deadlines, requirements, and programs - no need to contact them separately! Just scroll up to see all the information.</p>
        </div>
    </div>
    """
    
    return html

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8080
    port = int(os.getenv("PORT", "8080"))
    
    print(f"🌐 Starting Education Insights API on port {port}...")
    print(f"📊 Chat UI: http://localhost:{port}")
    print(f"🔧 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
