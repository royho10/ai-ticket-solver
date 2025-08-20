"""
Simple Agent using LangChain and MCP tools.

This agent uses LangChain's built-in tool calling and conversation handling
with dynamically fetched MCP tools.
"""

from typing import List, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from .mcp_client.mcp_client import MCPClientManager


class SimpleAgent:
    """Simple agent that uses LangChain with dynamically fetched MCP tools."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0,
        max_iterations: int = 3,
    ):
        self.llm = ChatAnthropic(
            model=model,
            temperature=temperature,
        )
        self.mcp_manager = MCPClientManager()
        self.tools = []
        self.agent_executor = None
        self.max_iterations = max_iterations

    async def initialize(self):
        """Initialize the agent by fetching tools from MCP servers."""
        # Fetch tools dynamically from all registered adapters
        self.tools = await self.mcp_manager.get_tools()
        print(f"🤖 Agent initialized with {len(self.tools)} tools")

        # Create the agent with LangChain
        self._create_agent()

    def register_adapter(self, adapter):
        """Register an MCP adapter."""
        self.mcp_manager.register_adapter(adapter)

    def _create_agent(self):
        """Create the LangChain agent with tools."""
        if not self.tools:
            print("🤖 Creating basic agent without MCP tools")
            self.agent_executor = None
            return

        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create the agent
        agent = create_tool_calling_agent(
            llm=self.llm, 
            tools=self.tools, 
            prompt=prompt)

        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            max_iterations=self.max_iterations,
            verbose=False,
            handle_parsing_errors=True,
            return_intermediate_steps=False,
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are a helpful assistant with access to various tools.

When you need to use a tool to answer the user's question, use the appropriate tool and provide a response based on the results.

For Jira queries, be efficient:
- ALWAYS start by getting the cloudId using Atlassian_getAccessibleAtlassianResources
- Then use Atlassian_searchJiraIssuesUsingJql directly for ticket searches
- Don't call Atlassian_atlassianUserInfo unless specifically asked for user information
- For user's tickets: "assignee = currentUser() ORDER BY updated DESC"
- For tickets they reported: "reporter = currentUser() ORDER BY created DESC" 
- For recent tickets: "updated >= -7d ORDER BY updated DESC"

Be helpful and provide clear, concise responses based on actual tool results."""

    async def chat(self, query: str, system_prompt: Optional[str] = None) -> str:
        """
        Process a user query using LangChain agent with available tools.

        Args:
            query: User's question or request
            system_prompt: Optional system prompt to override default

        Returns:
            Agent's response
        """
        if not self.agent_executor:
            await self.initialize()

        if not self.agent_executor:
            return "Error: Agent not properly initialized"

        try:
            result = await self.agent_executor.ainvoke({"input": query})
        
            # Simple extraction - just get the "output" and convert to clean string
            output = result.get("output", str(result))
            
            # If it's still a list of dicts, extract the text
            if isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict):
                return output[0].get("text", str(output))
            
            return str(output)
                
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def _override_system_prompt(self, new_prompt: str):
        """Override the system prompt and recreate the agent."""
        # Create new prompt template with custom system message
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", new_prompt),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Recreate agent with new prompt
        agent = create_tool_calling_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        # Update the agent executor
        self.agent_executor.agent = agent

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
