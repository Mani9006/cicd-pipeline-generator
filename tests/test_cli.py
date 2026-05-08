"""
Tests for the CLI module.

Covers argument parsing, validation, template listing, and
the main entry point behavior.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.cli import _build_parser, _detect_platform, _list_templates, _validate_file, main
from src.questionnaire import Language, NotificationChannel, Platform, ProjectConfig


class TestArgumentParser:
    """Tests for the CLI argument parser."""

    def test_parser_help(self) -> None:
        """Test that help message is generated without error."""
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parser_version(self) -> None:
        """Test version flag exits cleanly."""
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_parser_quick_mode(self) -> None:
        """Test quick mode with language and platform."""
        parser = _build_parser()
        args = parser.parse_args(["--quick", "python", "github_actions"])
        assert args.quick == ["python", "github_actions"]

    def test_parser_output_flag(self) -> None:
        """Test output path flag."""
        parser = _build_parser()
        args = parser.parse_args(["--output", "/tmp/pipeline.yml"])
        assert args.output == "/tmp/pipeline.yml"

    def test_parser_validate_flag(self) -> None:
        """Test validate file flag."""
        parser = _build_parser()
        args = parser.parse_args(["--validate", "pipeline.yml"])
        assert args.validate == "pipeline.yml"

    def test_parser_list_flag(self) -> None:
        """Test list templates flag."""
        parser = _build_parser()
        args = parser.parse_args(["--list"])
        assert args.list is True

    def test_parser_name_flag(self) -> None:
        """Test project name flag."""
        parser = _build_parser()
        args = parser.parse_args(["--name", "my-project"])
        assert args.name == "my-project"

    def test_parser_docker_flag(self) -> None:
        """Test Docker flag."""
        parser = _build_parser()
        args = parser.parse_args(["--docker"])
        assert args.docker is True

    def test_parser_verbose_flag(self) -> None:
        """Test verbose flag."""
        parser = _build_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True


class TestListTemplates:
    """Tests for the list templates function."""

    @patch("builtins.print")
    def test_list_templates_outputs(self, mock_print: MagicMock) -> None:
        """Test that list templates produces output."""
        _list_templates()
        assert mock_print.called
        calls = [str(c) for c in mock_print.call_args_list]
        output = " ".join(calls)
        assert "Languages" in output
        assert "Platforms" in output
        assert "python" in output.lower()
        assert "github_actions" in output


class TestDetectPlatform:
    """Tests for platform detection from filenames."""

    def test_detect_github_actions(self) -> None:
        """Test detecting GitHub Actions from path."""
        assert _detect_platform(".github/workflows/ci.yml") == Platform.GITHUB_ACTIONS

    def test_detect_gitlab_ci(self) -> None:
        """Test detecting GitLab CI from filename."""
        assert _detect_platform(".gitlab-ci.yml") == Platform.GITLAB_CI

    def test_detect_jenkins(self) -> None:
        """Test detecting Jenkins from filename."""
        assert _detect_platform("Jenkinsfile") == Platform.JENKINS

    def test_detect_azure_devops(self) -> None:
        """Test detecting Azure DevOps from filename."""
        assert _detect_platform("azure-pipelines.yml") == Platform.AZURE_DEVOPS

    def test_detect_circleci(self) -> None:
        """Test detecting CircleCI from path."""
        assert _detect_platform(".circleci/config.yml") == Platform.CIRCLECI

    def test_detect_default(self) -> None:
        """Test default fallback for unknown filenames."""
        assert _detect_platform("unknown.yml") == Platform.GITHUB_ACTIONS


class TestValidateFile:
    """Tests for file validation."""

    @patch("pathlib.Path.exists")
    def test_validate_file_not_found(self, mock_exists: MagicMock) -> None:
        """Test validation of non-existent file."""
        mock_exists.return_value = False
        result = _validate_file("nonexistent.yml")
        assert result == 1

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_validate_file_found(
        self, mock_read: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test validation of existing file."""
        mock_exists.return_value = True
        mock_read.return_value = """
name: test
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        result = _validate_file(".github/workflows/ci.yml")
        assert result in (0, 1)  # 0 if no issues, 1 if warnings


class TestMainEntryPoint:
    """Tests for the main CLI entry point."""

    @patch("builtins.print")
    def test_main_list_flag(self, mock_print: MagicMock) -> None:
        """Test main with --list flag."""
        result = main(["--list"])
        assert result == 0

    @patch("src.cli.PipelineGenerator")
    @patch("src.cli._parse_config_from_args")
    def test_main_quick_mode(
        self,
        mock_parse: MagicMock,
        mock_generator: MagicMock,
    ) -> None:
        """Test main with quick mode args."""
        config = ProjectConfig()
        config.language = Language.PYTHON
        config.platform = Platform.GITHUB_ACTIONS
        config.deploy_target = None  # type: ignore[assignment]
        mock_parse.return_value = config

        mock_instance = MagicMock()
        mock_instance.generate.return_value = "generated content"
        mock_generator.return_value = mock_instance

        result = main(["--quick", "python", "github_actions"])
        assert result == 0

    @patch("src.cli.run_questionnaire")
    @patch("src.cli.PipelineGenerator")
    def test_main_interactive(
        self,
        mock_generator: MagicMock,
        mock_questionnaire: MagicMock,
    ) -> None:
        """Test main in interactive mode."""
        config = ProjectConfig()
        config.language = Language.PYTHON
        config.platform = Platform.GITHUB_ACTIONS
        mock_questionnaire.return_value = config

        mock_instance = MagicMock()
        mock_instance.generate.return_value = "generated content"
        mock_generator.return_value = mock_instance

        # Mock stdin to prevent blocking
        with patch("sys.stdin"):
            result = main([])
        assert result == 0

    def test_main_keyboard_interrupt(self) -> None:
        """Test main handles keyboard interrupt."""
        with patch(
            "src.cli.run_questionnaire",
            side_effect=KeyboardInterrupt,
        ):
            result = main([])
        assert result == 130
