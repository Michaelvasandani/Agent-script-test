#!/usr/bin/env python3
"""Collect aggregate statistics for repositories accessible to a GitHub token."""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"
SCRIPT_PATH = "scripts/analyze_github_repositories.py"


def _request_json(
    path: str,
    token: str,
    opener: Callable[..., Any],
) -> tuple[Any, str]:
    request = Request(
        f"{API_ROOT}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "github-agentic-workflow-repository-statistics",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with opener(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload, response.headers.get("Link", "")
    except HTTPError as error:
        raise RuntimeError(f"GitHub API request failed with HTTP {error.code}") from None
    except (URLError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("GitHub API request failed") from None


def _list_repositories(token: str, opener: Callable[..., Any]) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1

    while True:
        query = urlencode(
            {
                "affiliation": "owner,collaborator,organization_member",
                "page": page,
                "per_page": 100,
                "sort": "full_name",
                "visibility": "all",
            }
        )
        payload, link_header = _request_json(f"/user/repos?{query}", token, opener)
        if not isinstance(payload, list):
            raise RuntimeError("GitHub API returned an invalid repository list")
        repositories.extend(payload)

        if 'rel="next"' not in link_header:
            return repositories
        page += 1


def collect_github_statistics(
    token: str,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Authenticate to GitHub and aggregate repositories visible to the token."""
    if not token:
        raise ValueError("REPO_STATS_TOKEN is required")

    user, _ = _request_json("/user", token, opener)
    if not isinstance(user, dict) or not isinstance(user.get("login"), str):
        raise RuntimeError("GitHub API returned an invalid authenticated user")
    login = user["login"]
    repositories = _list_repositories(token, opener)

    visibility_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    archived = 0
    forked = 0
    owned = 0
    total_open_issues = 0
    total_size_kb = 0
    total_stars = 0

    for repository in repositories:
        visibility = repository.get("visibility")
        if not isinstance(visibility, str):
            visibility = "private" if repository.get("private") else "public"
        visibility_counts[visibility] += 1
        language_counts[repository.get("language") or "Unknown"] += 1
        archived += int(bool(repository.get("archived")))
        forked += int(bool(repository.get("fork")))
        owner = repository.get("owner") or {}
        owned += int(str(owner.get("login", "")).casefold() == login.casefold())
        total_open_issues += int(repository.get("open_issues_count") or 0)
        total_size_kb += int(repository.get("size") or 0)
        total_stars += int(repository.get("stargazers_count") or 0)

    return {
        "authentication_confirmed": True,
        "authenticated_user": login,
        "execution_confirmed": True,
        "repository_scope": "repositories accessible to the configured token",
        "schema_version": 1,
        "script": SCRIPT_PATH,
        "statistics": {
            "archived_repositories": archived,
            "forked_repositories": forked,
            "owned_by_authenticated_user": owned,
            "primary_languages": dict(sorted(language_counts.items())),
            "repositories_by_visibility": dict(sorted(visibility_counts.items())),
            "total_open_issues": total_open_issues,
            "total_repositories": len(repositories),
            "total_size_kb": total_size_kb,
            "total_stars": total_stars,
        },
    }


def main() -> None:
    token = os.environ.get("REPO_STATS_TOKEN", "")
    try:
        result = collect_github_statistics(token)
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
