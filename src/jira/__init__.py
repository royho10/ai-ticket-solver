"""
Jira domain package for ticket_solver.

This package contains all Jira-related functionality including:
- Agent: JiraAgent for LangChain-based interactions
- Service: JiraService for API interactions
- Tools: LangChain tools for Jira operations
- Models: Pydantic models for Jira data structures
"""

from .agent import JiraAgent, create_jira_agent
from .service import JiraService, get_jira_issue
from .tools import jira_tools
from .models import (
    JiraIssue,
    JiraIssueFields,
    JiraUser,
    JiraStatus,
    JiraPriority,
    JiraProject,
)

__all__ = [
    # Agent
    "JiraAgent",
    "create_jira_agent",
    # Service
    "JiraService",
    "get_jira_issue",
    # Tools
    "jira_tools",
    # Models
    "JiraIssue",
    "JiraIssueFields",
    "JiraUser",
    "JiraStatus",
    "JiraPriority",
    "JiraProject",
]
