"""
Core pipeline generator that orchestrates template selection and output.

Routes the project configuration to the appropriate platform template
and applies deployment strategies, quality gates, and notifications.
"""

import logging
from pathlib import Path
from typing import Optional

from src.questionnaire import (
    DeployStrategy,
    DeployTarget,
    Language,
    NotificationChannel,
    Platform,
    ProjectConfig,
)
from src.strategies.blue_green import generate_blue_green_steps
from src.strategies.canary import generate_canary_steps
from src.strategies.rolling import generate_rolling_steps
from src.templates.azure_devops import AzureDevOpsTemplate
from src.templates.circleci import CircleCITemplate
from src.templates.github_actions import GitHubActionsTemplate
from src.templates.gitlab_ci import GitLabCITemplate
from src.templates.jenkins import JenkinsTemplate
from src.validators.security_check import SecurityValidator
from src.validators.syntax_check import SyntaxValidator
from src.utils.file_writer import FileWriter

logger = logging.getLogger(__name__)


class PipelineGenerator:
    """
    Main pipeline generator that coordinates template rendering,
    strategy application, validation, and file output.
    """

    def __init__(self, config: ProjectConfig) -> None:
        """
        Initialize the generator with project configuration.

        Args:
            config: The project configuration from the questionnaire.
        """
        self.config = config
        self._template_map: dict[Platform, type] = {
            Platform.GITHUB_ACTIONS: GitHubActionsTemplate,
            Platform.GITLAB_CI: GitLabCITemplate,
            Platform.JENKINS: JenkinsTemplate,
            Platform.AZURE_DEVOPS: AzureDevOpsTemplate,
            Platform.CIRCLECI: CircleCITemplate,
        }

    def generate(self, output_path: Optional[str] = None) -> str:
        """
        Generate the CI/CD pipeline configuration.

        Args:
            output_path: Optional explicit output file path.

        Returns:
            The generated pipeline configuration as a string.

        Raises:
            ValueError: If platform is not supported.
            RuntimeError: If generation fails.
        """
        logger.info(
            "Generating %s pipeline for %s project: %s",
            self.config.platform.value,
            self.config.language.value,
            self.config.project_name,
        )

        # Get template class
        template_class = self._template_map.get(self.config.platform)
        if template_class is None:
            raise ValueError(f"Unsupported platform: {self.config.platform}")

        # Instantiate and render template
        template = template_class(self.config)
        pipeline_content = template.render()

        # Apply deployment strategy
        pipeline_content = self._apply_strategy(pipeline_content)

        # Validate generated pipeline
        self._validate(pipeline_content)

        # Write to file
        writer = FileWriter(output_path or self._default_output_path())
        writer.write(pipeline_content)

        logger.info("Pipeline generated successfully at %s", writer.file_path)
        return pipeline_content

    def _apply_strategy(self, content: str) -> str:
        """
        Apply deployment strategy steps to the generated pipeline.

        Args:
            content: The generated pipeline content.

        Returns:
            Updated pipeline content with deployment strategy.
        """
        if self.config.deploy_strategy == DeployStrategy.NONE:
            return content
        if self.config.deploy_target == DeployTarget.NONE:
            return content

        logger.info(
            "Applying %s deployment strategy",
            self.config.deploy_strategy.value,
        )

        strategy_map = {
            DeployStrategy.ROLLING: generate_rolling_steps,
            DeployStrategy.BLUE_GREEN: generate_blue_green_steps,
            DeployStrategy.CANARY: generate_canary_steps,
        }

        strategy_fn = strategy_map.get(self.config.deploy_strategy)
        if strategy_fn:
            strategy_steps = strategy_fn(
                self.config.platform,
                self.config.deploy_target,
            )
            content = self._inject_strategy(content, strategy_steps)

        return content

    def _inject_strategy(self, content: str, strategy_steps: str) -> str:
        """
        Inject deployment strategy steps into the pipeline content.

        Args:
            content: The pipeline content.
            strategy_steps: The strategy steps to inject.

        Returns:
            Content with strategy steps injected.
        """
        # Platform-specific injection points
        inject_markers = {
            Platform.GITHUB_ACTIONS: "# <!-- DEPLOY_STRATEGY_PLACEHOLDER -->",
            Platform.GITLAB_CI: "# <!-- DEPLOY_STRATEGY_PLACEHOLDER -->",
            Platform.JENKINS: "// <!-- DEPLOY_STRATEGY_PLACEHOLDER -->",
            Platform.AZURE_DEVOPS: "# <!-- DEPLOY_STRATEGY_PLACEHOLDER -->",
            Platform.CIRCLECI: "# <!-- DEPLOY_STRATEGY_PLACEHOLDER -->",
        }

        marker = inject_markers.get(self.config.platform, "")
        if marker and marker in content:
            content = content.replace(marker, strategy_steps)
        else:
            # Append strategy steps at the end if no marker
            content += f"\n{strategy_steps}\n"

        return content

    def _validate(self, content: str) -> None:
        """
        Validate the generated pipeline content.

        Args:
            content: The pipeline content to validate.

        Raises:
            SyntaxError: If syntax validation fails.
            SecurityError: If security validation fails.
        """
        logger.info("Running validation checks")

        syntax_validator = SyntaxValidator(self.config.platform)
        security_validator = SecurityValidator()

        syntax_errors = syntax_validator.validate(content)
        if syntax_errors:
            for error in syntax_errors:
                logger.warning("Syntax issue: %s", error)

        security_issues = security_validator.validate(content)
        if security_issues:
            for issue in security_issues:
                logger.warning("Security concern: %s", issue)

        # Fail on critical security issues
        critical_issues = [
            issue for issue in security_issues
            if issue.severity == "critical"
        ]
        if critical_issues:
            raise RuntimeError(
                f"Critical security issues found: {len(critical_issues)}"
            )

    def _default_output_path(self) -> str:
        """
        Determine the default output file path based on platform.

        Returns:
            The default output file path.
        """
        output_map: dict[Platform, str] = {
            Platform.GITHUB_ACTIONS: ".github/workflows/ci.yml",
            Platform.GITLAB_CI: ".gitlab-ci.yml",
            Platform.JENKINS: "Jenkinsfile",
            Platform.AZURE_DEVOPS: "azure-pipelines.yml",
            Platform.CIRCLECI: ".circleci/config.yml",
        }
        return output_map.get(self.config.platform, "pipeline.yml")


def generate_pipeline(
    config: ProjectConfig,
    output_path: Optional[str] = None,
) -> str:
    """
    Convenience function to generate a pipeline from configuration.

    Args:
        config: The project configuration.
        output_path: Optional output file path.

    Returns:
        The generated pipeline content.
    """
    generator = PipelineGenerator(config)
    return generator.generate(output_path)
