"""
Data Agent - ADK Implementation
Handles all BigQuery data retrieval using ADK LlmAgent
"""
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from tools.bigquery_tools import (
    query_bigquery,
    get_school_data,
    get_graduation_data,
    get_district_finance,
    find_high_need_low_tech_spending,
    find_high_graduation_low_funding,
    find_strong_stem_low_class_size,
    search_schools_with_stem
)


def create_data_agent(project_id: str, dataset: str = "education_data") -> LlmAgent:
    """
    Create the Data Agent using ADK LlmAgent.
    
    The Data Agent is responsible for retrieving education data from BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        
    Returns:
        ADK LlmAgent configured as Data Agent
    """
    
    # Define the agent's instruction
    instruction = f"""You are the Data Sub-Agent for the California Education Insights system.

Your PRIMARY responsibility is to retrieve education data from BigQuery (California schools, 2018 data).

AVAILABLE BIGQUERY TABLES:
- ccd_directory (10,000 CA schools): demographics, enrollment, teachers, location
- graduation_rates (788 high schools): graduation rates by school
- district_finance (2,198 districts): per-pupil spending, total expenditures
- stem_* tables (12 tables): AP, Calculus, Physics, Chemistry, Biology, etc.

AVAILABLE TOOLS:
1. query_bigquery - Execute custom SQL queries
2. get_school_data - Get school info with calculated metrics (low_income_pct, student_teacher_ratio)
3. get_graduation_data - Get graduation rates for high schools
4. get_district_finance - Get per-pupil spending and district finances

SPECIALIZED RESEARCH QUESTION TOOLS:
5. find_high_need_low_tech_spending - Q1: Schools with high low-income % + low spending (grant priority)
6. find_high_graduation_low_funding - Q2: High graduation despite high poverty (replicable models)
7. find_strong_stem_low_class_size - Q3: Strong STEM programs + low class sizes
8. search_schools_with_stem - Search schools by specific STEM course (AP, calculus, physics, etc.)

KEY COLUMN MAPPINGS:
- School ID: ncessch
- District ID: leaid  
- Low-income indicator: free_lunch / enrollment * 100
- Class size: enrollment / teachers_fte
- STEM join: CONCAT(leaid, school_id) = COMBOKEY

GUIDELINES:
- Use specialized tools (#5-7) for the 3 research questions - they have optimized JOINs
- Tools automatically calculate metrics (low_income_pct, student_teacher_ratio)
- All graduation queries filter to overall rates (race=99, disability=99, etc.)
- STEM data joins via COMBOKEY = CONCAT(leaid, school_id)
- Include row counts and explain what the data shows
- If no results, suggest adjusting filters

CURRENT CONFIGURATION:
- Project: {project_id}
- Dataset: {dataset}
- State: California
- Year: 2018

EXAMPLE QUERIES:
"Find 5 schools needing grants" → find_high_need_low_tech_spending(limit=5)
"High-performing high-need schools" → find_high_graduation_low_funding()
"STEM schools with small classes" → find_strong_stem_low_class_size()
"Schools with calculus programs" → search_schools_with_stem(stem_course="calculus")
"All schools in county 6037" → get_school_data(county="6037")

Always provide clear summaries with key metrics highlighted."""

    # Create function tools
    tools = [
        FunctionTool(func=query_bigquery),
        FunctionTool(func=get_school_data),
        FunctionTool(func=get_graduation_data),
        FunctionTool(func=get_district_finance),
        # Specialized research question tools
        FunctionTool(func=find_high_need_low_tech_spending),
        FunctionTool(func=find_high_graduation_low_funding),
        FunctionTool(func=find_strong_stem_low_class_size),
        FunctionTool(func=search_schools_with_stem)
    ]
    
    # Create the agent
    agent = LlmAgent(
        name="DataAgent",
        model="gemini-2.0-flash-exp",
        instruction=instruction,
        tools=tools
    )
    
    return agent

