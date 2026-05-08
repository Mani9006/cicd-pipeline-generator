"""
Command-line interface for the CI/CD Pipeline Generator.

Provides commands for interactive pipeline generation,
batch mode, validation, and listing available templates.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.questionnaire import (
    DeployStrategy,
    DeployTarget,
    Language,
    NotificationChannel,
    Platform,
    ProjectConfig,
    run_questionnaire,
)
from src.generator import PipelineGenerator
from src.validators.syntax_check import SyntaxValidator
from src.validators.security_check import SecurityValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="cicd-gen",
        description="Generate CI/CD pipeline configurations for multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cicd-gen                         Launch interactive questionnaire
  cicd-gen --quick python github   Quick generate with language and platform
  cicd-gen --validate pipeline.yml Validate existing pipeline file
  cicd-gen --list                  List available templates
        """,
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )
    parser.add_argument(
        "--quick",
        nargs=2,
        metavar=("LANGUAGE", "PLATFORM"),
        help="Quick mode: specify language and platform directly",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: platform-specific)",
    )
    parser.add_argument(
        "--validate",
        type=str,
        metavar="FILE",
        help="Validate an existing pipeline file",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available templates"
    )
    parser.add_argument(
        "--name", "-n", type=str, default="my-app", help="Project name"
    )
    parser.add_argument(
        "--test", type=str, default=None, help="Testing framework"
    )
    parser.add_argument(
        "--deploy", type=str, default=None, help="Deployment target"
    )
    parser.add_argument(
        "--strategy", type=str, default=None, help="Deployment strategy"
    )
    parser.add_argument(
        "--docker", action="store_true", help="Enable Docker build"
    )
    parser.add_argument(
        "--coverage", type=int, default=80, help="Code coverage threshold"
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Disable code coverage"
    )
    parser.add_argument(
        "--no-lint", action="store_true", help="Disable linting"
    )
    parser.add_argument(
        "--no-security", action="store_true", help="Disable security scan"
    )
    parser.add_argument(
        "--notify", type=str, default=None, help="Notification channel"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    return parser


def _list_templates() -> None:
    """Print available templates and options."""
    print("=" * 60)
    print("  Available CI/CD Pipeline Templates")
    print("=" * 60)

    print("\nLanguages:")
    for lang in Language:
        print(f"  - {lang.value}")

    print("\nPlatforms:")
    for plat in Platform:
        print(f"  - {plat.value}")

    print("\nDeployment Targets:")
    for target in DeployTarget:
        print(f"  - {target.value}")

    print("\nDeployment Strategies:")
    for strat in DeployStrategy:
        print(f"  - {strat.value}")

    print("\nNotification Channels:")
    for notif in NotificationChannel:
        print(f"  - {notif.value}")

    print("\nPre-built Configurations:")
    configs = [
        ("python", "github_actions", "Python app with pytest, Docker build"),
        ("python", "gitlab_ci", "Python app with GitLab CI, coverage"),
        ("nodejs", "github_actions", "Node.js app with Jest, Vercel deploy"),
        ("nodejs", "circleci", "Node.js app with Mocha, Heroku deploy"),
        ("go", "github_actions", "Go app with go test, Kubernetes deploy"),
        ("go", "azure_devops", "Go app with Azure DevOps, AKS deploy"),
        ("docker", "github_actions", "Docker build and push workflow"),
        ("docker", "gitlab_ci", "Docker build with GitLab CI registry"),
    ]
    for lang, plat, desc in configs:
        print(f"  {lang} + {plat}: {desc}")
    print()


def _validate_file(file_path: str) -> int:
    """
    Validate an existing pipeline file.

    Args:
        file_path: Path to the pipeline file.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("File not found: %s", file_path)
        return 1

    content = path.read_text()
    platform = _detect_platform(path.name)

    print(f"Validating {file_path} (detected platform: {platform.value})")

    syntax_validator = SyntaxValidator(platform)
    security_validator = SecurityValidator()

    syntax_errors = syntax_validator.validate(content)
    security_issues = security_validator.validate(content)

    print(f"\nSyntax check: {len(syntax_errors)} issues found")
    for error in syntax_errors:
        print(f"  [{error.severity}] Line {error.line}: {error.message}")

    print(f"\nSecurity check: {len(security_issues)} issues found")
    for issue in security_issues:
        print(f"  [{issue.severity}] {issue.message}")

    if syntax_errors or security_issues:
        return 1
    print("\nValidation passed!")
    return 0


def _detect_platform(filename: str) -> Platform:
    """Detect CI/CD platform from filename."""
    mapping = {
        ".github": Platform.GITHUB_ACTIONS,
        "gitlab-ci": Platform.GITLAB_CI,
        "Jenkinsfile": Platform.JENKINS,
        "azure-pipelines": Platform.AZURE_DEVOPS,
        ".circleci": Platform.CIRCLECI,
    }
    for key, platform in mapping.items():
        if key in filename:
            return platform
    return Platform.GITHUB_ACTIONS


def _parse_config_from_args(args: argparse.Namespace) -> ProjectConfig:
    """
    Build a ProjectConfig from CLI arguments.

    Args:
        args: Parsed CLI arguments.

    Returns:
        A ProjectConfig populated from CLI args.
    """
    config = ProjectConfig()
    config.project_name = args.name

    if args.quick:
        config.language = Language(args.quick[0].lower())
        config.platform = Platform(args.quick[1].lower())

    if args.test:
        from src.questionnaire import TestFramework
        config.test_framework = TestFramework(args.test.lower())

    if args.deploy:
        config.deploy_target = DeployTarget(args.deploy.lower())

    if args.strategy:
        config.deploy_strategy = DeployStrategy(args.strategy.lower())

    if args.docker:
        config.docker_enabled = True

    config.code_coverage = not args.no_coverage
    config.coverage_threshold = args.coverage
    config.linting = not args.no_lint
    config.security_scan = not args.no_security

    if args.notify:
        config.notification = NotificationChannel(args.notify.lower())

    return config


def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        _list_templates()
        return 0

    if args.validate:
        return _validate_file(args.validate)

    try:
        if args.quick:
            logger.info("Quick mode: %s on %s", args.quick[0], args.quick[1])
            config = _parse_config_from_args(args)
        else:
            config = run_questionnaire()

        generator = PipelineGenerator(config)
        content = generator.generate(args.output)

        print("\n" + "=" * 60)
        print("  Pipeline generated successfully!")
        print("=" * 60)
        return 0

    except KeyboardInterrupt:
        logger.info("\nGeneration cancelled by user.")
        return 130
    except Exception as exc:
        logger.error("Generation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
