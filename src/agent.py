"""
Simple Agent using MCP tools and Claude directly.

This agent dynamically gets tools from MCP servers and uses Claude
to handle user queries without any server-specific code.
"""

from typing import List
import anthropic

from .mcp_client.mcp_client import MCPClientManager


class SimpleAgent:
    """Simple agent that uses Claude with dynamically fetched MCP tools."""

    def __init__(
        self, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0
    ):
        self.anthropic_client = anthropic.Anthropic()
        self.model = model
        self.temperature = temperature
        self.mcp_manager = MCPClientManager()
        self.tools = []

    async def initialize(self):
        """Initialize the agent by fetching tools from MCP servers."""
        # Fetch tools dynamically from all registered adapters
        self.tools = await self.mcp_manager.get_tools()
        print(f"🤖 Agent initialized with {len(self.tools)} tools")

    def register_adapter(self, adapter):
        """Register an MCP adapter."""
        self.mcp_manager.register_adapter(adapter)

    async def chat(self, query: str, system_prompt: str = None) -> str:
        """
        Process a user query using Claude with available tools.

        Args:
            query: User's question or request
            system_prompt: Optional system prompt to guide the agent

        Returns:
            Agent's response
        """
        if not self.tools:
            await self.initialize()

        try:
            # Convert LangChain tools to Claude tool format
            claude_tools = self._convert_tools_for_claude()

            # Build system prompt
            default_system = """You are a helpful assistant with access to various tools.

When you need to use a tool to answer the user's question, use the appropriate tool and provide a response based on the results.

For Jira queries, be efficient:
- ALWAYS start by getting the cloudId using Atlassian_getAccessibleAtlassianResources
- Then use Atlassian_searchJiraIssuesUsingJql directly for ticket searches
- Don't call Atlassian_atlassianUserInfo unless specifically asked for user information
- For user's tickets: "assignee = currentUser() ORDER BY updated DESC"
- For tickets they reported: "reporter = currentUser() ORDER BY created DESC" 
- For recent tickets: "updated >= -7d ORDER BY updated DESC"

Be helpful and provide clear, concise responses based on actual tool results."""

            if system_prompt:
                final_system = f"{system_prompt}\n\n{default_system}"
            else:
                final_system = default_system

            # First call to Claude with tools
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=self.temperature,
                system=final_system,
                tools=claude_tools,
                messages=[{"role": "user", "content": query}],
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                return await self._handle_tool_calls(response, query, final_system)
            else:
                # Find the text content in the response
                for content_block in response.content:
                    if content_block.type == "text":
                        return content_block.text
                return "No text response found"

        except Exception as e:
            return f"Error processing query: {str(e)}"

    async def _handle_tool_calls(
        self, response, original_query: str, system_prompt: str
    ) -> str:
        """Handle tool calls from Claude, including chained tool calls."""
        messages = [{"role": "user", "content": original_query}]

        current_response = response
        max_iterations = 3  # Reduced from 5 to save API calls
        iteration = 0

        while current_response.stop_reason == "tool_use" and iteration < max_iterations:
            iteration += 1
            print(f"🔧 Tool call iteration {iteration}")

            # Add Claude's response with tool calls
            claude_content = []
            for content_block in current_response.content:
                if content_block.type == "text":
                    claude_content.append({"type": "text", "text": content_block.text})
                elif content_block.type == "tool_use":
                    claude_content.append(
                        {
                            "type": "tool_use",
                            "id": content_block.id,
                            "name": content_block.name,
                            "input": content_block.input,
                        }
                    )

            messages.append({"role": "assistant", "content": claude_content})

            # Execute tools and add results
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        # Find the tool and execute it
                        tool_name = content_block.name
                        tool_input = content_block.input
                        print(
                            f"🔧 Executing tool: {tool_name} with input: {tool_input}"
                        )

                        # Find the tool in our tools list
                        tool = next(
                            (t for t in self.tools if t.name == tool_name), None
                        )
                        if tool:
                            # Execute tool using standard LangChain interface
                            result = await tool.ainvoke(tool_input)
                            print(f"✅ Tool result length: {len(str(result))}")

                            messages.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": content_block.id,
                                            "content": str(result),
                                        }
                                    ],
                                }
                            )
                        else:
                            print(f"❌ Tool not found: {tool_name}")
                            messages.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": content_block.id,
                                            "content": f"Tool {tool_name} not found",
                                        }
                                    ],
                                }
                            )
                    except Exception as e:
                        print(f"❌ Tool execution error: {e}")
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": content_block.id,
                                        "content": f"Error executing tool: {str(e)}",
                                    }
                                ],
                            }
                        )

            # Get next response from Claude
            print(f"📤 Sending {len(messages)} messages to Claude")
            current_response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=self.temperature,
                system=system_prompt,
                tools=self._convert_tools_for_claude(),
                messages=messages,
            )
            print(f"📥 Got response with stop_reason: {current_response.stop_reason}")

        # Find the text content in the final response
        for content_block in current_response.content:
            if content_block.type == "text":
                return content_block.text

        return "No text response found in final response"

    def _convert_tools_for_claude(self) -> List[dict]:
        """Convert LangChain tools to Claude tool format."""
        claude_tools = []
        for tool in self.tools:
            claude_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {"type": "object", "properties": {}, "required": []},
            }

            # Try to extract schema from the tool if available
            if hasattr(tool, "args_schema") and tool.args_schema:
                # Convert Pydantic schema to JSON schema
                schema = tool.args_schema.model_json_schema()
                # Ensure the schema has required fields for Claude
                if isinstance(schema, dict):
                    # Make sure it has type: object
                    if "type" not in schema:
                        schema["type"] = "object"
                    # Make sure it has properties
                    if "properties" not in schema:
                        schema["properties"] = {}
                    # Make sure it has required array
                    if "required" not in schema:
                        schema["required"] = []
                    claude_tool["input_schema"] = schema
            elif hasattr(tool, "get_input_schema"):
                # Alternative: use get_input_schema method
                try:
                    schema_class = tool.get_input_schema()
                    if schema_class and hasattr(schema_class, "model_json_schema"):
                        schema = schema_class.model_json_schema()
                        # Extract just the tool parameters, not the LangChain wrapper
                        if "properties" in schema and "args" in schema["properties"]:
                            # This is the LangChain wrapper format
                            args_schema = schema["properties"]["args"]
                            if "items" in args_schema and isinstance(
                                args_schema["items"], dict
                            ):
                                schema = args_schema["items"]

                        # Ensure the schema has required fields for Claude
                        if isinstance(schema, dict):
                            if "type" not in schema:
                                schema["type"] = "object"
                            if "properties" not in schema:
                                schema["properties"] = {}
                            if "required" not in schema:
                                schema["required"] = []
                            claude_tool["input_schema"] = schema
                except Exception as e:
                    print(f"Warning: Could not extract schema for {tool.name}: {e}")

            claude_tools.append(claude_tool)

        return claude_tools

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]


async def create_simple_agent() -> SimpleAgent:
    """
    Create and initialize a simple agent with default adapters.

    This is a convenience function that automatically registers
    the Atlassian adapter and initializes the agent.
    """
    from .mcp_client.adapters.atlassian_mcp_adapter import create_atlassian_adapter

    agent = SimpleAgent()

    # Register default adapters
    atlassian_adapter = create_atlassian_adapter()
    agent.register_adapter(atlassian_adapter)

    # You can easily add more adapters here:
    # github_adapter = create_github_adapter()
    # agent.register_adapter(github_adapter)

    # Initialize agent with registered adapters
    await agent.initialize()

    return agent
