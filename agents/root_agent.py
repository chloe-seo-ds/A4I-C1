"""
Root Agent - ADK Implementation
Top-level orchestrator using sub-agents
"""
import os
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
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
        ADK LlmAgent configured as Root Agent with sub-agents as tools
    """
    
    # Create sub-agents
    data_agent = create_data_agent(project_id=project_id, dataset=dataset)
    insights_agent = create_insights_agent()
    
    # Convert specialized agents into AgentTools (per ADK pattern)
    data_tool = AgentTool(agent=data_agent)
    insights_tool = AgentTool(agent=insights_agent)
    
    # Use persona-aware prompt from config and add sub-agent descriptions
    instruction = ROOT_AGENT_PROMPT + f"""

**YOUR SUB-AGENTS (Available as Tools):**

1. **DataAgent** - BigQuery Data Specialist
   - Retrieves education data from BigQuery (California 2018)
   - 10K schools, 788 with graduation rates, 2,198 districts
   - Has 8 specialized tools: query_bigquery, get_school_data, get_graduation_data, 
     get_district_finance, and research question tools
   - Can find high-need/low-spending schools, high graduation/low funding, STEM programs
   
   Use for:
   • "Find 5 schools with highest low-income % and lowest tech spending"
   • "Get schools with high graduation rates despite low funding"
   • "Show schools with strong STEM programs and small class sizes"

2. **InsightsAgent** - Recommendation & Analysis Expert
   - Analyzes data and generates actionable recommendations
   - Adapts to user type (parent/educator/official)
   - Ensures recommendations are data-backed, feasible, and equitable
   
   Use for:
   • Generating recommendations based on school data
   • Providing strategic guidance for educators/officials
   • Suggesting interventions and next steps for parents

**ORCHESTRATION WORKFLOW:**

1. **Understand the Request**
   - Identify user type (parent/educator/official)
   - Determine what data is needed

2. **Gather Data** → Call DataAgent
   - Pass specific data request (e.g., "Find high-need schools")
   - Review the returned data

3. **Generate Insights** → Call InsightsAgent
   - Pass the data context and user needs
   - Get refined, actionable recommendations

4. **Present Results**
   - Synthesize insights for the user's role
   - Format appropriately (parent/educator/official)

**Current Configuration:**
- Project: {project_id}
- Dataset: {dataset}

**IMPORTANT:**
- Use DataAgent FIRST to retrieve data
- Use InsightsAgent to analyze data and generate recommendations
- Both agents can handle multi-step workflows - delegate complex tasks to them!
"""
    
    # Use different model names for API vs Vertex AI
    model_name = "gemini-2.0-flash-exp" if os.getenv("GOOGLE_API_KEY") else "gemini-2.0-flash-exp"
    
    # Create root agent with sub-agents as AgentTools
    agent = LlmAgent(
        model=model_name,
        name="RootAgent",
        instruction=instruction,
        tools=[data_tool, insights_tool]  # Sub-agents as AgentTools per ADK pattern!
    )
    
    return agent
