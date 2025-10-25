"""
MCP Server for Parent Services - K-12 School Match Engine

This server provides tools for:
1. Parsing student documents (report cards, IEPs)
2. Matching schools based on student profile
3. Ranking and recommending schools

Run as standalone MCP server:
    python mcp_servers/parent_services_server.py
"""
import os
import sys
import asyncio
import json
from typing import Any, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_servers.tools.student_profile import create_student_profile
from mcp_servers.tools.school_matcher import (
    match_schools,
    rank_schools,
    generate_school_recommendations
)
from mcp_servers.config import PROJECT_ID, BIGQUERY_DATASET


# Initialize MCP Server
app = Server("parent-services-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools for K-12 school matching.
    """
    return [
        Tool(
            name="create_student_profile",
            description="""Extract student profile from text description or uploaded document.
            
Use this when a parent provides information about their child (grade level, interests, needs, location).

Input parameters:
- text_input: Text description of the student (e.g., "My daughter is in 6th grade, loves math and science, needs small classes, lives in San Jose")
- file_data: (Optional) Base64-encoded file data if document uploaded
- mime_type: (Optional) MIME type of uploaded file

Returns: Structured student profile with grade level, interests, learning needs, location, etc.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "text_input": {
                        "type": "string",
                        "description": "Parent's description of their child and school needs"
                    },
                    "file_data": {
                        "type": "string",
                        "description": "Optional: Base64-encoded file data (report card, IEP, etc.)"
                    },
                    "mime_type": {
                        "type": "string",
                        "description": "Optional: MIME type of uploaded file (e.g., application/pdf, image/jpeg)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="match_and_recommend_schools",
            description="""Find and rank K-12 schools based on student profile.
            
This is the main tool for school matching. It:
1. Queries BigQuery for schools matching the student's grade level and location
2. Scores schools based on 5 factors (quality, programs, environment, location, admission)
3. Ranks schools and generates match reasoning
4. Creates personalized application strategy

Input parameters:
- student_profile: Student profile dict (from create_student_profile)
- max_schools: Maximum number of schools to return (default: 10)

Returns: Top 10+ ranked schools with match scores, reasoning, and application strategy""",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_profile": {
                        "type": "object",
                        "description": "Student profile from create_student_profile tool"
                    },
                    "max_schools": {
                        "type": "integer",
                        "description": "Maximum number of schools to return (default: 10)"
                    }
                },
                "required": ["student_profile"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute a tool by name with given arguments.
    """
    try:
        if name == "create_student_profile":
            # Extract arguments
            text_input = arguments.get("text_input")
            file_data = arguments.get("file_data")  # Base64 encoded
            mime_type = arguments.get("mime_type")
            
            # Decode file data if provided
            file_bytes = None
            if file_data:
                import base64
                file_bytes = base64.b64decode(file_data)
            
            # Create profile
            result = create_student_profile(
                text_input=text_input,
                file_bytes=file_bytes,
                mime_type=mime_type,
                api_key=os.getenv("GOOGLE_API_KEY")
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        elif name == "match_and_recommend_schools":
            # Extract arguments
            student_profile = arguments.get("student_profile", {})
            max_schools = arguments.get("max_schools", 10)
            
            # Match schools
            match_result = match_schools(
                student_profile=student_profile,
                project_id=PROJECT_ID,
                dataset=BIGQUERY_DATASET,
                limit=max_schools * 2  # Query more for better ranking
            )
            
            if match_result.get("status") != "success":
                return [TextContent(
                    type="text",
                    text=json.dumps(match_result, indent=2)
                )]
            
            # Rank schools
            ranked = rank_schools(
                schools=match_result["schools"],
                student_profile=student_profile
            )
            
            # Generate recommendations
            recommendations = generate_school_recommendations(
                ranked_schools=ranked[:max_schools],
                student_profile=student_profile
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2, default=str)
            )]
            
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}"
                })
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            })
        )]


async def main():
    """
    Main entry point - run MCP server over stdio.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("🚀 Starting Parent Services MCP Server...", file=sys.stderr)
    print(f"   Project: {PROJECT_ID}", file=sys.stderr)
    print(f"   Dataset: {BIGQUERY_DATASET}", file=sys.stderr)
    print("   Ready to help parents find the best K-12 schools!", file=sys.stderr)
    
    asyncio.run(main())

