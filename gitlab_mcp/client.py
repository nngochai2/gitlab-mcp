import os
from functools import lru_cache
from typing import Any

import gitlab


@lru_cache(maxsize=1)
def get_gitlab() -> gitlab.Gitlab:
    url = os.environ.get("GITLAB_URL", "https://gitlab.com")
    token = os.environ.get("GITLAB_TOKEN")
    ssl_verify = os.environ.get("GITLAB_SSL_VERIFY", "true").lower() != "false"

    if not token:
        raise ValueError("GITLAB_TOKEN environment variable is required")

    return gitlab.Gitlab(url, private_token=token, ssl_verify=ssl_verify)


def get_project(project_id: str | int) -> Any:
    return get_gitlab().projects.get(project_id)
