"""CI/CD platform templates package."""

from src.templates.github_actions import GitHubActionsTemplate
from src.templates.gitlab_ci import GitLabCITemplate
from src.templates.jenkins import JenkinsTemplate
from src.templates.azure_devops import AzureDevOpsTemplate
from src.templates.circleci import CircleCITemplate

__all__ = [
    "GitHubActionsTemplate",
    "GitLabCITemplate",
    "JenkinsTemplate",
    "AzureDevOpsTemplate",
    "CircleCITemplate",
]
