#!/usr/bin/env python3
"""
Education Insights & Resource Recommender
Main entry point for ADK-based hierarchical agent system

Run:
    python main.py --demo    # Demo with sample queries
    python main.py           # Interactive mode
"""

import os
import sys
from typing import Dict, Any

# Check if running in Cloud Shell (ADK available)
try:
    from google.adk.agents import LlmAgent
    from google.adk.sessions import State
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("⚠️  WARNING: google.adk not found")
    print("   Install with: pip install google-adk")
    sys.exit(1)

from agents.root_agent import create_root_agent
from agents.config import get_config


def create_runner_state() -> State:
    """Create initial state for the agent runner"""
    config = get_config()
    
    # State requires (value, delta) as positional arguments
    initial_state = {
        'project_id': config.project_id,
        'location': config.location,
        'bigquery_dataset': config.bigquery_dataset,
        'model_name': config.model_name,
        'temperature': config.temperature,
        'max_output_tokens': config.max_output_tokens,
        
        # Conversation state
        'user_type': None,  # Will be detected: 'parent', 'educator', 'official'
        'conversation_history': [],
        
        # Session metadata
        'session_id': None,
        'total_queries': 0,
    }
    
    return State(value=initial_state, delta={})


def print_welcome():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print("🎓 EDUCATION INSIGHTS & RESOURCE RECOMMENDER")
    print("=" * 70)
    print("\n✨ Powered by Google ADK & Vertex AI")
    print(f"📊 Connected to BigQuery: {get_config().project_id}")
    print("\n💡 This system adapts to THREE user types:")
    print("   👪 PARENTS - School choice, advocacy, student support")
    print("   👨‍🏫 EDUCATORS - Interventions, resources, pedagogy")
    print("   🏛️  OFFICIALS - Policy, funding, systemic solutions")
    print("\n" + "=" * 70 + "\n")


def run_demo_mode():
    """Run demo testing the 3 core research questions"""
    print_welcome()
    print("🎬 DEMO MODE - Testing research questions...\n")
    
    # Import the specialized tools directly
    from tools.bigquery_tools import (
        find_high_need_low_tech_spending,
        find_high_graduation_low_funding,
        find_strong_stem_low_class_size
    )
    
    config = get_config()
    
    # Create mock ToolContext for testing
    class MockState:
        def __init__(self, project_id, dataset):
            self.project_id = project_id
            self.dataset = dataset
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    class MockContext:
        def __init__(self, project_id, dataset):
            self.state = MockState(project_id, dataset)
    
    mock_ctx = MockContext(config.project_id, config.bigquery_dataset)
    
    # Demo queries matching the 3 research questions
    demo_queries = [
        {
            "title": "Q1: Grant Priority Schools",
            "emoji": "💰",
            "description": "Schools with highest low-income % + lowest tech spending",
            "function": lambda: find_high_need_low_tech_spending(
                limit=5,
                tool_context=mock_ctx
            )
        },
        {
            "title": "Q2: High-Performing High-Need Schools",
            "emoji": "⭐",
            "description": "High graduation rates despite below-average funding",
            "function": lambda: find_high_graduation_low_funding(
                limit=10,
                tool_context=mock_ctx
            )
        },
        {
            "title": "Q3: STEM Excellence + Small Classes",
            "emoji": "🔬",
            "description": "Strong STEM programs with low class sizes",
            "function": lambda: find_strong_stem_low_class_size(
                limit=10,
                tool_context=mock_ctx
            )
        }
    ]
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"{demo['emoji']} {demo['title']} ({i}/{len(demo_queries)})")
        print(f"{'─' * 70}")
        print(f"📝 {demo['description']}\n")
        
        try:
            # Run the query
            result = demo['function']()
            
            # Print response
            if result['status'] == 'success':
                print(f"✅ Found {result.get('count', 0)} schools\n")
                print(f"📊 Results:")
                print(result['summary'])
                print()
            else:
                print(f"⚠️  {result.get('message', 'No data found')}\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("✅ Demo complete! Multi-agent system is configured.")
    print("   • Data layer: BigQuery + 3 research questions ✅")
    print("   • Agent architecture: Root → Data → Insights ✅")
    print("   • Deploy to Cloud Run to enable full agent orchestration")
    print("=" * 70 + "\n")


def run_interactive_mode():
    """Run interactive conversation with the user"""
    print_welcome()
    print("💬 INTERACTIVE MODE")
    print("Type your questions below. Type 'quit' or 'exit' to stop.\n")
    
    # Create agent
    config = get_config()
    root_agent = create_root_agent(
        project_id=config.project_id,
        dataset=config.bigquery_dataset
    )
    state = create_runner_state()
    
    print("💡 Tip: Tell us your role for better recommendations!")
    print("   Example: 'I'm a parent' or 'I'm a teacher' or 'I'm on the school board'\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Thank you for using Education Insights!")
                print("   Empowering data-driven decisions in education.\n")
                break
            
            # Run the agent directly
            print("\n🤔 Thinking...\n")
            response = root_agent.run(user_input, state=state)
            
            # Print response
            print(f"Agent: {response.content}\n")
            
            # Update state
            state = response.state
            current_queries = state.value.get('total_queries', 0) if hasattr(state, 'value') else state.get('total_queries', 0)
            state.update({'total_queries': current_queries + 1})
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            print("\nPlease try again or type 'quit' to exit.\n")


def main():
    """Main entry point"""
    # Check for ADK
    if not ADK_AVAILABLE:
        return
    
    # Parse command line args
    demo_mode = '--demo' in sys.argv or '-d' in sys.argv
    
    try:
        if demo_mode:
            run_demo_mode()
        else:
            run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

