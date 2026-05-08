"""
Interactive questionnaire to gather CI/CD pipeline requirements.

Collects project details including language, testing framework,
deployment target, and pipeline preferences from the user.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    DOCKER = "docker"


class Platform(str, Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLECI = "circleci"


class TestFramework(str, Enum):
    """Supported testing frameworks by language."""
    PYTEST = "pytest"
    JEST = "jest"
    MOCHA = "mocha"
    GO_TEST = "go_test"
    CARGO_TEST = "cargo_test"
    JUNIT = "junit"
    NONE = "none"


class DeployTarget(str, Enum):
    """Supported deployment targets."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    HEROKU = "heroku"
    KUBERNETES = "kubernetes"
    DOCKER_HUB = "docker_hub"
    VERCEL = "vercel"
    SSH = "ssh"
    NONE = "none"


class DeployStrategy(str, Enum):
    """Supported deployment strategies."""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    NONE = "none"


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    SLACK = "slack"
    EMAIL = "email"
    BOTH = "both"
    NONE = "none"


@dataclass
class ProjectConfig:
    """Configuration gathered from the questionnaire."""
    project_name: str = ""
    language: Language = Language.PYTHON
    platform: Platform = Platform.GITHUB_ACTIONS
    test_framework: TestFramework = TestFramework.PYTEST
    deploy_target: DeployTarget = DeployTarget.NONE
    deploy_strategy: DeployStrategy = DeployStrategy.NONE
    code_coverage: bool = True
    coverage_threshold: int = 80
    linting: bool = True
    security_scan: bool = True
    dependency_check: bool = True
    notification: NotificationChannel = NotificationChannel.NONE
    slack_webhook: str = ""
    email_recipients: str = ""
    environment_variables: list[str] = field(default_factory=list)
    branches_to_track: list[str] = field(default_factory=lambda: ["main"])
    working_directory: str = "."
    docker_enabled: bool = False
    dockerfile_path: str = "Dockerfile"


def _prompt_choice(
    question: str,
    options: list[str],
    default: Optional[int] = None
) -> str:
    """Display options and return user selection."""
    print(f"\n{question}")
    for idx, option in enumerate(options, 1):
        marker = " (default)" if default == idx - 1 else ""
        print(f"  [{idx}] {option}{marker}")
    while True:
        choice = input("Select option: ").strip()
        if choice == "" and default is not None:
            return options[default]
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("Invalid selection. Please try again.")


def _prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt user with a yes/no question."""
    suffix = " [Y/n]" if default else " [y/N]"
    response = input(f"\n{question}{suffix}: ").strip().lower()
    if response == "":
        return default
    return response in ("y", "yes")


def _prompt_text(question: str, default: str = "") -> str:
    """Prompt user for free-form text input."""
    suffix = f" (default: {default})" if default else ""
    response = input(f"\n{question}{suffix}: ").strip()
    return response if response else default


def run_questionnaire() -> ProjectConfig:
    """
    Run the interactive questionnaire and return a ProjectConfig.

    Returns:
        ProjectConfig with all user-provided settings.
    """
    config = ProjectConfig()

    print("=" * 60)
    print("  CI/CD Pipeline Generator - Interactive Setup")
    print("=" * 60)

    config.project_name = _prompt_text("Project name", "my-app")

    config.language = Language(
        _prompt_choice(
            "What is your project's primary language?",
            [lang.value for lang in Language],
            default=0
        )
    )

    config.platform = Platform(
        _prompt_choice(
            "Which CI/CD platform do you want to generate for?",
            [plat.value for plat in Platform],
            default=0
        )
    )

    # Select test framework based on language
    test_options = _get_test_options(config.language)
    if test_options:
        config.test_framework = TestFramework(
            _prompt_choice(
                "Which testing framework do you use?",
                [opt.value for opt in test_options],
                default=0
            )
        )

    config.linting = _prompt_yes_no("Enable linting/code quality checks?", True)
    config.security_scan = _prompt_yes_no("Enable security scanning?", True)

    if config.language in (Language.PYTHON, Language.NODEJS, Language.JAVA):
        config.code_coverage = _prompt_yes_no("Enable code coverage reporting?", True)
        if config.code_coverage:
            threshold = _prompt_text("Coverage threshold (percentage)", "80")
            try:
                config.coverage_threshold = max(0, min(100, int(threshold)))
            except ValueError:
                config.coverage_threshold = 80

    config.docker_enabled = _prompt_yes_no("Build and push Docker images?", False)
    if config.docker_enabled:
        config.dockerfile_path = _prompt_text("Dockerfile path", "Dockerfile")

    config.deploy_target = DeployTarget(
        _prompt_choice(
            "Where do you want to deploy?",
            [target.value for target in DeployTarget],
            default=4  # kubernetes
        )
    )

    if config.deploy_target != DeployTarget.NONE:
        config.deploy_strategy = DeployStrategy(
            _prompt_choice(
                "Which deployment strategy do you prefer?",
                [strategy.value for strategy in DeployStrategy],
                default=0
            )
        )

    config.notification = NotificationChannel(
        _prompt_choice(
            "Configure notifications?",
            [notif.value for notif in NotificationChannel],
            default=3
        )
    )

    if config.notification in (NotificationChannel.SLACK, NotificationChannel.BOTH):
        config.slack_webhook = _prompt_text("Slack webhook URL", "${{ secrets.SLACK_WEBHOOK }}")
    if config.notification in (NotificationChannel.EMAIL, NotificationChannel.BOTH):
        config.email_recipients = _prompt_text("Email recipients (comma-separated)", "")

    branches = _prompt_text("Branches to track (comma-separated)", "main, develop")
    config.branches_to_track = [b.strip() for b in branches.split(",") if b.strip()]

    print("\n" + "=" * 60)
    print("  Configuration complete!")
    print("=" * 60)

    return config


def _get_test_options(language: Language) -> list[TestFramework]:
    """Return available test frameworks for a given language."""
    mapping: dict[Language, list[TestFramework]] = {
        Language.PYTHON: [TestFramework.PYTEST],
        Language.NODEJS: [TestFramework.JEST, TestFramework.MOCHA],
        Language.GO: [TestFramework.GO_TEST],
        Language.RUST: [TestFramework.CARGO_TEST],
        Language.JAVA: [TestFramework.JUNIT],
        Language.DOCKER: [TestFramework.NONE],
    }
    return mapping.get(language, [TestFramework.NONE])
