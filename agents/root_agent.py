"""
Root Agent - ADK Implementation
Top-level orchestrator using sub-agents
"""
import os
from google.adk.agents import LlmAgent
from agents.data_agent import create_data_agent
from agents.insights_agent import create_insights_agent
from agents.config import ROOT_AGENT_PROMPT


def create_root_agent(project_id: str, dataset: str = "education_data") -> LlmAgent:
    """
    Create the Root Agent using ADK LlmAgent.
    
    The Root Agent orchestrates two specialized sub-agents:
    - DataAgent: Handles all BigQuery data retrieval
    - InsightsAgent: Generates refined recommendations through iterative refinement
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        
    Returns:
        ADK LlmAgent configured as Root Agent with sub-agents
    """
    
    # Create sub-agents
    data_agent = create_data_agent(project_id=project_id, dataset=dataset)
    insights_agent = create_insights_agent()
    
    # Use persona-aware prompt from config and add sub-agent descriptions
    instruction = ROOT_AGENT_PROMPT + f"""

**YOUR SUB-AGENTS:**

1. **DataAgent** - BigQuery Data Specialist
   - Retrieves education data from BigQuery
   - Has 8 specialized tools for different query types
   - Can query schools, test scores, demographics, and run custom SQL
   - Intelligently selects the right tool for each data request
   - Handles missing data gracefully with helpful guidance

2. **InsightsAgent** - Recommendation Orchestrator
   - Generates high-quality, actionable recommendations
   - Orchestrates an iterative refinement loop:
     * RecommenderAgent creates initial recommendations
     * CritiqueAgent evaluates and identifies weaknesses
     * RecommenderAgent refines based on feedback
   - Ensures recommendations are data-backed, feasible, and equitable

**ORCHESTRATION WORKFLOW:**

1. **Understand the Request**
   - Identify user type (parent/educator/official)
   - Determine what data is needed
   - Clarify the question or problem

2. **Gather Data**
   - Call DataAgent with specific data requests
   - DataAgent will use its 8 tools to retrieve relevant information
   - If data is missing, DataAgent provides guidance

3. **Generate Insights**
   - Call InsightsAgent with the data and user context
   - InsightsAgent runs its refinement loop automatically
   - Receives refined, high-quality recommendations

4. **Present Results**
   - Format recommendations for the user's role
   - Use appropriate language and framing
   - Provide actionable next steps

**COMMUNICATION EXAMPLES:**

To DataAgent:
"Find schools in California with high low-income populations and low tech spending"
"Get test score data for San Francisco Unified School District"
"Show me schools with strong STEM and small class sizes"

To InsightsAgent:
"Based on this data: [DATA], generate recommendations for a parent whose child is struggling with reading"
"Analyze this school performance data and provide recommendations for a superintendent allocating $5M"

**Current Configuration:**
- Project: {project_id}
- Dataset: {dataset}

**IMPORTANT:**
- Always call DataAgent FIRST to get data
- Then call InsightsAgent with the data to get recommendations
- DataAgent and InsightsAgent work together - use both!
"""
    
    # Use different model names for API vs Vertex AI
    model_name = "gemini-2.0-flash-exp" if os.getenv("GOOGLE_API_KEY") else "gemini-2.0-flash-exp"
    
    # Create root agent with sub-agents as tools
    agent = LlmAgent(
        model=model_name,
        name="RootAgent",
        instruction=instruction,
        tools=[data_agent, insights_agent]  # Sub-agents are used as tools!
    )
    
    return agent
