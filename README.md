# 🎓 Education Insights & Resource Recommender

An AI-powered conversational agent system that helps parents, educators, and policymakers make data-driven decisions about education resources and outcomes.

## 🎯 Project Overview

This system uses Google Cloud's Vertex AI and BigQuery to analyze educational data and provide actionable insights through natural language conversations.

### Example Queries
- "Identify the five schools in the county with the highest rate of low-income students and the lowest per-pupil technology spending"
- "Find schools with high graduation rates despite below-average funding"
- "Find schools with strong STEM programs and low class sizes"

## 🏗️ Architecture

**Hierarchical Sub-Agent Structure:**

```
User Query
    ↓
Root Agent (Parent Orchestrator)
    │
    ├── calls → Data Sub-Agent (BigQuery Specialist)
    │                  ↓
    │           [returns data]
    │                  ↓
    └── calls → Insights Sub-Agent (Analysis Expert)
                       ↓
                [returns insights]
                       ↓
        Root Agent Synthesizes Response
                       ↓
                  User Response
```

**Key Points:**
- Root Agent is the main orchestrator (parent)
- Data Agent and Insights Agent are sub-agents (children)
- Sub-agents only respond to Root Agent
- Sub-agents do NOT communicate with each other
- All coordination happens through Root Agent

## 🔧 Tech Stack

- **Google BigQuery**: Educational data warehouse
- **Vertex AI Agent Development Kit (ADK)**: Agent framework
- **Vertex AI Agent Engine**: Deployment platform
- **Python 3.10+**: Primary language
- **Streamlit** (Optional): UI interface

## 📦 Setup Instructions

### 1. Google Cloud Setup

```bash
# Install Google Cloud SDK
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Local Environment Setup

**Option A: UV (Recommended - 10x Faster! ⚡)**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run setup script
./setup_uv.sh

# Or manually:
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**Option B: Traditional pip**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

See `UV_SETUP.md` for detailed UV instructions.

### 3. Load Data into BigQuery

```bash
# Create dataset
bq mk --dataset --location=US education_insights

# Load data (example)
bq load --source_format=CSV \
  education_insights.schools \
  ./data/schools.csv \
  auto
```

### 4. Run Agents Locally

```bash
# Test individual agents
python agents/root_agent.py
python agents/data_agent.py
python agents/insights_agent.py

# Run full system
python main.py
```

### 5. Deploy to Vertex AI (Production)

```bash
# Deploy agents
./deployment/deploy.sh
```

## 📊 Data Sources

- **Data.gov**: https://catalog.data.gov/dataset?groups=education2168
- **Education Data Portal**: https://educationdata.urban.org/
- **NCES**: https://nces.ed.gov/

## 🤖 Agent Roles

### Root Agent (Parent)
- **Main orchestrator** of the entire system
- Greets users and interprets education-related queries
- Calls sub-agents as tools/functions
- Synthesizes responses from sub-agents
- Only agent that interacts with users

### Data Sub-Agent (Child)
- **Specialized tool** called by Root Agent
- Queries BigQuery datasets
- Filters and aggregates data
- Returns structured results to Root Agent only

### Insights Sub-Agent (Child)
- **Specialized tool** called by Root Agent
- Analyzes patterns and trends
- Provides comparisons and recommendations
- Returns insights to Root Agent only

## 🚀 Usage

### Python API
```python
from agents.root_agent import RootAgent

agent = RootAgent()
response = agent.query(
    "Find schools with high graduation rates despite below-average funding"
)
print(response)
```

### Streamlit UI (if implemented)
```bash
streamlit run app.py
```

## 📁 Project Structure

```
A4I-C1/
├── agents/
│   ├── root_agent.py         # Orchestrator agent
│   ├── data_agent.py          # BigQuery query agent
│   ├── insights_agent.py      # Analysis agent
│   └── config.py              # Configuration
├── tools/
│   ├── bigquery_tools.py      # BigQuery utilities
│   └── analysis_tools.py      # Analysis functions
├── data/
│   └── *.csv                  # Raw data files
├── tests/
│   └── test_agents.py         # Unit tests
├── deployment/
│   └── deploy.yaml            # Deployment config
├── notebooks/
│   └── data_exploration.ipynb # Data analysis
├── requirements.txt
├── README.md
└── PROJECT_PLAN.md            # Detailed implementation guide
```

## 🎬 Demo Scenarios

1. **Resource Prioritization**: Identify schools needing technology grants
2. **Best Practice Discovery**: Find high-performing schools with limited budgets
3. **Program Comparison**: Compare STEM programs across districts

## 🔮 Stretch Goals

- [ ] Interactive visualizations (charts, maps)
- [ ] Multimodal inputs (images, video)
- [ ] Predictive analytics
- [ ] Mobile-friendly interface

## 📝 Documentation

See `PROJECT_PLAN.md` for detailed implementation steps.

## 👥 Team

[Your team information here]

## 📄 License

[Your license here]

## 🙏 Acknowledgments

- Google Cloud for Vertex AI platform
- Open education data providers
- [Your team and advisors]

