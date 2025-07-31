#!/usr/bin/env python3
"""
Example script showing how to use the Jira Agent.
This demonstrates the main features and usage patterns.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from jira.agent import JiraAgent

def main():
    """Demonstrate Jira agent capabilities."""
    print("🤖 Jira Agent Example")
    print("=" * 50)
    
    try:
        # Create the agent
        agent = JiraAgent()
        
        # Example queries you can ask the agent
        example_queries = [
            "show me my jira tickets",
            "what tickets do I have?",
            "get details for ticket KAN-4", 
            "what is the summary of KAN-1?",
            "tell me about ticket KAN-2"
        ]
        
        print("You can ask the agent questions like:")
        for i, query in enumerate(example_queries, 1):
            print(f"  {i}. {query}")
        
        print(f"\nLet's try the first example...")
        print(f"\n👤 User: {example_queries[0]}")
        print(f"🤖 Agent: ", end="")
        
        response = agent.run(example_queries[0])
        print(response)
        
        print(f"\n💡 You can modify this script to try other queries!")
        print(f"💡 Or create your own agent instances in your code.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure to run 'python test_agent.py' first to verify setup.")

if __name__ == "__main__":
    main()
