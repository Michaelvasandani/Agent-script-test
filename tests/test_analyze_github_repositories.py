import json
from urllib.error import HTTPError

from scripts.analyze_github_repositories import collect_github_statistics


class FakeResponse:
    def __init__(self, payload, link=""):
        self._payload = json.dumps(payload).encode("utf-8")
        self.headers = {"Link": link}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._payload


class FakeOpener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_collect_github_statistics_aggregates_all_pages() -> None:
    first_page_link = '<https://api.github.com/user/repos?page=2>; rel="next"'
    opener = FakeOpener(
        [
            FakeResponse({"login": "octocat"}),
            FakeResponse(
                [
                    {
                        "archived": False,
                        "fork": False,
                        "language": "Python",
                        "open_issues_count": 2,
                        "owner": {"login": "octocat"},
                        "private": False,
                        "size": 100,
                        "stargazers_count": 3,
                        "visibility": "public",
                    },
                    {
                        "archived": True,
                        "fork": True,
                        "language": None,
                        "open_issues_count": 0,
                        "owner": {"login": "example-org"},
                        "private": True,
                        "size": 200,
                        "stargazers_count": 1,
                        "visibility": "private",
                    },
                ],
                link=first_page_link,
            ),
            FakeResponse(
                [
                    {
                        "archived": False,
                        "fork": False,
                        "language": "Go",
                        "open_issues_count": 4,
                        "owner": {"login": "example-org"},
                        "private": True,
                        "size": 50,
                        "stargazers_count": 5,
                        "visibility": "internal",
                    }
                ]
            ),
        ]
    )

    result = collect_github_statistics("test-secret", opener=opener)

    assert result == {
        "authentication_confirmed": True,
        "authenticated_user": "octocat",
        "execution_confirmed": True,
        "repository_scope": "repositories accessible to the configured token",
        "schema_version": 1,
        "script": "scripts/analyze_github_repositories.py",
        "statistics": {
            "archived_repositories": 1,
            "forked_repositories": 1,
            "owned_by_authenticated_user": 1,
            "primary_languages": {"Go": 1, "Python": 1, "Unknown": 1},
            "repositories_by_visibility": {"internal": 1, "private": 1, "public": 1},
            "total_open_issues": 6,
            "total_repositories": 3,
            "total_size_kb": 350,
            "total_stars": 9,
        },
    }
    assert len(opener.requests) == 3
    assert "page=2" in opener.requests[-1][0].full_url


def test_collect_github_statistics_uses_token_without_returning_it() -> None:
    token = "github_pat_secret-canary"
    opener = FakeOpener([FakeResponse({"login": "octocat"}), FakeResponse([])])

    result = collect_github_statistics(token, opener=opener)

    authorization = opener.requests[0][0].get_header("Authorization")
    assert authorization == f"Bearer {token}"
    assert token not in json.dumps(result)


def test_collect_github_statistics_rejects_missing_token() -> None:
    try:
        collect_github_statistics("")
    except ValueError as error:
        assert str(error) == "REPO_STATS_TOKEN is required"
    else:
        raise AssertionError("missing token was accepted")


def test_collect_github_statistics_redacts_token_from_api_errors() -> None:
    token = "github_pat_secret-canary"
    api_error = HTTPError("https://api.github.com/user", 401, "Unauthorized", {}, None)
    opener = FakeOpener([api_error])

    try:
        collect_github_statistics(token, opener=opener)
    except RuntimeError as error:
        assert "HTTP 401" in str(error)
        assert token not in str(error)
    else:
        raise AssertionError("API failure was not reported")
