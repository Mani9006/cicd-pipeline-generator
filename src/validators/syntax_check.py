"""
Syntax validator for generated CI/CD pipeline configurations.

Checks for common syntax errors, structural issues, and platform-specific
requirements across GitHub Actions, GitLab CI, Jenkins, Azure DevOps, and CircleCI.
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.questionnaire import Platform


@dataclass
class SyntaxError:
    """Represents a syntax validation error."""
    message: str
    line: int = 0
    severity: str = "error"  # error, warning, info
    platform: str = ""


class SyntaxValidator:
    """Validates pipeline syntax for various CI/CD platforms."""

    def __init__(self, platform: Platform) -> None:
        """
        Initialize validator for the specified platform.

        Args:
            platform: The CI/CD platform to validate for.
        """
        self.platform = platform

    def validate(self, content: str) -> list[SyntaxError]:
        """
        Validate pipeline content for syntax issues.

        Args:
            content: The pipeline configuration content.

        Returns:
            List of syntax errors found.
        """
        errors: list[SyntaxError] = []
        lines = content.split("\n")

        # Common checks for all platforms
        errors.extend(self._check_empty_content(content))
        if errors:
            return errors
        errors.extend(self._check_trailing_whitespace(lines))

        # Platform-specific checks
        if self.platform == Platform.GITHUB_ACTIONS:
            errors.extend(self._validate_github_actions(content, lines))
        elif self.platform == Platform.GITLAB_CI:
            errors.extend(self._validate_gitlab_ci(content, lines))
        elif self.platform == Platform.JENKINS:
            errors.extend(self._validate_jenkins(content, lines))
        elif self.platform == Platform.AZURE_DEVOPS:
            errors.extend(self._validate_azure_devops(content, lines))
        elif self.platform == Platform.CIRCLECI:
            errors.extend(self._validate_circleci(content, lines))

        return errors

    def _check_empty_content(self, content: str) -> list[SyntaxError]:
        """Check if content is empty."""
        if not content or not content.strip():
            return [SyntaxError("Pipeline content is empty", severity="error")]
        return []

    def _check_trailing_whitespace(self, lines: list[str]) -> list[SyntaxError]:
        """Check for trailing whitespace in lines."""
        errors = []
        for i, line in enumerate(lines, 1):
            if line.endswith(" ") or line.endswith("\t"):
                errors.append(SyntaxError(
                    f"Trailing whitespace on line {i}",
                    line=i,
                    severity="warning",
                ))
        return errors

    def _validate_github_actions(self, content: str, lines: list[str]) -> list[SyntaxError]:
        """Validate GitHub Actions workflow syntax."""
        errors = []

        # Check required 'on' trigger (as a standalone YAML key, not substring of 'runs-on')
        has_on_trigger = any(
            line.strip().startswith("on:") or line.strip() == "on:"
            for line in lines
        )
        if not has_on_trigger:
            errors.append(SyntaxError(
                "Missing 'on' trigger definition",
                severity="error",
                platform="github_actions",
            ))

        # Check 'jobs' keyword
        if "jobs:" not in content:
            errors.append(SyntaxError(
                "Missing 'jobs' section",
                severity="error",
                platform="github_actions",
            ))

        # Check 'runs-on' in jobs
        job_blocks = re.findall(r"(\w+):\n\s+name:.*?\n", content)
        if "runs-on:" not in content:
            errors.append(SyntaxError(
                "Missing 'runs-on' in job definition",
                severity="error",
                platform="github_actions",
            ))

        # Check for unbalanced braces in expressions
        open_braces = content.count("${{")
        close_braces = content.count("}}")
        if open_braces != close_braces:
            errors.append(SyntaxError(
                f"Unbalanced braces: {open_braces} open, {close_braces} close",
                severity="error",
                platform="github_actions",
            ))

        # Check indentation (GitHub Actions uses 2 spaces)
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                if indent % 2 != 0:
                    errors.append(SyntaxError(
                        f"Incorrect indentation (should be multiple of 2) on line {i}",
                        line=i,
                        severity="warning",
                        platform="github_actions",
                    ))

        return errors

    def _validate_gitlab_ci(self, content: str, lines: list[str]) -> list[SyntaxError]:
        """Validate GitLab CI syntax."""
        errors = []

        # Check for stages or hidden jobs
        if "stages:" not in content and not re.search(r"^\.\w+:", content, re.MULTILINE):
            errors.append(SyntaxError(
                "Missing 'stages' definition",
                severity="warning",
                platform="gitlab_ci",
            ))

        # Check script presence in jobs
        job_pattern = re.compile(r"^(\w+):\s*$", re.MULTILINE)
        for match in job_pattern.finditer(content):
            job_name = match.group(1)
            if job_name == "stages" or job_name.startswith("."):
                continue
            # Check if job has script section
            start = match.end()
            next_match = job_pattern.search(content, start)
            end = next_match.start() if next_match else len(content)
            job_block = content[start:end]
            if "script:" not in job_block:
                errors.append(SyntaxError(
                    f"Job '{job_name}' missing 'script' section",
                    severity="error",
                    platform="gitlab_ci",
                ))

        # Check for invalid characters in job names
        invalid_chars = re.findall(r"^([\w\s]+):\s*$", content, re.MULTILINE)
        for name in invalid_chars:
            if " " in name.strip():
                errors.append(SyntaxError(
                    f"Job name '{name.strip()}' contains spaces",
                    severity="error",
                    platform="gitlab_ci",
                ))

        return errors

    def _validate_jenkins(self, content: str, lines: list[str]) -> list[SyntaxError]:
        """Validate Jenkinsfile (declarative) syntax."""
        errors = []

        # Check pipeline block
        if "pipeline {" not in content:
            errors.append(SyntaxError(
                "Missing 'pipeline' block",
                severity="error",
                platform="jenkins",
            ))

        # Check balanced braces
        open_count = content.count("{")
        close_count = content.count("}")
        if open_count != close_count:
            errors.append(SyntaxError(
                f"Unbalanced braces: {open_count} open, {close_count} close",
                severity="error",
                platform="jenkins",
            ))

        # Check stages block
        if "stages {" not in content:
            errors.append(SyntaxError(
                "Missing 'stages' block",
                severity="warning",
                platform="jenkins",
            ))

        # Check agent definition
        if "agent" not in content:
            errors.append(SyntaxError(
                "Missing 'agent' definition",
                severity="warning",
                platform="jenkins",
            ))

        return errors

    def _validate_azure_devops(self, content: str, lines: list[str]) -> list[SyntaxError]:
        """Validate Azure DevOps pipeline syntax."""
        errors = []

        # Check trigger definition
        if "trigger:" not in content:
            errors.append(SyntaxError(
                "Missing 'trigger' definition",
                severity="warning",
                platform="azure_devops",
            ))

        # Check stages
        if "stages:" not in content and "jobs:" not in content and "steps:" not in content:
            errors.append(SyntaxError(
                "Missing pipeline structure (stages/jobs/steps)",
                severity="error",
                platform="azure_devops",
            ))

        # Check task syntax
        task_pattern = re.findall(r"- task:\s*(\S+)@(\d+)", content)
        if not task_pattern and "script:" not in content:
            errors.append(SyntaxError(
                "No tasks or scripts defined",
                severity="warning",
                platform="azure_devops",
            ))

        # Check for displayName
        if "displayName:" not in content:
            errors.append(SyntaxError(
                "Steps should have 'displayName' for readability",
                severity="info",
                platform="azure_devops",
            ))

        return errors

    def _validate_circleci(self, content: str, lines: list[str]) -> list[SyntaxError]:
        """Validate CircleCI config syntax."""
        errors = []

        # Check version
        if not re.search(r"^version:\s*2\.1\s*$", content, re.MULTILINE):
            errors.append(SyntaxError(
                "Missing or incorrect CircleCI version (should be 2.1)",
                severity="error",
                platform="circleci",
            ))

        # Check jobs or workflows
        if "jobs:" not in content and "workflows:" not in content:
            errors.append(SyntaxError(
                "Missing 'jobs' or 'workflows' section",
                severity="error",
                platform="circleci",
            ))

        # Check workflows reference existing jobs
        if "workflows:" in content:
            # Extract job names
            job_names = re.findall(r"^  (\w+):\s*$", content, re.MULTILINE)
            # Check if jobs section exists
            if "jobs:" not in content:
                errors.append(SyntaxError(
                    "Missing 'jobs' section definition",
                    severity="error",
                    platform="circleci",
                ))

        # Check executor or docker image in jobs
        if "executor:" not in content and "docker:" not in content:
            errors.append(SyntaxError(
                "Jobs should specify an executor or Docker image",
                severity="warning",
                platform="circleci",
            ))

        # Check orbs syntax
        orb_pattern = re.findall(r"^  \w+:\s*(\S+)@(\d+\.\d+(?:\.\d+)?)$", content, re.MULTILINE)
        for orb_name, version in orb_pattern:
            if not re.match(r"^\d+\.\d+(?:\.\d+)?$", version):
                errors.append(SyntaxError(
                    f"Orb '{orb_name}' has invalid version format: {version}",
                    severity="warning",
                    platform="circleci",
                ))

        return errors
