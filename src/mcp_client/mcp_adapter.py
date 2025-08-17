"""
Generic MCP Server Adapter Interface.

This module defines the interface that all MCP server adapters must implement.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.tools import Tool
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters


class MCPServerAdapter(ABC):
    """Abstract base class for MCP server adapters."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        # Session management for persistent connections
        self._session: ClientSession = None
        self._streams = None
        self._stdio_context = None

    @abstractmethod
    def create_server_params(self) -> StdioServerParameters:
        """
        Create server parameters for connecting to the MCP server.

        This is the only method that needs to be vendor-specific.
        """
        pass

    async def _establish_session(self):
        """Establish a persistent session if not already established."""
        if self._session is None:
            try:
                server_params = self.create_server_params()
                self._stdio_context = stdio_client(server_params)
                self._streams = await self._stdio_context.__aenter__()
                read, write = self._streams

                self._session = ClientSession(read, write)
                await self._session.__aenter__()
                await asyncio.wait_for(self._session.initialize(), timeout=30.0)
                print(f"🔗 Established persistent session for {self.name}")
            except Exception as e:
                print(f"⚠️ Failed to establish persistent session for {self.name}: {e}")
                await self._cleanup_session()
                raise

    async def _cleanup_session(self):
        """Clean up persistent session."""
        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                self._stdio_context = None
                self._streams = None
        except Exception as e:
            print(f"Warning: Error cleaning up session for {self.name}: {e}")

    async def fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Fetch available tools from the MCP server.

        This method is generic for all MCP servers - only server_params differ.
        """
        server_params = self.create_server_params()

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=30.0)

                # Get available tools
                tools_response = await asyncio.wait_for(
                    session.list_tools(), timeout=20.0
                )

                # Convert MCP tools to our format
                tools_info = []
                for tool in tools_response.tools:
                    tools_info.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": getattr(tool, "inputSchema", {}),
                        }
                    )

                return tools_info

    async def execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        Execute a specific tool on the MCP server using persistent session.
        """
        try:
            # Ensure we have a persistent session
            await self._establish_session()

            print(f"🔍 Executing {tool_name} with args: {tool_args}")

            # Execute the tool using persistent session
            result = await self._session.call_tool(tool_name, tool_args)

            # Extract result content
            if hasattr(result, "content") and result.content:
                return (
                    result.content[0].text
                    if result.content[0].text
                    else str(result.content)
                )
            return str(result)

        except Exception as e:
            print(f"⚠️ Persistent session failed for {self.name}: {e}")
            print("🔄 Falling back to individual session")

            # Fall back to individual session
            server_params = self.create_server_params()
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=30.0)
                    result = await session.call_tool(tool_name, tool_args)

                    if hasattr(result, "content") and result.content:
                        return (
                            result.content[0].text
                            if result.content[0].text
                            else str(result.content)
                        )
                    return str(result)

    def parse_tool_input(self, tool_name: str, input_str: str) -> Dict[str, Any]:
        """
        Parse input string into tool parameters.

        Base implementation with sensible defaults. Can be overridden by subclasses.
        """
        import json

        # Try to parse as JSON first
        try:
            return json.loads(input_str)
        except Exception:
            pass

        # Generic fallback
        return {"input": input_str}

    def wrap_tool(self, tool_meta: Dict[str, Any]) -> Tool:
        """
        Wrap a tool metadata into a LangChain Tool object.

        This method is the same for all adapters.
        """
        from pydantic import create_model
        from typing import Optional
        from langchain.tools import StructuredTool

        async def async_tool_func(**kwargs) -> str:
            """Execute the MCP tool with the given input."""
            try:
                print(f"🔍 Tool {tool_meta['name']} called with kwargs: {kwargs}")

                # Convert kwargs to JSON string for MCP
                if kwargs:
                    # For MCP, we need to pass the arguments directly, not as a JSON string
                    result = await self.execute_tool(tool_meta["name"], kwargs)
                else:
                    result = await self.execute_tool(tool_meta["name"], {})

                print(f"🔍 Tool {tool_meta['name']} result: {result[:100]}...")
                return result
            except Exception as e:
                error_msg = f"Error executing {tool_meta['name']}: {str(e)}"
                print(f"❌ {error_msg}")
                return error_msg

        # Create Pydantic model for parameters
        parameters = tool_meta.get("parameters", {})
        args_schema = None

        if parameters and isinstance(parameters, dict):
            properties = parameters.get("properties", {})
            required = parameters.get("required", [])

            if properties:
                # Build fields for the Pydantic model
                fields = {}
                for field_name, field_spec in properties.items():
                    field_type = str  # Default to string

                    if field_spec.get("type") == "integer":
                        field_type = int
                    elif field_spec.get("type") == "number":
                        field_type = float
                    elif field_spec.get("type") == "boolean":
                        field_type = bool
                    elif field_spec.get("type") == "array":
                        field_type = list
                    elif field_spec.get("type") == "object":
                        field_type = dict

                    # Make field optional if not required
                    if field_name not in required:
                        field_type = Optional[field_type]
                        fields[field_name] = (field_type, None)
                    else:
                        fields[field_name] = (field_type, ...)

                # Create dynamic Pydantic model
                model_name = f"{tool_meta['name'].replace('-', '_')}_Input"
                args_schema = create_model(model_name, **fields)

        # Use StructuredTool which handles kwargs properly
        return StructuredTool.from_function(
            func=async_tool_func,
            name=f"{self.name}_{tool_meta['name']}",
            description=tool_meta.get("description", "No description provided"),
            args_schema=args_schema,
            coroutine=async_tool_func,
        )
