"""
Data Agent as a Tool
Wraps data retrieval functionality to be callable as a function tool
"""
from google.adk.tools import ToolContext
from typing import Dict, Any, Optional
from tools.bigquery_tools import get_school_data, get_test_scores, get_demographics


def query_education_data(
    query_type: str,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Query education data from BigQuery for California schools.
    
    Args:
        query_type: Type of data - "schools" for school info, "test_scores" for test data, "demographics" for student demographics
        
    Returns:
        Dictionary with California education data (automatically filtered to San Francisco area, limit 10 results)
    """
    try:
        # Always query California data with San Francisco as default location
        state = "CA"
        district = None
        limit = 10
        
        if query_type == "schools":
            return get_school_data(
                state=state,
                district=district,
                limit=limit,
                tool_context=tool_context
            )
        elif query_type == "test_scores":
            return get_test_scores(
                state=state,
                district=district,
                limit=limit,
                tool_context=tool_context
            )
        elif query_type == "demographics":
            return get_demographics(
                state=state,
                district=district,
                limit=limit,
                tool_context=tool_context
            )
        else:
            return {
                "error": f"Unknown query_type: {query_type}",
                "valid_types": ["schools", "test_scores", "demographics"]
            }
    except Exception as e:
        return {
            "error": str(e),
            "query_type": query_type
        }

