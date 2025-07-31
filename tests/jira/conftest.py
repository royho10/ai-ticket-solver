"""Test configuration and fixtures for Jira tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_jira_issue_data():
    """Mock Jira issue data for testing."""
    return {
        "id": "12345",
        "key": "PROJ-123",
        "self": "https://example.atlassian.net/rest/api/3/issue/12345",
        "fields": {
            "summary": "Test issue summary",
            "description": "Test issue description",
            "status": {"id": "1", "name": "Open", "description": "Issue is open"},
            "assignee": {
                "accountId": "12345",
                "displayName": "John Doe",
                "emailAddress": "john.doe@example.com",
                "active": True,
            },
            "reporter": {
                "accountId": "67890",
                "displayName": "Jane Smith",
                "emailAddress": "jane.smith@example.com",
                "active": True,
            },
            "priority": {
                "id": "3",
                "name": "Medium",
                "iconUrl": "https://example.com/medium.png",
            },
            "project": {
                "id": "10001",
                "key": "PROJ",
                "name": "Test Project",
                "projectTypeKey": "software",
            },
            "labels": ["bug", "frontend"],
            "created": "2023-01-01T10:00:00.000Z",
            "updated": "2023-01-02T15:30:00.000Z",
        },
    }


@pytest.fixture
def mock_jira_service():
    """Mock JiraService for testing."""
    return MagicMock()
