#!/usr/bin/env python3
"""
Interactive Jira Agent Chat
Simple script to chat with your Jira agent and experiment with prompts.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from jira.agent import JiraAgent

def main():
    """Interactive chat with the Jira agent."""
    print("🤖 Interactive Jira Agent Chat")
    print("=" * 50)
    print("Ask questions about your Jira tickets in natural language!")
    print("Examples:")
    print("  • show me my tickets")
    print("  • what is KAN-4 about?")  
    print("  • get details for ticket KAN-1")
    print("  • how many tickets do I have?")
    print()
    print("Type 'quit' or 'exit' to stop")
    print("=" * 50)
    
    try:
        # Create the agent (less verbose for cleaner chat)
        agent = JiraAgent(verbose=False)
        print("✅ Agent ready! Start asking questions...\n")
        
        while True:
            # Get user input
            user_input = input("👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                print("Please ask a question about Jira tickets!")
                continue
            
            try:
                # Send to agent and get response
                print("🤖 Agent: ", end="", flush=True)
                response = agent.run(user_input)
                print(response)
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Try asking a different question!\n")
    
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        print("Make sure to run 'python test_agent.py' first to verify setup.")

if __name__ == "__main__":
    main()
