"""
Document Parser using Gemini Vision API
Extracts student profile from uploaded documents (report cards, IEPs, etc.)
"""
import os
from typing import Dict, Any, Optional
import json
import re


def parse_document_with_gemini(
    file_bytes: bytes,
    mime_type: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse uploaded document using Gemini Vision API.
    
    Extracts student information from:
    - Report cards
    - IEP documents
    - Test scores
    - Parent notes
    
    Args:
        file_bytes: Document file as bytes
        mime_type: MIME type of the file
        api_key: Google API key (or use environment variable)
        
    Returns:
        Dictionary with extracted student profile
    """
    try:
        import google.genai as genai
        from google.genai import types
        
        # Use provided API key or environment variable
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return {
                "status": "error",
                "message": "GOOGLE_API_KEY not found in environment"
            }
        
        # Initialize client
        client = genai.Client(api_key=api_key, vertexai=False)
        
        # Create prompt for student profile extraction
        prompt = """You are an education assistant helping parents find the right K-12 school for their child.

Analyze this document and extract the following information about the student:

1. **Grade Level**: What grade is the student currently in or entering? (K-12)
2. **Academic Strengths**: What subjects or areas does the student excel in?
3. **Academic Challenges**: What subjects need improvement or support?
4. **Interests**: What are the student's interests, hobbies, or passions? (STEM, Arts, Sports, etc.)
5. **Learning Needs**: Does the student need small classes, special education services, gifted programs, etc.?
6. **Test Scores**: Any standardized test scores mentioned? (e.g., proficiency levels, percentiles)
7. **Special Services**: IEP, 504 plan, English learner, gifted & talented?
8. **Location**: Any mention of city, zip code, or address?

Return your response in this EXACT JSON format (no markdown, no code blocks):
{
  "grade_level": "current grade (e.g., 6, K, 10)",
  "grade_entering": "grade student will enter (e.g., 7 if currently in 6th)",
  "academic_strengths": ["list", "of", "strengths"],
  "academic_challenges": ["list", "of", "challenges"],
  "interests": ["list", "of", "interests"],
  "learning_needs": ["small classes", "special ed", "gifted program", etc.],
  "test_scores": {"subject": "proficiency level"},
  "special_services": ["IEP", "504", "ELL", "GATE", etc.],
  "location": {"city": "city name", "state": "CA", "zip": "95112"},
  "summary": "Brief 1-2 sentence summary of the student"
}

If information is not available, use empty strings or empty arrays. Be specific and extract all details mentioned."""

        # Create content parts
        text_part = types.Part(text=prompt)
        file_part = types.Part(inline_data=types.Blob(mime_type=mime_type, data=file_bytes))
        
        # Generate response
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[text_part, file_part]
        )
        
        response_text = response.text.strip()
        
        # Try to extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group(0)
        
        # Parse JSON response
        try:
            student_data = json.loads(response_text)
            student_data["status"] = "success"
            return student_data
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return raw text
            return {
                "status": "partial_success",
                "message": "Could not parse structured data, returning raw text",
                "raw_response": response_text,
                "grade_level": "",
                "grade_entering": "",
                "academic_strengths": [],
                "academic_challenges": [],
                "interests": [],
                "learning_needs": [],
                "test_scores": {},
                "special_services": [],
                "location": {},
                "summary": response_text[:500]  # First 500 chars
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error parsing document: {str(e)}"
        }


def extract_student_info(text_input: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract student information from plain text input.
    
    Use this when parent types their needs directly instead of uploading a document.
    
    Args:
        text_input: Parent's text description of their child
        api_key: Google API key
        
    Returns:
        Dictionary with extracted student profile
    """
    try:
        import google.genai as genai
        
        # Use provided API key or environment variable
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return {
                "status": "error",
                "message": "GOOGLE_API_KEY not found in environment"
            }
        
        # Initialize client
        client = genai.Client(api_key=api_key, vertexai=False)
        
        # Create prompt
        prompt = f"""You are an education assistant helping parents find the right K-12 school for their child.

The parent provided this information about their child:
"{text_input}"

Extract and structure this information into the following JSON format (no markdown, no code blocks):
{{
  "grade_level": "current grade (e.g., 6, K, 10)",
  "grade_entering": "grade student will enter next OR grade for which they're seeking school recommendations",
  "school_type_requested": "elementary, middle, or high - IMPORTANT: detect if parent explicitly asks for a specific school type (e.g., 'which high school', 'looking for elementary school', etc.)",
  "academic_strengths": ["list", "of", "strengths"],
  "academic_challenges": ["list", "of", "challenges"],
  "interests": ["list", "of", "interests"],
  "learning_needs": ["small classes", "special ed", "gifted program", etc.],
  "test_scores": {{}},
  "special_services": ["IEP", "504", "ELL", "GATE", etc.],
  "location": {{"city": "city name", "state": "CA", "zip": "95112"}},
  "summary": "Brief 1-2 sentence summary"
}}

CRITICAL: If the parent mentions "high school", "highschool", or asks what high school their child can attend, set school_type_requested to "high".
If they mention "elementary" or "middle school", set accordingly.
If information is not mentioned, use empty strings or empty arrays."""

        # Generate response
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group(0)
        
        # Parse JSON
        try:
            student_data = json.loads(response_text)
            student_data["status"] = "success"
            return student_data
        except json.JSONDecodeError:
            return {
                "status": "partial_success",
                "message": "Could not parse structured data",
                "raw_response": response_text,
                "grade_level": "",
                "grade_entering": "",
                "academic_strengths": [],
                "academic_challenges": [],
                "interests": [],
                "learning_needs": [],
                "test_scores": {},
                "special_services": [],
                "location": {},
                "summary": response_text[:500]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error extracting student info: {str(e)}"
        }

