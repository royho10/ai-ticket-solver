from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI
from .tools import jira_tools

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class JiraAgent:
    """Agent specialized for Jira operations."""

    def __init__(self, model="gpt-4", temperature=0, verbose=True):
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.agent = initialize_agent(
            tools=jira_tools,
            llm=self.llm,
            agent="zero-shot-react-description",
            verbose=verbose,
        )

    def run(self, query: str) -> str:
        """Run a query through the Jira agent."""
        return self.agent.run(query)

    def invoke(self, input_data: dict) -> dict:
        """Invoke the agent with input data."""
        return self.agent.invoke(input_data)


def create_jira_agent():
    """Create a Jira agent instance."""
    return JiraAgent()
