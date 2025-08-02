"""
Jira domain package for ticket_solver.

This package contains Jira-related functionality:
- Service: JiraService for API interactions with Jira
"""

from .service import JiraService, get_jira_issue

__all__ = [
    "JiraService",
    "get_jira_issue",
]
