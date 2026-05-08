"""
Tests for CI/CD platform templates.

Covers all five platform templates with various language and configuration combinations.
"""

import pytest

from src.questionnaire import (
    DeployTarget,
    Language,
    NotificationChannel,
    Platform,
    ProjectConfig,
    TestFramework,
)
from src.templates.azure_devops import AzureDevOpsTemplate
from src.templates.circleci import CircleCITemplate
from src.templates.github_actions import GitHubActionsTemplate
from src.templates.gitlab_ci import GitLabCITemplate
from src.templates.jenkins import JenkinsTemplate


def create_config(
    language: Language = Language.PYTHON,
    platform: Platform = Platform.GITHUB_ACTIONS,
    test_framework: TestFramework = TestFramework.PYTEST,
    deploy_target: DeployTarget = DeployTarget.KUBERNETES,
    notification: NotificationChannel = NotificationChannel.NONE,
    docker: bool = False,
    coverage: bool = True,
    lint: bool = True,
    security: bool = True,
) -> ProjectConfig:
    """Create a test configuration."""
    config = ProjectConfig()
    config.project_name = "test-app"
    config.language = language
    config.platform = platform
    config.test_framework = test_framework
    config.deploy_target = deploy_target
    config.notification = notification
    config.docker_enabled = docker
    config.code_coverage = coverage
    config.linting = lint
    config.security_scan = security
    config.coverage_threshold = 80
    config.branches_to_track = ["main"]
    config.slack_webhook = "https://hooks.slack.com/test"
    config.email_recipients = "team@example.com"
    return config


class TestGitHubActionsTemplate:
    """Tests for the GitHub Actions template."""

    def test_render_python(self) -> None:
        """Test rendering Python workflow."""
        config = create_config(Language.PYTHON)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "test-app" in result
        assert "python-version: 3.11" in result
        assert "pip install" in result
        assert "pytest" in result
        assert "on:" in result
        assert "jobs:" in result

    def test_render_nodejs(self) -> None:
        """Test rendering Node.js workflow."""
        config = create_config(
            Language.NODEJS,
            test_framework=TestFramework.JEST,
        )
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "node-version: 20" in result
        assert "npm ci" in result
        assert "npm run build" in result

    def test_render_go(self) -> None:
        """Test rendering Go workflow."""
        config = create_config(Language.GO, test_framework=TestFramework.GO_TEST)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "go-version: 1.21" in result
        assert "go mod download" in result
        assert "go build" in result

    def test_render_with_security(self) -> None:
        """Test rendering with security scanning."""
        config = create_config(security=True)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "Trivy" in result
        assert "bandit" in result

    def test_render_with_notifications(self) -> None:
        """Test rendering with Slack notifications."""
        config = create_config(notification=NotificationChannel.SLACK)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "Slack" in result
        assert "slackapi" in result

    def test_render_with_docker(self) -> None:
        """Test rendering with Docker build."""
        config = create_config(docker=True)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "DOCKER_IMAGE" in result
        assert "docker/build-push-action" in result

    def test_render_with_coverage(self) -> None:
        """Test rendering with code coverage."""
        config = create_config(coverage=True)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "coverage" in result.lower()
        assert "codecov" in result

    def test_render_kubernetes_deploy(self) -> None:
        """Test rendering with Kubernetes deployment."""
        config = create_config(deploy_target=DeployTarget.KUBERNETES)
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "kubectl" in result
        assert "KUBECONFIG" in result

    def test_render_heroku_deploy(self) -> None:
        """Test rendering with Heroku deployment."""
        config = create_config(
            Language.NODEJS,
            TestFramework.JEST,
            deploy_target=DeployTarget.HEROKU,
        )
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert "heroku" in result.lower()

    def test_step_block_render(self) -> None:
        """Test the StepBlock dataclass rendering."""
        from src.templates.github_actions import StepBlock
        step = StepBlock(name="Test Step", run="echo hello")
        rendered = step.render()
        assert "Test Step" in rendered
        assert "echo hello" in rendered

    def test_step_block_with_uses(self) -> None:
        """Test StepBlock with 'uses' field."""
        from src.templates.github_actions import StepBlock
        step = StepBlock(name="Checkout", uses="actions/checkout@v4")
        rendered = step.render()
        assert "actions/checkout@v4" in rendered


class TestGitLabCITemplate:
    """Tests for the GitLab CI template."""

    def test_render_python(self) -> None:
        """Test rendering Python GitLab CI config."""
        config = create_config(Language.PYTHON)
        template = GitLabCITemplate(config)
        result = template.render()
        assert "stages:" in result
        assert "python:3.11-slim" in result
        assert "pytest" in result

    def test_render_nodejs(self) -> None:
        """Test rendering Node.js GitLab CI config."""
        config = create_config(Language.NODEJS, test_framework=TestFramework.JEST)
        template = GitLabCITemplate(config)
        result = template.render()
        assert "node:20-slim" in result
        assert "npm ci" in result

    def test_render_with_docker(self) -> None:
        """Test rendering with Docker build."""
        config = create_config(docker=True)
        template = GitLabCITemplate(config)
        result = template.render()
        assert "docker_build" in result
        assert "docker push" in result

    def test_stages_order(self) -> None:
        """Test that stages are in correct order."""
        config = create_config()
        template = GitLabCITemplate(config)
        result = template.render()
        build_pos = result.find("- build")
        test_pos = result.find("- test")
        assert build_pos < test_pos


class TestJenkinsTemplate:
    """Tests for the Jenkins template."""

    def test_render_python(self) -> None:
        """Test rendering Python Jenkinsfile."""
        config = create_config(Language.PYTHON)
        template = JenkinsTemplate(config)
        result = template.render()
        assert "pipeline {" in result
        assert "python:3.11-slim" in result
        assert "stages {" in result

    def test_render_go(self) -> None:
        """Test rendering Go Jenkinsfile."""
        config = create_config(Language.GO, test_framework=TestFramework.GO_TEST)
        template = JenkinsTemplate(config)
        result = template.render()
        assert "golang:1.21" in result
        assert "go build" in result

    def test_balanced_braces(self) -> None:
        """Test that braces are balanced."""
        config = create_config()
        template = JenkinsTemplate(config)
        result = template.render()
        open_count = result.count("{")
        close_count = result.count("}")
        assert open_count == close_count

    def test_post_block(self) -> None:
        """Test that post block exists."""
        config = create_config()
        template = JenkinsTemplate(config)
        result = template.render()
        assert "post {" in result


class TestAzureDevOpsTemplate:
    """Tests for the Azure DevOps template."""

    def test_render_python(self) -> None:
        """Test rendering Python Azure pipeline."""
        config = create_config(Language.PYTHON)
        template = AzureDevOpsTemplate(config)
        result = template.render()
        assert "trigger:" in result
        assert "stages:" in result
        assert "UsePythonVersion" in result

    def test_render_go(self) -> None:
        """Test rendering Go Azure pipeline."""
        config = create_config(Language.GO, test_framework=TestFramework.GO_TEST)
        template = AzureDevOpsTemplate(config)
        result = template.render()
        assert "GoTool" in result
        assert "go test" in result


class TestCircleCITemplate:
    """Tests for the CircleCI template."""

    def test_render_python(self) -> None:
        """Test rendering Python CircleCI config."""
        config = create_config(Language.PYTHON)
        template = CircleCITemplate(config)
        result = template.render()
        assert "version: 2.1" in result
        assert "cimg/python:3.11" in result
        assert "workflows:" in result

    def test_render_nodejs(self) -> None:
        """Test rendering Node.js CircleCI config."""
        config = create_config(Language.NODEJS, test_framework=TestFramework.JEST)
        template = CircleCITemplate(config)
        result = template.render()
        assert "cimg/node:20.0" in result
        assert "npm ci" in result

    def test_render_with_orbs(self) -> None:
        """Test that orbs are included when needed."""
        config = create_config(docker=True, notification=NotificationChannel.SLACK)
        template = CircleCITemplate(config)
        result = template.render()
        assert "orbs:" in result
        assert "slack:" in result
        assert "docker:" in result


class TestAllLanguages:
    """Test all templates with all supported languages."""

    @pytest.mark.parametrize("language", [
        Language.PYTHON,
        Language.NODEJS,
        Language.GO,
        Language.DOCKER,
    ])
    def test_github_actions_all_languages(self, language: Language) -> None:
        """Test GitHub Actions with each language."""
        config = create_config(language=language)
        if language == Language.NODEJS:
            config.test_framework = TestFramework.JEST
        elif language == Language.GO:
            config.test_framework = TestFramework.GO_TEST
        elif language == Language.DOCKER:
            config.test_framework = TestFramework.NONE
        template = GitHubActionsTemplate(config)
        result = template.render()
        assert result is not None
        assert len(result) > 0

    @pytest.mark.parametrize("language", [
        Language.PYTHON,
        Language.NODEJS,
        Language.GO,
    ])
    def test_gitlab_ci_all_languages(self, language: Language) -> None:
        """Test GitLab CI with each language."""
        config = create_config(language=language)
        if language == Language.NODEJS:
            config.test_framework = TestFramework.JEST
        elif language == Language.GO:
            config.test_framework = TestFramework.GO_TEST
        template = GitLabCITemplate(config)
        result = template.render()
        assert result is not None
        assert len(result) > 0
