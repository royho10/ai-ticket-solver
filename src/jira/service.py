import requests
import os
import base64
from typing import Dict
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (look for it in project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Get environment variables first, then fall back to config file
JIRA_API_BASE = os.getenv("JIRA_API_BASE", "").strip("\"'")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "").strip("\"'")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "").strip("\"'")

# If not found in environment, try config file
if not JIRA_API_BASE or not JIRA_API_TOKEN or not JIRA_EMAIL:
    try:
        from configs.config import (
            JIRA_API_BASE as CONFIG_BASE,
            JIRA_API_TOKEN as CONFIG_TOKEN,
            JIRA_EMAIL as CONFIG_EMAIL,
        )

        JIRA_API_BASE = JIRA_API_BASE or CONFIG_BASE
        JIRA_API_TOKEN = JIRA_API_TOKEN or CONFIG_TOKEN
        JIRA_EMAIL = JIRA_EMAIL or CONFIG_EMAIL
    except ImportError:
        # Final fallback to defaults
        JIRA_API_BASE = JIRA_API_BASE or "https://yourcompany.atlassian.net/rest/api/3"
        JIRA_API_TOKEN = JIRA_API_TOKEN or "your_api_token"
        JIRA_EMAIL = JIRA_EMAIL or "you@example.com"

# Remove quotes if present (from .env file)
# Already handled above by stripping quotes when loading from environment
JIRA_API_TOKEN = JIRA_API_TOKEN.strip('"') if JIRA_API_TOKEN else ""
JIRA_EMAIL = JIRA_EMAIL.strip('"') if JIRA_EMAIL else ""


class JiraService:
    """Service layer for Jira API interactions."""

    def __init__(self):
        self.base_url = JIRA_API_BASE
        # Proper Basic Auth for Jira API token
        auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_base64}",
            "Accept": "application/json",
        }

    def get_issue(self, issue_id: str) -> Dict:
        """Get a Jira issue by its ID."""
        url = f"{self.base_url}/issue/{issue_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search_my_issues(self) -> Dict:
        """Search for issues assigned to the current user or reported by them."""
        # JQL query to find issues assigned to current user OR reported by current user
        jql = "(assignee = currentUser() OR reporter = currentUser()) ORDER BY updated DESC"
        url = f"{self.base_url}/search"
        params = {
            "jql": jql,
            "maxResults": 10,
            "fields": "summary,status,priority,updated,assignee,reporter"
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


# Convenience function for backward compatibility
def get_jira_issue(issue_id: str) -> Dict:
    """Get a Jira issue by its ID."""
    service = JiraService()
    return service.get_issue(issue_id)
