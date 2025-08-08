"""
Multi-MCP Server Agent with Atlassian Integration

Scalable agent architecture that can work with multiple MCP servers:
- Generic MCP client framework
- Server-specific adapters (Atlassian, future servers)
- Clean separation between generic and server-specific functionality
- Easy to extend with new MCP servers
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

from .base_client import GenericMCPClient
from .atlassian_adapter import create_atlassian_adapter


# Load environment variables
env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)


class MultiMCPAgent:
    """
    Multi-MCP Server Agent that can connect to multiple MCP servers.

    This agent provides a unified interface to work with different MCP servers
    through server-specific adapters. Currently supports:
    - Atlassian MCP Server (Jira & Confluence)

    Future servers can be easily added by creating new adapter classes.
    """

    def __init__(
        self,
        ai_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0,
        verbose: bool = True,
        mcp_verbose: bool = False,
        enable_atlassian: bool = True,
    ):
        """
        Initialize the Multi-MCP Agent.

        Args:
            ai_model: Claude model to use for AI processing
            temperature: Temperature for AI responses (0-1)
            verbose: Whether to print debug information
            mcp_verbose: Whether to show verbose MCP protocol output (False = quieter operation)
            enable_atlassian: Whether to enable Atlassian MCP server
        """
        self.verbose = verbose

        # Initialize the generic MCP client with verbosity control
        self.mcp_client = GenericMCPClient(
            ai_model=ai_model,
            temperature=temperature,
            verbose=verbose,
            mcp_verbose=mcp_verbose,
        )

        # Register MCP server adapters
        if enable_atlassian:
            self._register_atlassian_adapter()

        # Track initialization state
        self._initialized = False

    def _register_atlassian_adapter(self) -> None:
        """Register the Atlassian MCP server adapter."""
        try:
            atlassian_adapter = create_atlassian_adapter(
                verbose=self.verbose, mcp_verbose=self.mcp_client.mcp_verbose
            )
            self.mcp_client.register_mcp_server(atlassian_adapter)

            if self.verbose:
                print("📋 Registered Atlassian MCP adapter (Jira & Confluence)")

        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to register Atlassian adapter: {e}")

    async def initialize_all_connections(self) -> bool:
        """
        Initialize connections to all registered MCP servers.

        Returns:
            bool: True if at least one server connected successfully
        """
        if self._initialized:
            return True

        try:
            if self.verbose:
                print("🚀 Initializing Multi-MCP Agent...")

            # Initialize all server connections
            connection_results = await self.mcp_client.initialize_all_connections()

            # Check if any connections succeeded
            successful_connections = sum(
                1 for success in connection_results.values() if success
            )
            total_servers = len(connection_results)

            if successful_connections > 0:
                self._initialized = True
                if self.verbose:
                    print(
                        f"✅ Multi-MCP Agent ready! ({successful_connections}/{total_servers} servers connected)"
                    )
                return True
            else:
                if self.verbose:
                    print("❌ No MCP servers connected successfully")
                return False

        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to initialize MCP connections: {e}")
            return False

    async def chat(self, query: str) -> str:
        """
        Process a user query across all connected MCP servers.

        Args:
            query: The user's question or request

        Returns:
            str: The agent's response combining results from relevant servers
        """
        try:
            # Ensure connections are initialized
            if not self._initialized:
                success = await self.initialize_all_connections()
                if not success:
                    return "❌ No MCP servers are available. Please check your configuration."

            # Execute query across relevant servers
            return await self.mcp_client.execute_multi_server_query(query)

        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg

    def chat_sync(self, query: str) -> str:
        """
        Synchronous wrapper for the async chat method.

        Args:
            query: The user's question or request

        Returns:
            str: The agent's response
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, we need to handle this differently
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.chat(query))
                    return future.result()
            else:
                return asyncio.run(self.chat(query))
        except RuntimeError:
            # Fallback for event loop issues
            return asyncio.run(self.chat(query))

    def add_mcp_server_adapter(self, adapter) -> None:
        """
        Add a custom MCP server adapter.

        Args:
            adapter: An instance of BaseMCPServerAdapter or its subclass
        """
        self.mcp_client.register_mcp_server(adapter)
        # Reset initialization to force reconnection
        self._initialized = False

    def get_connected_servers(self) -> list:
        """Get list of connected MCP server names."""
        return list(self.mcp_client.server_adapters.keys())

    async def get_all_capabilities(self) -> str:
        """Get capabilities summary from all connected servers."""
        return await self.mcp_client._format_all_capabilities()


# Backward compatibility classes and functions
class ClaudeJiraAgent(MultiMCPAgent):
    """
    Backward compatibility class for ClaudeJiraAgent.

    This is now a specialized version of MultiMCPAgent that focuses on Atlassian.
    """

    def __init__(self, **kwargs):
        # Force enable only Atlassian for backward compatibility
        kwargs["enable_atlassian"] = True
        super().__init__(**kwargs)

    async def run(self, query: str) -> str:
        """Backward compatibility method."""
        return await self.chat(query)

    def run_sync(self, query: str) -> str:
        """Backward compatibility method."""
        return self.chat_sync(query)


def create_multi_mcp_agent(**kwargs) -> MultiMCPAgent:
    """
    Create a Multi-MCP agent instance.

    Args:
        **kwargs: Arguments to pass to MultiMCPAgent constructor

    Returns:
        MultiMCPAgent: A new agent instance
    """
    return MultiMCPAgent(**kwargs)


def create_claude_jira_agent(**kwargs) -> ClaudeJiraAgent:
    """
    Create a Claude Jira agent instance (backward compatibility).

    Args:
        **kwargs: Arguments to pass to ClaudeJiraAgent constructor

    Returns:
        ClaudeJiraAgent: A new agent instance focused on Atlassian
    """
    return ClaudeJiraAgent(**kwargs)


def create_jira_agent(**kwargs):
    """Create a Jira agent instance (legacy compatibility)."""
    return create_claude_jira_agent(**kwargs)


# Example of how to add new MCP servers:
#
# from .github_adapter import create_github_adapter
# from .slack_adapter import create_slack_adapter
#
# class ExtendedMultiMCPAgent(MultiMCPAgent):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#         # Add GitHub MCP server
#         if kwargs.get('enable_github', False):
#             github_adapter = create_github_adapter()
#             self.add_mcp_server_adapter(github_adapter)
#
#         # Add Slack MCP server
#         if kwargs.get('enable_slack', False):
#             slack_adapter = create_slack_adapter()
#             self.add_mcp_server_adapter(slack_adapter)
