"""
School Information Enrichment Agent
Uses AI to automatically fetch/generate detailed school information
"""
import os
from typing import Dict, Any, List
import json


def enrich_school_information(
    school_name: str,
    school_level: int,
    city: str,
    charter: int = 0,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Use Gemini AI agent to enrich school information with:
    - Tour schedules and open house dates
    - Application deadlines
    - Enrollment requirements
    - Special programs and services
    
    Args:
        school_name: Name of the school
        school_level: 1=Elementary, 2=Middle, 3=High
        city: City location
        charter: 0=Public, 1=Charter
        api_key: Google API key
        
    Returns:
        Dictionary with enriched school information
    """
    try:
        import google.genai as genai
        
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            # Return default information if no API key
            return _generate_default_information(school_name, school_level, charter)
        
        client = genai.Client(api_key=api_key, vertexai=False)
        
        # Determine school type
        school_type = "Charter School" if charter == 1 else "Public School"
        level_name = {1: "Elementary", 2: "Middle School", 3: "High School"}.get(school_level, "School")
        
        # Create prompt for AI agent
        prompt = f"""You are a school information assistant. Generate realistic and helpful information for this California school:

**School:** {school_name}
**Type:** {school_type} {level_name}
**Location:** {city}, California
**Current Date:** October 25, 2025

Generate the following information in JSON format (respond ONLY with valid JSON, no markdown):

{{
  "tours": [
    {{"type": "Open House", "date": "specific date between November 2025 and January 2026", "time": "evening time like 6:00 PM", "registration": "how to register"}},
    {{"type": "Campus Tour", "schedule": "recurring schedule in 2025-2026", "registration": "how to register"}}
  ],
  "deadlines": [
    {{"type": "Application/Lottery Deadline", "date": "realistic future date in 2026 (typically January-February for CA schools)", "notes": "specific details"}},
    {{"type": "Document Submission", "date": "date in 2026 after application", "notes": "what documents"}},
    {{"type": "Enrollment Decision", "date": "decision date in 2026", "notes": "when families are notified"}}
  ],
  "requirements": [
    "Proof of residence (utility bill, lease agreement)",
    "Child's birth certificate",
    "Immunization records",
    "Previous school records/transcripts (if applicable)"
  ],
  "programs": [
    {{"name": "program name", "description": "brief description"}},
    {{"name": "another program", "description": "description"}}
  ],
  "contact": {{
    "phone": "Generate a UNIQUE realistic California phone number (408 area code for {city}). Make it DIFFERENT for each school by varying the last digits.",
    "email": "Generate a unique email based on the school name (e.g., {school_name.lower().replace(' ', '')}@schooldistrict.org)",
    "website": "Generate a UNIQUE website URL based on the actual school name (e.g., https://www.{school_name.lower().replace(' ', '')}.org or similar). Make it SPECIFIC to {school_name}.",
    "office_hours": "typical office hours"
  }}
}}

CRITICAL: The contact information MUST be UNIQUE and SPECIFIC to {school_name}. 
- Phone: Use 408 area code but vary the last 7 digits for each school
- Website: Create a realistic domain based on the actual school name "{school_name}"
- Email: Base it on the school name

Make the information realistic for a California {school_type} {level_name}. For charter schools, include lottery information. For public schools, mention attendance zones."""

        # Call Gemini
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group(0)
        
        # Parse JSON
        enriched_data = json.loads(response_text)
        enriched_data["status"] = "success"
        enriched_data["source"] = "ai_generated"
        
        return enriched_data
        
    except Exception as e:
        print(f"Error enriching school information: {e}")
        # Return default information on error
        return _generate_default_information(school_name, school_level, charter)


def _generate_default_information(school_name: str, school_level: int, charter: int) -> Dict[str, Any]:
    """
    Generate default school information when AI is unavailable.
    """
    school_type = "Charter" if charter == 1 else "Public"
    level_name = {1: "Elementary", 2: "Middle", 3: "High"}.get(school_level, "")
    
    return {
        "status": "success",
        "source": "default",
        "tours": [
            {
                "type": "Open House",
                "date": "Check school website for upcoming dates",
                "time": "Typically 6:00-8:00 PM",
                "registration": "Visit school website or call office"
            },
            {
                "type": "Campus Tour",
                "schedule": "Usually available by appointment",
                "registration": "Call school office to schedule"
            }
        ],
        "deadlines": [
            {
                "type": "Lottery Application" if charter else "Enrollment Period",
                "date": "Typically January-February for following school year",
                "notes": "Contact school for specific dates"
            },
            {
                "type": "Document Submission",
                "date": "Required documents due before enrollment",
                "notes": "Varies by school"
            }
        ],
        "requirements": [
            "Proof of residence",
            "Birth certificate",
            "Immunization records",
            "Previous school transcripts (if applicable)"
        ],
        "programs": [
            {
                "name": "Core Academic Program",
                "description": f"Standard {level_name} curriculum"
            },
            {
                "name": "Special Education Services",
                "description": "Support for students with IEPs"
            }
        ],
        "contact": {
            "phone": "Contact school district",
            "email": "Visit school website",
            "website": "Search online for official school website",
            "office_hours": "Typically Monday-Friday, 8:00 AM - 4:00 PM"
        }
    }


def enrich_multiple_schools(
    schools: List[Dict[str, Any]],
    api_key: str = None,
    max_schools: int = 10
) -> List[Dict[str, Any]]:
    """
    Enrich multiple schools with detailed information using parallel API calls.
    
    Args:
        schools: List of school dictionaries
        api_key: Google API key
        max_schools: Maximum number to enrich (default 10, set to 5 for faster loading)
        
    Returns:
        List of schools with enriched information
    """
    import concurrent.futures
    import threading
    
    enriched_schools = []
    schools_to_enrich = schools[:max_schools]
    
    print(f"   🚀 Enriching {len(schools_to_enrich)} schools in parallel...")
    
    def enrich_one_school(school, index):
        """Helper function to enrich a single school"""
        try:
            print(f"   [{index+1}/{len(schools_to_enrich)}] Enriching {school.get('school_name', 'Unknown')}")
            
            enrichment = enrich_school_information(
                school_name=school.get('school_name', 'Unknown'),
                school_level=school.get('school_level', 2),
                city=school.get('city_location', 'California'),
                charter=school.get('charter', 0),
                api_key=api_key
            )
            
            # Add enrichment data to school
            school['enrichment'] = enrichment
            return school
        except Exception as e:
            print(f"   ⚠️ Error enriching {school.get('school_name')}: {e}")
            school['enrichment'] = {'status': 'error', 'message': str(e)}
            return school
    
    # Use ThreadPoolExecutor to make parallel API calls (max 5 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all enrichment tasks
        future_to_school = {
            executor.submit(enrich_one_school, school, i): school 
            for i, school in enumerate(schools_to_enrich)
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_school):
            try:
                enriched_school = future.result()
                enriched_schools.append(enriched_school)
            except Exception as e:
                print(f"   ⚠️ Future exception: {e}")
                school = future_to_school[future]
                school['enrichment'] = {'status': 'error'}
                enriched_schools.append(school)
    
    # Sort back to original order
    enriched_schools.sort(key=lambda s: schools.index(s) if s in schools else 999)
    
    print(f"   ✅ Enriched {len(enriched_schools)} schools")
    return enriched_schools

