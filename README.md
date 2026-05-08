# CI/CD Pipeline Generator

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square&logo=python" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License: MIT">
  <img src="https://img.shields.io/badge/tests-pytest-orange?style=flat-square&logo=pytest" alt="Tests: pytest">
  <img src="https://img.shields.io/badge/code%20style-black-black?style=flat-square" alt="Code style: black">
</p>

<p align="center">
  <strong>Generate production-grade CI/CD pipelines for 5 platforms from an interactive CLI</strong>
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#usage">Usage</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#supported-platforms">Platforms</a> &bull;
  <a href="#examples">Examples</a>
</p>

---

## Features

- **5 CI/CD Platforms** - GitHub Actions, GitLab CI, Jenkins, Azure DevOps, CircleCI
- **Interactive Questionnaire** - Step-by-step CLI wizard for configuration
- **Quick Mode** - Generate pipelines with a single command
- **6 Languages** - Python, Node.js, Go, Rust, Java, Docker
- **3 Deployment Strategies** - Rolling, Blue-Green, Canary
- **Quality Gates** - Code coverage thresholds, linting, security scanning
- **Security Validation** - Automatic scanning for hardcoded secrets and vulnerabilities
- **Syntax Validation** - Platform-specific syntax checking for generated pipelines
- **Notifications** - Slack and email integration
- **File Backup** - Automatic backup of existing pipeline files before overwrite
- **No External Dependencies** - Pure Python standard library (zero runtime deps)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/example/cicd-pipeline-generator.git
cd cicd-pipeline-generator

# Install (development mode)
pip install -e ".[dev]"

# Or run directly
python -m src.cli --help
```

### Generate Your First Pipeline

**Interactive mode (recommended for first use):**

```bash
cicd-gen
```

**Quick mode (for scripting):**

```bash
# Python project with GitHub Actions
cicd-gen --quick python github_actions

# Node.js project with Docker and Heroku deploy
cicd-gen --quick nodejs github_actions --deploy heroku --docker

# Go project with Kubernetes deploy
cicd-gen --quick go github_actions --deploy kubernetes --docker
```

**List available options:**

```bash
cicd-gen --list
```

## Usage

### Interactive Mode

Run `cicd-gen` without arguments to launch the interactive questionnaire. It will guide you through:

1. **Project name** - Your application name
2. **Language** - Python, Node.js, Go, Rust, Java, or Docker
3. **CI/CD Platform** - GitHub Actions, GitLab CI, Jenkins, Azure DevOps, CircleCI
4. **Testing** - Test framework selection based on language
5. **Quality Checks** - Linting, security scanning, code coverage
6. **Coverage Threshold** - Minimum coverage percentage (default: 80%)
7. **Docker** - Whether to build and push Docker images
8. **Deployment Target** - AWS, GCP, Azure, Heroku, Kubernetes, Docker Hub, Vercel
9. **Deployment Strategy** - Rolling, Blue-Green, or Canary
10. **Notifications** - Slack webhook and/or email recipients
11. **Branch Tracking** - Which branches trigger the pipeline

### Quick Mode Options

```bash
cicd-gen --quick <LANGUAGE> <PLATFORM> [OPTIONS]
```

| Option | Description | Example |
|--------|-------------|---------|
| `--quick` | Quick mode with language and platform | `--quick python github_actions` |
| `-n, --name` | Project name | `--name my-api` |
| `--test` | Testing framework | `--test pytest` |
| `--deploy` | Deployment target | `--deploy kubernetes` |
| `--strategy` | Deployment strategy | `--strategy blue_green` |
| `--docker` | Enable Docker build | `--docker` |
| `--coverage` | Coverage threshold (%) | `--coverage 90` |
| `--no-coverage` | Disable coverage | `--no-coverage` |
| `--no-lint` | Disable linting | `--no-lint` |
| `--no-security` | Disable security scan | `--no-security` |
| `--notify` | Notification channel | `--notify slack` |
| `-o, --output` | Output file path | `-o .github/workflows/my-pipeline.yml` |
| `--validate` | Validate existing file | `--validate .github/workflows/ci.yml` |
| `--list` | List all templates | `--list` |
| `-v, --verbose` | Enable verbose logging | `--verbose` |
| `--version` | Show version | `--version` |

### Validation

Validate existing pipeline files for syntax and security issues:

```bash
# Validate a GitHub Actions workflow
cicd-gen --validate .github/workflows/ci.yml

# Validate a GitLab CI config
cicd-gen --validate .gitlab-ci.yml

# Validate a Jenkinsfile
cicd-gen --validate Jenkinsfile
```

## Supported Platforms

| Platform | Output File | Status |
|----------|-------------|--------|
| GitHub Actions | `.github/workflows/ci.yml` | Full support |
| GitLab CI | `.gitlab-ci.yml` | Full support |
| Jenkins | `Jenkinsfile` | Full support (declarative) |
| Azure DevOps | `azure-pipelines.yml` | Full support |
| CircleCI | `.circleci/config.yml` | Full support |

## Architecture

The project follows a modular, extensible architecture:

```
src/
  cli.py           # CLI entry point and argument parsing
  questionnaire.py # Interactive configuration collection
  generator.py     # Core orchestration engine
  templates/       # Platform-specific template renderers
    github_actions.py
    gitlab_ci.py
    jenkins.py
    azure_devops.py
    circleci.py
  strategies/      # Deployment strategy generators
    rolling.py
    blue_green.py
    canary.py
  validators/      # Pipeline validation
    syntax_check.py
    security_check.py
  utils/           # Utilities
    file_writer.py
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Examples

### Python + Docker + GitHub Actions

```bash
cicd-gen --quick python github_actions --docker --deploy docker_hub
```

Generates a pipeline with:
- Python 3.11 setup
- pytest test execution
- flake8 + black linting
- Trivy + Bandit security scanning
- Codecov coverage reporting (80% threshold)
- Docker image build with Buildx
- Docker Hub push

See [examples/python_docker.yml](examples/python_docker.yml)

### Node.js + Heroku

```bash
cicd-gen --quick nodejs github_actions --deploy heroku
```

Generates a pipeline with:
- Node.js 20 setup with npm cache
- Jest test execution
- ESLint checks
- npm audit security scanning
- Heroku container deployment

See [examples/nodejs_heroku.yml](examples/nodejs_heroku.yml)

### Go + Kubernetes

```bash
cicd-gen --quick go github_actions --deploy kubernetes --docker
```

Generates a pipeline with:
- Go 1.21 setup
- go test execution
- go vet + gofmt linting
- Trivy vulnerability scanning
- Docker image build and push to GHCR
- Kubernetes deployment with kubectl

See [examples/go_k8s.yml](examples/go_k8s.yml)

## Deployment Strategies

### Rolling Deployment

Gradually replaces old instances with new ones. Best for stateless applications.

- Kubernetes: `kubectl rollout status deployment/app`
- AWS: `aws elasticbeanstalk update-environment`

### Blue-Green Deployment

Maintains two identical environments and instantly switches traffic.

- Zero-downtime deployments
- Instant rollback capability
- Requires 2x infrastructure

### Canary Deployment

Routes a small percentage of traffic (10%) to the new version first.

- Monitors health metrics before full rollout
- Automatic rollback on high error rates
- Gradual traffic shifting

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.9+ (stdlib only) |
| Testing | pytest, pytest-cov |
| Linting | flake8, black |
| Type Checking | mypy |
| CI/CD | GitHub Actions, GitLab CI, Jenkins, Azure DevOps, CircleCI |
| Security | Trivy, Bandit, npm audit |
| Coverage | Codecov |
| Packaging | setuptools, pyproject.toml |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_templates.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_validators.py::TestSecurityValidator::test_hardcoded_aws_key
```

## Project Structure

```
project_13_cicd_pipeline/
  src/
    __init__.py
    cli.py                  # CLI entry point
    questionnaire.py        # Interactive configuration
    generator.py            # Pipeline orchestrator
    templates/
      __init__.py
      github_actions.py     # GitHub Actions template
      gitlab_ci.py          # GitLab CI template
      jenkins.py            # Jenkins template
      azure_devops.py       # Azure DevOps template
      circleci.py           # CircleCI template
    strategies/
      __init__.py
      rolling.py            # Rolling deploy strategy
      blue_green.py         # Blue-green deploy strategy
      canary.py             # Canary deploy strategy
    validators/
      __init__.py
      syntax_check.py       # Syntax validator
      security_check.py     # Security scanner
    utils/
      __init__.py
      file_writer.py        # Safe file I/O
  tests/
    __init__.py
    test_cli.py             # CLI tests
    test_generator.py       # Generator tests
    test_templates.py       # Template tests
    test_validators.py      # Validator tests
  examples/
    python_docker.yml       # Python + Docker example
    nodejs_heroku.yml       # Node.js + Heroku example
    go_k8s.yml              # Go + Kubernetes example
  docs/
    architecture.md         # Architecture documentation
  requirements.txt          # Python dependencies
  pyproject.toml           # Modern Python packaging
  setup.py                 # Backward compat setup
  README.md                # This file
  LICENSE                  # MIT License
  .gitignore               # Git ignore patterns
```

## Future Improvements

- [ ] **Jinja2 Templating** - User-defined custom template snippets
- [ ] **Plugin System** - Extensible platform support via plugins
- [ ] **Remote Templates** - Fetch templates from Git repositories
- [ ] **Pipeline Visualizer** - ASCII/Mermaid diagram generation
- [ ] **Web UI** - Browser-based interface
- [ ] **ArgoCD Support** - GitOps deployment generation
- [ ] **Terraform Integration** - Infrastructure-as-code deployment
- [ ] **Custom Orbs/Actions** - Publish reusable pipeline components
- [ ] **Pipeline Diff** - Compare generated vs existing pipelines
- [ ] **Schema Validation** - Full YAML schema validation per platform

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Acknowledgments

- Inspired by the need for consistent, secure CI/CD configurations across projects
- Built with Python's standard library for zero-dependency deployment
- Security patterns based on OWASP and industry best practices
