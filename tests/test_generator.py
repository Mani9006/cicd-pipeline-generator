"""
Tests for the pipeline generator module.

Covers configuration handling, template routing, strategy application,
and the full generation pipeline.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.generator import PipelineGenerator, generate_pipeline
from src.questionnaire import (
    DeployStrategy,
    DeployTarget,
    Language,
    NotificationChannel,
    Platform,
    ProjectConfig,
    TestFramework,
)


class TestPipelineGenerator:
    """Tests for the PipelineGenerator class."""

    def create_config(
        self,
        language: Language = Language.PYTHON,
        platform: Platform = Platform.GITHUB_ACTIONS,
        deploy_target: DeployTarget = DeployTarget.KUBERNETES,
        deploy_strategy: DeployStrategy = DeployStrategy.ROLLING,
    ) -> ProjectConfig:
        """Create a test configuration."""
        config = ProjectConfig()
        config.project_name = "test-project"
        config.language = language
        config.platform = platform
        config.deploy_target = deploy_target
        config.deploy_strategy = deploy_strategy
        config.test_framework = TestFramework.PYTEST
        config.code_coverage = True
        config.coverage_threshold = 80
        config.linting = True
        config.security_scan = True
        config.notification = NotificationChannel.NONE
        config.docker_enabled = True
        config.branches_to_track = ["main", "develop"]
        return config

    def test_generator_init(self) -> None:
        """Test generator initialization."""
        config = self.create_config()
        generator = PipelineGenerator(config)
        assert generator.config == config
        assert len(generator._template_map) == 5

    def test_unsupported_platform(self) -> None:
        """Test that unsupported platform raises ValueError."""
        config = self.create_config()
        # Create a config with an unsupported platform
        config.platform = MagicMock()
        config.platform.value = "unsupported"
        generator = PipelineGenerator(config)
        with pytest.raises(ValueError, match="Unsupported platform"):
            generator.generate()

    @patch("src.generator.FileWriter")
    def test_generate_github_actions(self, mock_writer: MagicMock) -> None:
        """Test generating a GitHub Actions pipeline."""
        config = self.create_config(
            platform=Platform.GITHUB_ACTIONS,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "GitHub Actions" in result
        assert "test-project" in result
        assert "jobs:" in result
        assert "build:" in result
        assert "runs-on: ubuntu-latest" in result

    @patch("src.generator.FileWriter")
    def test_generate_gitlab_ci(self, mock_writer: MagicMock) -> None:
        """Test generating a GitLab CI pipeline."""
        config = self.create_config(
            platform=Platform.GITLAB_CI,
            deploy_strategy=DeployStrategy.NONE,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "GitLab CI" in result
        assert "stages:" in result

    @patch("src.generator.FileWriter")
    def test_generate_jenkins(self, mock_writer: MagicMock) -> None:
        """Test generating a Jenkins pipeline."""
        config = self.create_config(
            platform=Platform.JENKINS,
            deploy_strategy=DeployStrategy.NONE,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "Jenkins" in result
        assert "pipeline {" in result

    @patch("src.generator.FileWriter")
    def test_generate_azure_devops(self, mock_writer: MagicMock) -> None:
        """Test generating an Azure DevOps pipeline."""
        config = self.create_config(
            platform=Platform.AZURE_DEVOPS,
            deploy_strategy=DeployStrategy.NONE,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "Azure DevOps" in result
        assert "stages:" in result

    @patch("src.generator.FileWriter")
    def test_generate_circleci(self, mock_writer: MagicMock) -> None:
        """Test generating a CircleCI config."""
        config = self.create_config(
            platform=Platform.CIRCLECI,
            deploy_strategy=DeployStrategy.NONE,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "CircleCI" in result
        assert "version: 2.1" in result

    def test_default_output_path(self) -> None:
        """Test default output paths per platform."""
        path_map = {
            Platform.GITHUB_ACTIONS: ".github/workflows/ci.yml",
            Platform.GITLAB_CI: ".gitlab-ci.yml",
            Platform.JENKINS: "Jenkinsfile",
            Platform.AZURE_DEVOPS: "azure-pipelines.yml",
            Platform.CIRCLECI: ".circleci/config.yml",
        }
        for platform, expected_path in path_map.items():
            config = self.create_config(platform=platform)
            generator = PipelineGenerator(config)
            assert generator._default_output_path() == expected_path

    @patch("src.generator.FileWriter")
    def test_no_deploy_strategy(self, mock_writer: MagicMock) -> None:
        """Test generation without deployment strategy."""
        config = self.create_config(deploy_strategy=DeployStrategy.NONE)
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert result is not None

    @patch("src.generator.FileWriter")
    def test_no_deploy_target(self, mock_writer: MagicMock) -> None:
        """Test generation without deployment target."""
        config = self.create_config(
            deploy_target=DeployTarget.NONE,
            deploy_strategy=DeployStrategy.ROLLING,
        )
        generator = PipelineGenerator(config)
        result = generator.generate()
        assert "deploy" not in result.lower() or "DEPLOY_STRATEGY_PLACEHOLDER" not in result


class TestConvenienceFunction:
    """Tests for the generate_pipeline convenience function."""

    @patch("src.generator.PipelineGenerator")
    def test_generate_pipeline(self, mock_gen_class: MagicMock) -> None:
        """Test the convenience function."""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "test content"
        mock_gen_class.return_value = mock_instance

        config = ProjectConfig()
        result = generate_pipeline(config, "/tmp/test.yml")

        assert result == "test content"
        mock_gen_class.assert_called_once_with(config)
        mock_instance.generate.assert_called_once_with("/tmp/test.yml")
