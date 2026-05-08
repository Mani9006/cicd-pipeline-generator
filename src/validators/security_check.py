"""
Security validator for generated CI/CD pipelines.

Scans pipeline configurations for common security issues including
hardcoded secrets, overly permissive permissions, and insecure practices.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityIssue:
    """Represents a security issue found in a pipeline."""
    message: str
    severity: str = "warning"  # critical, warning, info
    category: str = "general"
    line: int = 0


class SecurityValidator:
    """Validates pipeline content for security issues."""

    # Patterns for detecting hardcoded secrets
    SECRET_PATTERNS: dict[str, str] = {
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "aws_secret_key": r"['\"\s][0-9a-zA-Z/+]{40}['\"\s]",
        "private_key": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "api_key": r"api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]",
        "password": r"password\s*[:=]\s*['\"][^'\"\n]{4,}['\"]",
        "token": r"token\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
        "bearer_token": r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    }

    # Suspicious patterns
    SUSPICIOUS_PATTERNS: dict[str, str] = {
        "curl_to_bash": r"curl\s+.*\|\s*(?:bash|sh|zsh)",
        "wget_execute": r"wget\s+.*\s+-O\s*-\s*\|\s*(?:bash|sh|zsh)",
        "sudo_without_password": r"sudo\s+(?:-S\s+)?[^\n]*(?:NOPASSWD|passwordless)",
        "insecure_download": r"(?:curl|wget)\s+http://[^\s]+",
        "chmod_777": r"chmod\s+(?:-R\s+)?777",
        "docker_sock_mount": r"/var/run/docker\.sock",
        "disable_host_checking": r"StrictHostKeyChecking=no",
    }

    def validate(self, content: str) -> list[SecurityIssue]:
        """
        Scan pipeline content for security issues.

        Args:
            content: The pipeline configuration content.

        Returns:
            List of security issues found.
        """
        issues: list[SecurityIssue] = []
        lines = content.split("\n")

        issues.extend(self._check_hardcoded_secrets(content, lines))
        issues.extend(self._check_suspicious_patterns(content, lines))
        issues.extend(self._check_permissions(content, lines))
        issues.extend(self._check_container_security(content, lines))
        issues.extend(self._check_credential_usage(content, lines))

        return issues

    def _check_hardcoded_secrets(
        self, content: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Check for hardcoded secrets in pipeline content."""
        issues = []
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                # Check if it looks like a secret reference (e.g., secrets.XXX)
                line = lines[line_num - 1] if line_num <= len(lines) else ""
                if "secrets." in line or "${{ secrets" in line or "$" in line and "secrets" in line:
                    continue
                issues.append(SecurityIssue(
                    message=f"Potential hardcoded {secret_type} detected",
                    severity="critical",
                    category="secrets",
                    line=line_num,
                ))
        return issues

    def _check_suspicious_patterns(
        self, content: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Check for suspicious patterns indicating insecure practices."""
        issues = []
        for pattern_name, pattern in self.SUSPICIOUS_PATTERNS.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count("\n") + 1
                severity = "warning"
                if pattern_name in ("curl_to_bash", "wget_execute"):
                    severity = "critical"
                elif pattern_name in ("chmod_777", "disable_host_checking"):
                    severity = "warning"
                issues.append(SecurityIssue(
                    message=f"Suspicious pattern: {pattern_name} ({match.group(0)[:40]}...)",
                    severity=severity,
                    category="suspicious",
                    line=line_num,
                ))
        return issues

    def _check_permissions(
        self, content: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Check for overly permissive settings."""
        issues = []

        # Check for GITHUB_TOKEN with write-all permissions
        if re.search(r"permissions:\s*write-all", content):
            issues.append(SecurityIssue(
                message="Using 'write-all' permissions is overly permissive. "
                        "Use fine-grained permissions instead.",
                severity="warning",
                category="permissions",
            ))

        # Check for no branch protection
        if re.search(r"CI_(?:COMMIT|BUILD)" , content):
            # These are fine, but let's check if they skip branch checks
            pass

        # Check for running as root in Docker
        if re.search(r"USER\s+root", content, re.IGNORECASE):
            for i, line in enumerate(lines, 1):
                if re.search(r"USER\s+root", line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        message="Container running as root user. Consider using a non-root user.",
                        severity="warning",
                        category="container",
                        line=i,
                    ))

        # Check for missing branch filters
        if "branches:" not in content and "refs/heads/" not in content:
            if "push:" in content or "trigger:" in content:
                issues.append(SecurityIssue(
                    message="No branch restrictions defined. Pipeline may run on all branches.",
                    severity="info",
                    category="permissions",
                ))

        return issues

    def _check_container_security(
        self, content: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Check for container security issues."""
        issues = []

        # Check for latest tag usage
        latest_tag_pattern = re.findall(r"image:\s*([^\s:]+):latest", content)
        for match in latest_tag_pattern:
            issues.append(SecurityIssue(
                message=f"Using 'latest' tag for image '{match}'. "
                        "Pin to a specific version for reproducibility.",
                severity="warning",
                category="container",
            ))

        # Check for ADD instruction instead of COPY
        if "ADD " in content:
            issues.append(SecurityIssue(
                message="Using ADD instead of COPY. ADD can extract archives and fetch URLs, "
                        "which may be unintended.",
                severity="info",
                category="container",
            ))

        # Check for docker socket mount
        for i, line in enumerate(lines, 1):
            if "/var/run/docker.sock" in line:
                issues.append(SecurityIssue(
                    message="Mounting Docker socket is a security risk. "
                            "It grants full host Docker access.",
                    severity="critical",
                    category="container",
                    line=i,
                ))

        return issues

    def _check_credential_usage(
        self, content: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Check for proper credential usage patterns."""
        issues = []

        # Check for passwords in URLs
        url_password_pattern = re.findall(
            r"https?://[^:]+:([^@]+)@", content
        )
        for pwd in url_password_pattern:
            issues.append(SecurityIssue(
                message="Password detected in URL. Use secrets or environment variables.",
                severity="critical",
                category="secrets",
            ))

        # Check for proper secret references
        if "secrets" in content.lower():
            # Good - secrets are being used
            pass
        elif re.search(r"password|token|key", content, re.IGNORECASE):
            issues.append(SecurityIssue(
                message="Credentials may not be using proper secret management. "
                        "Consider using platform-native secret stores.",
                severity="info",
                category="secrets",
            ))

        return issues
