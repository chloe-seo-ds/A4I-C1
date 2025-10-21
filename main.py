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
    from google.adk import Runner
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
    
    return State(
        project_id=config.project_id,
        location=config.location,
        bigquery_dataset=config.bigquery_dataset,
        model_name=config.model_name,
        temperature=config.temperature,
        max_output_tokens=config.max_output_tokens,
        
        # Conversation state
        user_type=None,  # Will be detected: 'parent', 'educator', 'official'
        conversation_history=[],
        
        # Session metadata
        session_id=None,
        total_queries=0,
    )


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
    """Run with sample queries to demonstrate capabilities"""
    print_welcome()
    print("🎬 DEMO MODE - Running sample queries...\n")
    
    demo_queries = [
        {
            "user_type": "parent",
            "query": "My child is struggling with reading. What should I do?",
            "intro": "👪 PARENT QUERY"
        },
        {
            "user_type": "educator",
            "query": "Our 3rd graders are below grade level in math. What interventions work?",
            "intro": "👨‍🏫 EDUCATOR QUERY"
        },
        {
            "user_type": "official",
            "query": "How should we allocate $5M to reduce achievement gaps?",
            "intro": "🏛️  OFFICIAL QUERY"
        }
    ]
    
    # Create runner
    config = get_config()
    root_agent = create_root_agent(
        project_id=config.project_id,
        dataset=config.bigquery_dataset
    )
    runner = Runner(root_agent)
    state = create_runner_state()
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"{demo['intro']} ({i}/{len(demo_queries)})")
        print(f"{'─' * 70}")
        print(f"📝 Query: {demo['query']}\n")
        
        # Set user type in state
        state = state.update(user_type=demo['user_type'])
        
        try:
            # Run the agent
            response = runner.run(demo['query'], state=state)
            
            # Print response
            print(f"🤖 Response:")
            print(f"{response.content}\n")
            
            # Update state
            state = response.state
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("✅ Demo complete!")
    print("=" * 70 + "\n")


def run_interactive_mode():
    """Run interactive conversation with the user"""
    print_welcome()
    print("💬 INTERACTIVE MODE")
    print("Type your questions below. Type 'quit' or 'exit' to stop.\n")
    
    # Create runner
    config = get_config()
    root_agent = create_root_agent(
        project_id=config.project_id,
        dataset=config.bigquery_dataset
    )
    runner = Runner(root_agent)
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
            
            # Run the agent
            print("\n🤔 Thinking...\n")
            response = runner.run(user_input, state=state)
            
            # Print response
            print(f"Agent: {response.content}\n")
            
            # Update state
            state = response.state
            state = state.update(total_queries=state.get('total_queries', 0) + 1)
            
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

