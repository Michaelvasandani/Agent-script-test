from pathlib import Path


WORKFLOW = Path(".github/workflows/repository-script-analysis.md")
GITHUB_STATS_WORKFLOW = Path(".github/workflows/github-repository-statistics.md")


def test_workflow_is_manual_and_keeps_agent_read_only() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "issues: write" not in workflow


def test_workflow_allowlists_only_the_repository_analyzer() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'bash: ["python3 scripts/analyze_repository.py"]' in workflow
    assert "bash: [\":*\"]" not in workflow


def test_workflow_uses_safe_issue_creation() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "safe-outputs:\n  create-issue:" in workflow
    assert "## Readable summary" in workflow
    assert "## Raw script output" in workflow
    assert "## Execution confirmation" in workflow


def test_github_stats_workflow_is_manual_and_keeps_agent_read_only() -> None:
    workflow = GITHUB_STATS_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "issues: write" not in workflow


def test_github_stats_workflow_scopes_secret_to_mcp_script() -> None:
    workflow = GITHUB_STATS_WORKFLOW.read_text(encoding="utf-8")

    assert "mcp-scripts:" in workflow
    assert "run: python3 scripts/analyze_github_repositories.py" in workflow
    assert "REPO_STATS_TOKEN: ${{ secrets.REPO_STATS_TOKEN }}" in workflow
    assert 'tools:\n  bash: ["cat"]' in workflow
    assert 'bash: ["python3 scripts/analyze_github_repositories.py"]' not in workflow


def test_github_stats_workflow_uses_safe_issue_creation() -> None:
    workflow = GITHUB_STATS_WORKFLOW.read_text(encoding="utf-8")

    assert "safe-outputs:\n  create-issue:" in workflow
    assert "## Readable summary" in workflow
    assert "## Raw script output" in workflow
    assert "## Authentication and execution confirmation" in workflow
