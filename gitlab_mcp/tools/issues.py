import json
from typing import Any

import gitlab.exceptions
import mcp.types as types

from ..client import get_project

ISSUE_TOOLS = [
    types.Tool(
        name="gitlab_list_issues",
        description="List issues in a GitLab project with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (numeric) or path (e.g. 'group/project')",
                },
                "state": {
                    "type": "string",
                    "enum": ["opened", "closed", "all"],
                    "default": "opened",
                    "description": "Filter by issue state",
                },
                "labels": {
                    "type": "string",
                    "description": "Comma-separated list of label names to filter by",
                },
                "assignee_username": {
                    "type": "string",
                    "description": "Filter by assignee username",
                },
                "search": {
                    "type": "string",
                    "description": "Search term to filter issues by title/description",
                },
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of results per page (max 100)",
                },
            },
            "required": ["project_id"],
        },
    ),
    types.Tool(
        name="gitlab_get_issue",
        description="Get details of a specific GitLab issue.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "issue_iid": {
                    "type": "integer",
                    "description": "Issue IID (project-scoped issue number)",
                },
            },
            "required": ["project_id", "issue_iid"],
        },
    ),
    types.Tool(
        name="gitlab_create_issue",
        description="Create a new issue in a GitLab project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "title": {"type": "string", "description": "Issue title"},
                "description": {"type": "string", "description": "Issue description (Markdown)"},
                "labels": {
                    "type": "string",
                    "description": "Comma-separated list of label names",
                },
                "assignee_usernames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of usernames to assign the issue to",
                },
                "milestone_id": {
                    "type": "integer",
                    "description": "Milestone ID to associate with the issue",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format",
                },
            },
            "required": ["project_id", "title"],
        },
    ),
    types.Tool(
        name="gitlab_update_issue",
        description="Update an existing GitLab issue (title, description, labels, assignees, state).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "issue_iid": {"type": "integer"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "labels": {
                    "type": "string",
                    "description": "Comma-separated label names (replaces existing labels)",
                },
                "state_event": {
                    "type": "string",
                    "enum": ["close", "reopen"],
                    "description": "Transition the issue state",
                },
                "assignee_usernames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replace assignees with this list (empty list clears assignees)",
                },
            },
            "required": ["project_id", "issue_iid"],
        },
    ),
    types.Tool(
        name="gitlab_close_issue",
        description="Close a GitLab issue.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "issue_iid": {"type": "integer"},
            },
            "required": ["project_id", "issue_iid"],
        },
    ),
]


def _fmt(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Error: {msg}")]


async def handle_issue_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        project = get_project(arguments["project_id"])

        if name == "gitlab_list_issues":
            kwargs: dict[str, Any] = {
                "state": arguments.get("state", "opened"),
                "per_page": arguments.get("per_page", 20),
            }
            if "labels" in arguments:
                kwargs["labels"] = arguments["labels"]
            if "assignee_username" in arguments:
                kwargs["assignee_username"] = arguments["assignee_username"]
            if "search" in arguments:
                kwargs["search"] = arguments["search"]
            issues = project.issues.list(**kwargs)
            return _fmt([_issue_summary(i) for i in issues])

        if name == "gitlab_get_issue":
            issue = project.issues.get(arguments["issue_iid"])
            return _fmt(_issue_detail(issue))

        if name == "gitlab_create_issue":
            kwargs = {"title": arguments["title"]}
            for field in ("description", "labels", "milestone_id", "due_date"):
                if field in arguments:
                    kwargs[field] = arguments[field]
            if "assignee_usernames" in arguments:
                ids = _resolve_user_ids(arguments["assignee_usernames"])
                if ids:
                    kwargs["assignee_ids"] = ids
            issue = project.issues.create(kwargs)
            return _fmt(_issue_detail(issue))

        if name == "gitlab_update_issue":
            issue = project.issues.get(arguments["issue_iid"])
            for field in ("title", "description", "labels", "state_event"):
                if field in arguments:
                    setattr(issue, field, arguments[field])
            if "assignee_usernames" in arguments:
                ids = _resolve_user_ids(arguments["assignee_usernames"])
                issue.assignee_ids = ids
            issue.save()
            return _fmt(_issue_detail(issue))

        if name == "gitlab_close_issue":
            issue = project.issues.get(arguments["issue_iid"])
            issue.state_event = "close"
            issue.save()
            return [types.TextContent(type="text", text=f"Issue #{arguments['issue_iid']} closed.")]

    except gitlab.exceptions.GitlabError as e:
        return _err(str(e))
    except Exception as e:
        return _err(str(e))

    return _err(f"Unknown tool: {name}")


def _resolve_user_ids(usernames: list[str]) -> list[int]:
    from ..client import get_gitlab

    gl = get_gitlab()
    ids = []
    for username in usernames:
        users = gl.users.list(username=username)
        if users:
            ids.append(users[0].id)
    return ids


def _issue_summary(issue: Any) -> dict[str, Any]:
    return {
        "iid": issue.iid,
        "title": issue.title,
        "state": issue.state,
        "author": issue.author.get("username") if issue.author else None,
        "assignees": [a["username"] for a in (issue.assignees or [])],
        "labels": issue.labels,
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "web_url": issue.web_url,
    }


def _issue_detail(issue: Any) -> dict[str, Any]:
    return {
        **_issue_summary(issue),
        "description": issue.description,
        "milestone": issue.milestone,
        "due_date": issue.due_date,
        "closed_at": issue.closed_at,
        "user_notes_count": issue.user_notes_count,
    }
