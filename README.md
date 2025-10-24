# 🎓 EdEquity: Education Insights & Resource Recommender

An AI-powered conversational agent system that helps parents, educators, and policymakers make data-driven decisions about education resources and outcomes.

## ✨ Features

- 📊 **Interactive Data Visualizations**: Dynamic charts showing key metrics (Chart.js)
- 🗺️ **Google Maps Integration**: View school locations with detailed info windows
- 📝 **Executive Summaries**: Direct answers with school names and key metrics upfront
- 📋 **Detailed Data Tables**: Sortable, comprehensive school data
- 🎨 **Modern UI**: Beautiful, responsive interface with role-based interactions
- 📎 **Multimodal Inputs**: Upload images (school photos, documents) and PDFs (reports, policies) for AI analysis
- 🎯 **Drag & Drop**: Easy file uploads with preview and validation

## 🎯 Project Overview

This system uses Google Cloud's Vertex AI and BigQuery to analyze educational data and provide actionable insights through natural language conversations.

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

### 3. Configure Google Maps API (Optional)

For map visualizations, add your Google Maps API key:

```bash
# Create secrets directory if it doesn't exist
mkdir -p secrets

# Add your API key
echo "YOUR_GOOGLE_MAPS_API_KEY" > secrets/maps_api_key.txt
```

**Note**: Maps will be disabled if no API key is provided. The system will still work without maps.

### 4. Load Data into BigQuery

```bash
# Create dataset
bq mk --dataset --location=US education_insights

# Load data (example)
bq load --source_format=CSV \
  education_insights.schools \
  ./data/schools.csv \
  auto
```

### 5. Run Agents Locally

```bash
# Test individual agents
python agents/root_agent.py
python agents/data_agent.py
python agents/insights_agent.py

# Run full system
python main.py
```

### 6. Deploy to Vertex AI (Production)

```bash
# Deploy agents
./deployment/deploy.sh
```

## 📊 Data Sources

**BigQuery Dataset:** `education_data` (California 2018)
- **CCD Directory** (10,000 schools): Demographics, enrollment, teachers
- **Graduation Rates** (788 high schools): EdFacts graduation data
- **District Finance** (2,198 districts): Per-pupil spending, expenditures
- **STEM Courses** (12 tables): AP, Calculus, Physics, Chemistry, Biology, etc.

**Join Keys:**
- Schools → Districts: `leaid`
- Schools → Graduation: `ncessch`
- Schools → STEM: `CONCAT(leaid, school_id) = COMBOKEY`

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

### Web UI
```bash
# Start the FastAPI server
python api.py

# Open in browser
# http://localhost:8080
```

The web interface provides:
- **Executive Summary**: Direct answers with top 5 schools listed
- **Interactive Charts**: Bar charts showing key metrics (low-income %, spending, graduation rates, etc.)
- **Google Maps**: Interactive map with school locations and info windows
- **Detailed Data Table**: Full dataset with sortable columns

### Python API
```python
from agents.root_agent import RootAgent

agent = RootAgent()
response = agent.query(
    "Find schools with high graduation rates despite below-average funding"
)
print(response)
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
│   ├── response_formatter.py  # Rich response formatter (charts, maps, tables)
│   └── analysis_tools.py      # Analysis functions
├── static/
│   └── index.html             # Web UI
├── secrets/
│   └── maps_api_key.txt       # Google Maps API key (gitignored)
├── data/
│   └── *.parquet              # Education data files
├── api.py                     # FastAPI backend
├── main.py                    # CLI entry point
├── requirements.txt
└── README.md
```

## 🎬 Demo Scenarios

1. **Resource Prioritization**: Identify schools needing technology grants
2. **Best Practice Discovery**: Find high-performing schools with limited budgets
3. **Program Comparison**: Compare STEM programs across districts

## 🔮 Stretch Goals

- [x] Interactive visualizations (charts, maps)
- [x] Multimodal inputs (images, PDFs)
- [ ] Predictive analytics

## 📎 Multimodal Usage

The chat interface supports uploading images and PDFs:

**Upload Methods:**
1. Click the 📎 attach button
2. Drag and drop files onto the input area

**Supported Files:**
- **Images**: JPG, PNG, GIF, WebP (max 10MB)
- **PDFs**: Reports, policies, test scores (max 20MB)

**Example Use Cases:**
- Upload a school report card and ask "What are the key findings?"
- Share a facility photo and ask "How does this compare to other schools?"
- Upload district data charts and request analysis

## 🙏 Acknowledgments

- Google Cloud for Vertex AI platform
- Open education data providers

