"""
Modern Chat Interface for Claude Sonnet 4 + MCP Jira Agent

This replaces the old chat interface with a modern async implementation
using Claude Sonnet 4 and Model Context Protocol.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.mcp_client.agent import ClaudeJiraAgent


async def main():
    """Main chat loop using Claude Sonnet 4 + MCP."""

    print("🤖 Claude Sonnet 4 + MCP Jira Agent")
    print("=" * 50)
    print("💡 This agent uses Claude Sonnet 4 with Model Context Protocol")
    print("🔧 Connected to Jira via MCP tools and resources")
    print("📝 Type your questions about Jira tickets, or 'quit' to exit")
    print("=" * 50)
    print()

    # Initialize the agent
    try:
        print("🔗 Initializing MCP connection...")
        agent = ClaudeJiraAgent(
            verbose=True,  # Enable verbose for debugging
            mcp_verbose=False,  # Reduce MCP protocol output noise
        )

        # Ensure connections are initialized
        success = await agent.initialize_all_connections()
        if success:
            print("✅ Agent ready! Ask me anything about your Jira tickets.")

            # Show connected servers
            servers = agent.get_connected_servers()
            print(f"🔗 Connected to: {', '.join(servers)}")

            # Show capabilities preview
            capabilities = await agent.get_all_capabilities()
            lines = capabilities.split("\n")
            preview = (
                "\n".join(lines[:3])
                + f"\n... (showing first 3 lines of {len(lines)} total)"
            )
            print(f"🔧 Capabilities preview:\n{preview}")
        else:
            print("❌ Failed to connect to MCP servers")
            return
        print()

        print("💡 Try these example queries:")
        print("   • 'What issues are assigned to me?'")
        print("   • 'Show me details for KAN-7'")
        print("   • 'Get the description of KAN-5'")
        print("   • 'What's the status of my tickets?'")
        print()

    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check that ANTHROPIC_API_KEY is set in .env")
        print("   2. Verify Jira credentials are correct")
        print("   3. Ensure all dependencies are installed")
        return

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "bye", "q"]:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            # Process the query
            try:
                print("\n🤖 Claude:", end=" ")
                response = await agent.run(user_input)
                print(response)

            except Exception as e:
                print(f"\n❌ Error processing your request: {str(e)}")
                print("💡 Try rephrasing your question or check your configuration.")

            print()  # Add spacing between exchanges

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            print("💡 Please try again or type 'quit' to exit.")


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
