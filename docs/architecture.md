# CI/CD Pipeline Generator - Architecture

## Overview

The CI/CD Pipeline Generator is a Python CLI tool that generates production-ready CI/CD pipeline configurations for multiple platforms. It uses an interactive questionnaire or command-line arguments to gather project requirements, then renders platform-specific templates with deployment strategies, quality gates, and notifications.

## System Architecture

```
+---------------------+     +---------------------+     +---------------------+
|       CLI Layer     | --> |   Business Logic    | --> |   Template Layer    |
|                     |     |                     |     |                     |
|  - argparse parser  |     |  - PipelineGenerator|     |  - GitHub Actions   |
|  - quick mode       |     |  - Config router    |     |  - GitLab CI        |
|  - validate mode    |     |  - Strategy applier |     |  - Jenkins          |
|  - list mode        |     |  - Validation       |     |  - Azure DevOps     |
|                     |     |                     |     |  - CircleCI         |
+---------------------+     +----------+----------+     +---------------------+
                                     |
                                     v
+---------------------+     +---------------------+     +---------------------+
|   Strategy Layer    |     |   Validator Layer   |     |   Utility Layer     |
|                     |     |                     |     |                     |
|  - Rolling deploy   |     |  - Syntax check     |     |  - FileWriter       |
|  - Blue-green       |     |  - Security check   |     |  - Backup/restore   |
|  - Canary deploy    |     |  - Error reporting  |     |  - Path management  |
+---------------------+     +---------------------+     +---------------------+
```

## Module Breakdown

### 1. CLI Layer (`src/cli.py`)

The CLI module provides multiple entry modes:

- **Interactive Mode**: Launches `run_questionnaire()` to gather all configuration via prompts
- **Quick Mode**: Accepts `--quick <language> <platform>` for rapid generation
- **Validation Mode**: Validates existing pipeline files with `--validate <file>`
- **List Mode**: Lists all available templates and options

**Key Functions:**
- `main(argv)` - Entry point that routes to appropriate handler
- `_build_parser()` - Configures argparse with all options
- `_validate_file(file_path)` - File validation wrapper
- `_list_templates()` - Template listing output

### 2. Questionnaire (`src/questionnaire.py`)

The interactive configuration collector uses a `ProjectConfig` dataclass and enums for type safety.

**Enums:**
- `Language` - python, nodejs, go, rust, java, docker
- `Platform` - github_actions, gitlab_ci, jenkins, azure_devops, circleci
- `TestFramework` - pytest, jest, mocha, go_test, cargo_test, junit
- `DeployTarget` - aws, gcp, azure, heroku, kubernetes, docker_hub, vercel, ssh
- `DeployStrategy` - rolling, blue_green, canary
- `NotificationChannel` - slack, email, both, none

**Key Functions:**
- `run_questionnaire()` - Full interactive prompt flow
- `_prompt_choice()` - Multiple choice input
- `_prompt_yes_no()` - Boolean input
- `_prompt_text()` - Free-form text input

### 3. Generator (`src/generator.py`)

The core orchestrator class that coordinates all components.

**Class: `PipelineGenerator`**

| Method | Purpose |
|--------|---------|
| `__init__(config)` | Initialize with template routing map |
| `generate(output_path)` | Main generation pipeline |
| `_apply_strategy(content)` | Injects deployment strategy steps |
| `_inject_strategy(content, steps)` | Platform-aware strategy injection |
| `_validate(content)` | Runs syntax and security validators |
| `_default_output_path()` | Returns platform-specific default path |

**Generation Flow:**
1. Select template class from `_template_map`
2. Instantiate template with `ProjectConfig`
3. Render base template
4. Apply deployment strategy (if configured)
5. Run validation (syntax + security)
6. Write output file

### 4. Templates (`src/templates/`)

Each template is a class that implements a `render()` method returning the complete pipeline content as a string.

**Template Base Pattern:**
```python
class PlatformTemplate:
    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

    def render(self) -> str:
        # Render complete pipeline content
        pass
```

**Supported Platforms:**

| Platform | File | Output Path |
|----------|------|-------------|
| GitHub Actions | `github_actions.py` | `.github/workflows/ci.yml` |
| GitLab CI | `gitlab_ci.py` | `.gitlab-ci.yml` |
| Jenkins | `jenkins.py` | `Jenkinsfile` |
| Azure DevOps | `azure_devops.py` | `azure-pipelines.yml` |
| CircleCI | `circleci.py` | `.circleci/config.yml` |

**Template Features per Platform:**
- Language-specific setup (Python, Node.js, Go, Rust, Java, Docker)
- Test framework integration (pytest, jest, mocha, go test, cargo test, JUnit)
- Linting configuration (flake8/black, eslint, go vet, clippy, checkstyle)
- Security scanning (Trivy, Bandit, npm audit, CodeQL)
- Code coverage reporting (pytest-cov, jest, Go coverage, Codecov)
- Docker build and push (with caching)
- Kubernetes/AWS/Heroku/ACR deployment
- Slack and email notifications

### 5. Deployment Strategies (`src/strategies/`)

Three deployment strategies with platform-specific implementations.

**Strategy: Rolling**
- Gradually replaces instances with new version
- Supports Kubernetes `rollout status` and AWS Elastic Beanstalk
- Minimal downtime, simple rollback

**Strategy: Blue-Green**
- Maintains two identical environments
- Instant traffic switch with zero downtime
- Supports manual approval gates

**Strategy: Canary**
- Deploys to small subset of traffic (10%)
- Monitors health metrics before full rollout
- Automatic rollback on failure
- Supports SMI traffic splitting (Azure DevOps)

**Implementation Pattern:**
Each strategy module exposes a single function:
```python
def generate_strategy_steps(platform: Platform, target: DeployTarget) -> str:
    # Returns platform-specific YAML/script snippet
```

### 6. Validators (`src/validators/`)

**Syntax Validator (`syntax_check.py`)**
- Platform-specific validation rules
- YAML structure checks (indentation, required keys)
- Brace balancing (Jenkins, GitHub Actions expressions)
- Jenkins-specific Groovy checks

**Security Validator (`security_check.py`)**
- Secret detection (AWS keys, private keys, API keys, tokens)
- Suspicious pattern detection (curl | bash, chmod 777, Docker socket mount)
- Permission checks (write-all, root user)
- Container security (latest tag, ADD vs COPY)
- Credential usage patterns

### 7. Utilities (`src/utils/`)

**FileWriter (`file_writer.py`)**
- Atomic file writes
- Automatic directory creation
- Backup of existing files
- Restore on failure

## Data Flow

```
User Input (CLI/Interactive)
    |
    v
ProjectConfig (dataclass)
    |
    v
PipelineGenerator
    |---> Select Template Class
    |---> Template.render() -> Base Pipeline
    |---> Strategy Generator -> Strategy Steps
    |---> _inject_strategy() -> Complete Pipeline
    |---> SyntaxValidator.validate() -> Errors/Warnings
    |---> SecurityValidator.validate() -> Issues
    |---> FileWriter.write() -> Output File
```

## Error Handling

The application uses a layered error handling strategy:

1. **CLI Layer**: Catches `KeyboardInterrupt`, `SystemExit`, and generic exceptions
2. **Generator Layer**: Validates configuration before generation
3. **Template Layer**: All template methods return strings (no I/O)
4. **Validator Layer**: Non-blocking - collects all issues before reporting
5. **File Layer**: Atomic writes with automatic backup/restore

## Testing Strategy

- **Unit Tests**: Individual template methods, validators, utilities
- **Integration Tests**: Full generation pipeline with mocked I/O
- **Parametrized Tests**: All language/platform combinations
- **Mock Usage**: CLI questionnaire mocked for automated testing

## Future Enhancements

1. **Template Customization**: Jinja2-based templates with user-defined snippets
2. **Plugin System**: Extensible platform support via plugins
3. **Remote Templates**: Fetch templates from Git repositories
4. **Pipeline Visualizer**: ASCII or Mermaid diagram generation
5. **GitHub App**: Web-based UI for pipeline generation
