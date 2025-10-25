"""
Student Profile Parser
Extracts student information from documents or text input
"""
from typing import Dict, Any, Optional
from ..utils.document_parser import parse_document_with_gemini, extract_student_info
from ..config import GRADE_TO_LEVEL


def parse_student_documents(
    file_bytes: bytes,
    mime_type: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse student documents (report cards, IEPs, etc.) to extract profile.
    
    Args:
        file_bytes: Document file as bytes
        mime_type: MIME type of the file
        api_key: Google API key
        
    Returns:
        Extracted student profile with status
    """
    return parse_document_with_gemini(file_bytes, mime_type, api_key)


def create_student_profile(
    text_input: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a student profile from either text input or uploaded document.
    
    Args:
        text_input: Text description of student (if no file)
        file_bytes: Document file bytes (if uploading file)
        mime_type: MIME type of uploaded file
        api_key: Google API key
        
    Returns:
        Complete student profile ready for school matching
    """
    try:
        # Parse from BOTH file AND text if both provided
        if file_bytes and mime_type and text_input:
            # Parse document for detailed student info
            doc_profile = parse_document_with_gemini(file_bytes, mime_type, api_key)
            
            # Parse text for explicit parent requests (like "high school")
            text_profile = extract_student_info(text_input, api_key)
            
            # Merge: start with document data, override with text data (priority to parent's explicit request)
            profile = doc_profile.copy()
            
            # CRITICAL: Parent's explicit school type request takes priority
            if text_profile.get("school_type_requested"):
                profile["school_type_requested"] = text_profile["school_type_requested"]
            
            # Also merge other text fields if present
            if text_profile.get("location"):
                profile["location"] = text_profile["location"]
            
        elif file_bytes and mime_type:
            # Only file provided
            profile = parse_document_with_gemini(file_bytes, mime_type, api_key)
        elif text_input:
            # Only text provided
            profile = extract_student_info(text_input, api_key)
        else:
            return {
                "status": "error",
                "message": "Must provide either text_input or file_bytes"
            }
        
        if profile.get("status") == "error":
            return profile
        
        # Enrich profile with additional metadata
        enriched_profile = _enrich_profile(profile)
        
        return enriched_profile
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating student profile: {str(e)}"
        }


def _enrich_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich student profile with computed fields for matching.
    
    Args:
        profile: Raw profile from document parsing
        
    Returns:
        Enriched profile with additional metadata
    """
    enriched = profile.copy()
    
    # PRIORITY 1: Check if parent explicitly requested a specific school type
    school_type_requested = profile.get("school_type_requested", "").strip().lower()
    if "high" in school_type_requested:
        school_level = 3  # High School - parent explicitly asked for high school
    elif "middle" in school_type_requested:
        school_level = 2  # Middle School
    elif "elementary" in school_type_requested or "elem" in school_type_requested:
        school_level = 1  # Elementary
    else:
        # PRIORITY 2: Determine school level from grade
        grade_entering = profile.get("grade_entering", "").strip().lower()
        school_level = GRADE_TO_LEVEL.get(grade_entering, 0)
        
        # If not found, try parsing numeric grade
        if school_level == 0 and grade_entering:
            try:
                grade_num = int(''.join(filter(str.isdigit, grade_entering)))
                if grade_num <= 5:
                    school_level = 1  # Elementary
                elif 6 <= grade_num <= 8:
                    school_level = 2  # Middle
                elif 9 <= grade_num <= 12:
                    school_level = 3  # High
            except ValueError:
                school_level = 0
    
    enriched["school_level"] = school_level
    enriched["school_level_name"] = {
        1: "Elementary",
        2: "Middle School",
        3: "High School",
        4: "Other"
    }.get(school_level, "Unknown")
    
    # Categorize interests
    interests = profile.get("interests", [])
    enriched["interest_categories"] = {
        "stem": any(interest.lower() in ["math", "science", "stem", "technology", "engineering", "computer"]
                   for interest in interests),
        "arts": any(interest.lower() in ["art", "music", "drama", "theater", "dance", "creative"]
                   for interest in interests),
        "sports": any(interest.lower() in ["sports", "athletics", "physical", "pe", "soccer", "basketball"]
                     for interest in interests),
        "language": any(interest.lower() in ["language", "spanish", "french", "esl", "bilingual"]
                       for interest in interests)
    }
    
    # Identify special needs
    learning_needs = profile.get("learning_needs", [])
    special_services = profile.get("special_services", [])
    
    enriched["needs_categories"] = {
        "small_classes": any("small" in str(need).lower() for need in learning_needs),
        "special_ed": any("iep" in str(svc).lower() or "special ed" in str(svc).lower() 
                         for svc in special_services),
        "gifted": any("gifted" in str(need).lower() or "gate" in str(svc).lower() 
                     for need in learning_needs for svc in special_services),
        "english_learner": any("ell" in str(svc).lower() or "english learner" in str(svc).lower()
                              for svc in special_services)
    }
    
    return enriched

