from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class JiraUser(BaseModel):
    """Jira user model."""

    accountId: str
    displayName: str
    emailAddress: Optional[str] = None
    active: bool = True


class JiraStatus(BaseModel):
    """Jira issue status model."""

    id: str
    name: str
    description: Optional[str] = None


class JiraPriority(BaseModel):
    """Jira priority model."""

    id: str
    name: str
    iconUrl: Optional[str] = None


class JiraProject(BaseModel):
    """Jira project model."""

    id: str
    key: str
    name: str
    projectTypeKey: str


class JiraIssueFields(BaseModel):
    """Jira issue fields model."""

    summary: str
    description: Optional[str] = None
    status: JiraStatus
    assignee: Optional[JiraUser] = None
    reporter: Optional[JiraUser] = None
    priority: Optional[JiraPriority] = None
    project: JiraProject
    labels: List[str] = []
    created: Optional[str] = None
    updated: Optional[str] = None


class JiraIssue(BaseModel):
    """Jira issue model."""

    id: str
    key: str
    self: str  # URL to the issue
    fields: JiraIssueFields

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "JiraIssue":
        """Create a JiraIssue from API response data."""
        return cls(
            id=data["id"],
            key=data["key"],
            self=data["self"],
            fields=JiraIssueFields(
                summary=data["fields"]["summary"],
                description=data["fields"].get("description"),
                status=JiraStatus(**data["fields"]["status"]),
                assignee=JiraUser(**data["fields"]["assignee"])
                if data["fields"].get("assignee")
                else None,
                reporter=JiraUser(**data["fields"]["reporter"])
                if data["fields"].get("reporter")
                else None,
                priority=JiraPriority(**data["fields"]["priority"])
                if data["fields"].get("priority")
                else None,
                project=JiraProject(**data["fields"]["project"]),
                labels=data["fields"].get("labels", []),
                created=data["fields"].get("created"),
                updated=data["fields"].get("updated"),
            ),
        )
