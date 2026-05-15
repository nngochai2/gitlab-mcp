# gitlab-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes GitLab issues and merge requests as tools. Built for the ADLC (AI-Driven Development Lifecycle) workflow at Fsoft, targeting self-hosted GitLab instances.

## Setup

**Prerequisites:** Python 3.11+

```powershell
# Install dependencies
pip install -r gitlab_mcp/requirements.txt

# Configure via environment variables or a .env file in the project root
GITLAB_URL=https://your-gitlab-instance.example.com
GITLAB_TOKEN=<your-personal-access-token>
GITLAB_SSL_VERIFY=false   # set to false for self-signed certificates
```

## Running

```powershell
python -m gitlab_mcp
```

The server starts on `http://0.0.0.0:8000`. Override with `MCP_HOST` / `MCP_PORT`.

| Endpoint | Purpose |
|---|---|
| `GET /sse` | SSE stream — connect your MCP client here |
| `POST /messages/` | MCP message endpoint |

## Available tools

### Issues

| Tool | Description |
|---|---|
| `gitlab_list_issues` | List issues with filters (state, labels, assignee, search) |
| `gitlab_get_issue` | Get full details of an issue by IID |
| `gitlab_create_issue` | Create a new issue |
| `gitlab_update_issue` | Update title, description, labels, assignees, or state |
| `gitlab_close_issue` | Close an issue |
| `gitlab_delete_issue` | Permanently delete an issue (requires Owner/Admin) |
| `gitlab_create_issue_note` | Post a comment on an issue |
| `gitlab_link_issues` | Link two issues (`blocks`, `is_blocked_by`, `relates_to`) |

### Merge Requests

| Tool | Description |
|---|---|
| `gitlab_list_merge_requests` | List MRs with filters (state, branch, author, search) |
| `gitlab_get_merge_request` | Get details including pipeline status and reviewers |
| `gitlab_get_merge_request_changes` | Get the unified diff of an MR |
| `gitlab_get_merge_request_discussions` | Get all discussion threads and comments |
| `gitlab_create_merge_request_note` | Post a comment on an MR |
| `gitlab_approve_merge_request` | Approve an MR (restricted to MRs you authored) |
| `gitlab_merge_merge_request` | Merge an MR — squash and branch deletion optional (restricted to MRs you authored) |

All tools accept an optional `project_id` (numeric ID or path such as `"group/project"`). When omitted, `GITLAB_PROJECT_ID` is used as the default.

## MCP client configuration

Point your MCP client at the SSE endpoint:

```json
{
  "mcpServers": {
    "gitlab": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GITLAB_URL` | `https://gitlab.com` | GitLab instance URL |
| `GITLAB_TOKEN` | *(required)* | Personal access token |
| `GITLAB_PROJECT_ID` | *(optional)* | Default project ID or path — omit `project_id` from tool calls when set |
| `GITLAB_SSL_VERIFY` | `true` | Set to `false` to disable TLS verification |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_PORT` | `8000` | Bind port |
