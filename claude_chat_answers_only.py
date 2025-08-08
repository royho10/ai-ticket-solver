"""
Claude Sonnet 4 + MCP Jira Chat Interface (Answers Only)
Minimal interface showing only user input and agent responses.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_client.agent import ClaudeJiraAgent


async def main():
    """Minimal chat loop showing only user input and agent responses."""

    print("🤖 Claude Jira Assistant")
    print("Type your questions (or 'quit' to exit):")
    print("-" * 40)

    # Set environment for minimal output
    import os

    os.environ.update(
        {
            "MCP_VERBOSE": "false",
            "MCP_DEBUG": "false",
            "NODE_ENV": "production",
            "ANTHROPIC_LOG_LEVEL": "ERROR",
        }
    )

    # Initialize the agent silently
    try:
        agent = ClaudeJiraAgent(
            verbose=False,  # Disable verbose output
            mcp_verbose=False,  # Disable MCP protocol output
        )

        # Initialize connections
        await agent.initialize_all_connections()
        print("Ready!\n")

    except Exception as e:
        # Only show meaningful errors
        error_msg = str(e)
        if not any(
            noise in error_msg.lower()
            for noise in ["domexception", "aborterror", "http 404", "mcp-remote"]
        ):
            print(f"Failed to start: {error_msg}")
        return

    # Chat loop - only show user input and responses
    while True:
        try:
            print("You: ", end="", flush=True)
            user_input = input().strip()

            if user_input.lower() in ["quit", "exit", "bye", "q"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            print("Assistant: ", end="", flush=True)
            response = await agent.run(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            # Only show meaningful errors
            error_msg = str(e)
            if not any(
                noise in error_msg.lower()
                for noise in [
                    "domexception",
                    "aborterror",
                    "http 404",
                    "mcp-remote",
                    "connection",
                    "transport",
                    "undici",
                    "abort",
                ]
            ):
                print(f"Error: {error_msg}")
                print()


def sync_main():
    """Synchronous wrapper for the async main function."""
    return asyncio.run(main())


if __name__ == "__main__":
    print("🚀 Starting Claude Sonnet 4 + MCP Jira Chat Interface...")
    print()

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ This application requires Python 3.8 or higher")
        print(f"   Current version: {sys.version}")
        sys.exit(1)

    try:
        sync_main()
    except KeyboardInterrupt:
        print("\n👋 Chat interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Failed to start chat interface: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you have set ANTHROPIC_API_KEY in .env")
        print(
            "   2. Verify all dependencies are installed: pip install -r requirements.txt"
        )
        print("   3. Check that your Jira credentials are correct")
        sys.exit(1)
