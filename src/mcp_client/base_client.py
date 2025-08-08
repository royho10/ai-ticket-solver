"""
Base MCP Client for connecting to any MCP server.

This module provides generic MCP functionality that can work with any MCP server,
following the Model Context Protocol specification.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, Resource


class MCPTransportType(Enum):
    """Supported MCP transport types."""

    STDIO = "stdio"
    HTTP_SSE = "http_sse"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""

    name: str
    transport_type: MCPTransportType
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None

    def to_server_params(self, mcp_verbose: bool = False) -> StdioServerParameters:
        """Convert to MCP server parameters."""
        env = self.env or dict(os.environ)

        # Control MCP debugging output
        if not mcp_verbose:
            env = env.copy()
            env["NODE_ENV"] = "production"  # Reduce Node.js debugging
            env["DEBUG"] = ""  # Disable debug output
            env["SILENT"] = "true"  # Additional silence flag
            env["MCP_LOG_LEVEL"] = "error"  # Only show errors
            env["NPX_QUIET"] = "true"  # Quiet npx output
            # Set MCP remote to quiet mode
            env["MCP_REMOTE_QUIET"] = "true"
            # Redirect stderr to suppress debug output
            env["MCP_REMOTE_SILENT"] = "1"

        if self.transport_type == MCPTransportType.STDIO:
            return StdioServerParameters(
                command=self.command or "node", args=self.args or [], env=env
            )
        elif self.transport_type == MCPTransportType.HTTP_SSE:
            # For remote servers via mcp-remote proxy
            args = ["-y", "mcp-remote"]

            # Add URL
            if self.url:
                args.append(self.url)

            # If mcp_verbose is False, we'll need to filter output at a higher level
            # since mcp-remote doesn't respect quiet flags properly
            return StdioServerParameters(command="npx", args=args, env=env)
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")


class BaseMCPServerAdapter(ABC):
    """Abstract base class for MCP server adapters."""

    def __init__(
        self, config: MCPServerConfig, verbose: bool = True, mcp_verbose: bool = False
    ):
        self.config = config
        self.verbose = verbose
        self.mcp_verbose = mcp_verbose  # Control MCP-level debugging
        self.available_tools: List[Tool] = []
        self.available_resources: List[Resource] = []
        self._server_params: Optional[StdioServerParameters] = None

    @abstractmethod
    async def initialize_connection(self) -> bool:
        """Initialize connection to the MCP server."""
        pass

    @abstractmethod
    def parse_query_intent(self, query: str) -> List[tuple]:
        """Parse user query and determine which tools to execute."""
        pass

    @abstractmethod
    async def execute_server_specific_tool(
        self, session: ClientSession, tool_name: str, parameters: Any, **kwargs
    ) -> str:
        """Execute a server-specific tool with proper parameter handling."""
        pass

    async def discover_capabilities(self, session: ClientSession) -> Dict[str, Any]:
        """Discover server capabilities (tools, resources, etc.)."""
        capabilities = {}

        try:
            # Get available tools
            tools_response = await asyncio.wait_for(session.list_tools(), timeout=20.0)
            self.available_tools = tools_response.tools
            capabilities["tools"] = [tool.name for tool in self.available_tools]

            if self.verbose:
                print(
                    f"🔧 [{self.config.name}] Available tools: {capabilities['tools']}"
                )

        except Exception as e:
            if self.verbose:
                print(f"⚠️ [{self.config.name}] Could not list tools: {e}")
            capabilities["tools"] = []

        try:
            # Try to get resources (may not be available)
            resources_response = await asyncio.wait_for(
                session.list_resources(), timeout=10.0
            )
            self.available_resources = resources_response.resources
            capabilities["resources"] = [res.name for res in self.available_resources]

            if self.verbose:
                print(
                    f"📚 [{self.config.name}] Available resources: {capabilities['resources']}"
                )

        except Exception:
            capabilities["resources"] = []

        return capabilities

    def format_capabilities_summary(self) -> str:
        """Format available capabilities for display."""
        tools_count = len(self.available_tools)
        resources_count = len(self.available_resources)

        summary = f"**{self.config.name} MCP Server:**\n"
        summary += f"- Tools: {tools_count}\n"
        summary += f"- Resources: {resources_count}\n"

        if self.available_tools:
            summary += "\n**Available Tools:**\n"
            for tool in self.available_tools[:10]:  # Limit to first 10
                summary += f"- **{tool.name}**: {tool.description}\n"

            if len(self.available_tools) > 10:
                summary += f"- ... and {len(self.available_tools) - 10} more tools\n"

        return summary


class GenericMCPClient:
    """
    Generic MCP client that can connect to multiple MCP servers.

    This client follows the MCP specification and can work with any compliant server.
    Server-specific functionality is handled by adapter classes.
    """

    def __init__(
        self,
        ai_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0,
        verbose: bool = True,
        mcp_verbose: bool = False,
    ):
        self.ai_model = ai_model
        self.temperature = temperature
        self.verbose = verbose
        self.mcp_verbose = mcp_verbose  # Separate control for MCP debugging

        # Initialize AI client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_api_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set it in your .env file."
            )

        self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        self.server_adapters: Dict[str, BaseMCPServerAdapter] = {}

    def register_mcp_server(self, adapter: BaseMCPServerAdapter) -> None:
        """Register an MCP server adapter."""
        self.server_adapters[adapter.config.name] = adapter
        if self.verbose:
            print(f"📝 Registered MCP server: {adapter.config.name}")

    async def initialize_all_connections(self) -> Dict[str, bool]:
        """Initialize connections to all registered MCP servers."""
        results = {}

        for name, adapter in self.server_adapters.items():
            if self.verbose:
                print(f"🔗 Connecting to {name} MCP server...")

            try:
                # Pass MCP verbosity setting to server params
                adapter._server_params = adapter.config.to_server_params(
                    self.mcp_verbose
                )
                success = await adapter.initialize_connection()
                results[name] = success

                if success and self.verbose:
                    print(f"✅ Connected to {name} MCP server!")
                elif not success and self.verbose:
                    print(f"❌ Failed to connect to {name} MCP server")

            except Exception as e:
                if self.verbose:
                    print(f"❌ Error connecting to {name}: {str(e)}")
                results[name] = False

        return results

    async def execute_multi_server_query(self, query: str) -> str:
        """Execute a query across multiple MCP servers."""

        # Check for capability listing requests
        if self._is_capability_listing_query(query):
            return await self._format_all_capabilities()

        # Determine which servers can handle this query
        relevant_adapters = self._determine_relevant_servers(query)

        if not relevant_adapters:
            return await self._fallback_ai_response(query)

        # Execute query on relevant servers
        all_results = []

        for adapter_name, adapter in relevant_adapters.items():
            try:
                result = await self._execute_on_single_server(adapter, query)
                all_results.append(f"**{adapter_name} Results:**\n{result}")

            except Exception as e:
                all_results.append(f"**{adapter_name} Error:** {str(e)}")

        # Combine results with AI enhancement
        return await self._enhance_combined_results(query, all_results)

    def _is_capability_listing_query(self, query: str) -> bool:
        """Check if query is asking for available tools/capabilities."""
        query_lower = query.lower()
        return any(
            phrase in query_lower
            for phrase in [
                "what tools",
                "available tools",
                "tools do you have",
                "list tools",
                "what can you do",
                "capabilities",
            ]
        )

    async def _format_all_capabilities(self) -> str:
        """Format capabilities from all connected servers."""
        if not self.server_adapters:
            return "No MCP servers are currently connected."

        capabilities_text = "# Available MCP Capabilities\n\n"

        # Force capability discovery for each server if not already done
        for name, adapter in self.server_adapters.items():
            # If no tools discovered yet, try to discover them
            if not adapter.available_tools and adapter._server_params:
                try:
                    from mcp.client.stdio import stdio_client
                    from mcp import ClientSession

                    async with stdio_client(adapter._server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await asyncio.wait_for(session.initialize(), timeout=30.0)
                            await adapter.discover_capabilities(session)

                except Exception as e:
                    if self.verbose:
                        print(f"⚠️ Failed to discover capabilities for {name}: {e}")

            capabilities_text += adapter.format_capabilities_summary() + "\n"

        capabilities_text += (
            f"\nTotal: {len(self.server_adapters)} MCP server(s) connected."
        )
        return capabilities_text

    def _determine_relevant_servers(
        self, query: str
    ) -> Dict[str, BaseMCPServerAdapter]:
        """Determine which MCP servers are relevant for the query."""
        relevant = {}

        for name, adapter in self.server_adapters.items():
            # Let each adapter decide if it can handle the query
            tools_to_execute = adapter.parse_query_intent(query)
            if tools_to_execute:
                relevant[name] = adapter

        return relevant

    async def _execute_on_single_server(
        self, adapter: BaseMCPServerAdapter, query: str
    ) -> str:
        """Execute query on a single MCP server."""

        async with stdio_client(adapter._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await asyncio.wait_for(session.initialize(), timeout=30.0)

                # Discover capabilities
                await adapter.discover_capabilities(session)

                # Parse query and execute tools
                tools_to_execute = adapter.parse_query_intent(query)

                if not tools_to_execute:
                    return "No relevant tools found for this query."

                results = []
                for tool_name, parameters in tools_to_execute:
                    try:
                        result = await adapter.execute_server_specific_tool(
                            session, tool_name, parameters
                        )
                        results.append(f"Tool '{tool_name}': {result}")

                    except Exception as e:
                        results.append(f"Tool '{tool_name}' failed: {str(e)}")

                return "\n".join(results)

    async def _fallback_ai_response(self, query: str) -> str:
        """Provide AI response when no MCP servers can handle the query."""
        system_prompt = """You are a helpful assistant. The user's query could not be handled by any connected MCP servers. Provide a helpful response explaining what you can do and suggest how they might rephrase their query."""

        response = self.anthropic_client.messages.create(
            model=self.ai_model,
            max_tokens=512,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
        )

        return response.content[0].text

    async def _enhance_combined_results(self, query: str, results: List[str]) -> str:
        """Use AI to enhance and combine results from multiple servers."""
        if not results:
            return await self._fallback_ai_response(query)

        combined_data = "\n\n".join(results)

        enhanced_query = f"""
Original user query: {query}

Results from MCP servers:
{combined_data}

Please provide a comprehensive, well-organized response based on the MCP server results above. Synthesize the information and present it in a user-friendly way.
"""

        response = self.anthropic_client.messages.create(
            model=self.ai_model,
            max_tokens=1024,
            temperature=self.temperature,
            messages=[{"role": "user", "content": enhanced_query}],
        )

        return response.content[0].text

    async def run_query(self, query: str) -> str:
        """
        Main entry point for executing queries across MCP servers.

        Args:
            query: The user's question or request

        Returns:
            str: The combined response from relevant MCP servers
        """
        try:
            return await self.execute_multi_server_query(query)
        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg

    def run_query_sync(self, query: str) -> str:
        """Synchronous wrapper for run_query."""
        return asyncio.run(self.run_query(query))
