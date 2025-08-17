#!/usr/bin/env python3
"""
Simple Chat Interface for the Generic MCP Agent.

This provides an interactive chat interface like the previous version,
but using the new simple, generic MCP client architecture.
"""

import asyncio
import sys
from pathlib import Path

from src.agent import create_simple_agent

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """Interactive chat interface with the generic MCP agent."""

    print("🚀 Starting Simple MCP Agent Chat Interface...")
    print("Creating agent and fetching tools...")

    try:
        # Create and initialize the agent
        agent = await create_simple_agent()

        print(f"✅ Agent ready with {len(agent.tools)} tools!")
        print("=" * 50)
        print("🤖 Simple MCP Agent Chat")
        print("Type your questions (or 'quit' to exit):")
        print("=" * 50)

        # Interactive chat loop
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()

                # Check for exit
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                # Process the query
                print("Assistant: ", end="", flush=True)
                response = await agent.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n👋 Chat interrupted. Goodbye!")
                break
            except EOFError:
                print("\n👋 Chat ended. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error processing query: {e}")

    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
