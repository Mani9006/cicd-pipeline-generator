"""
Rolling deployment strategy generator.

Produces pipeline snippets for rolling deployments that gradually
replace old instances with new ones to minimize downtime.
"""

from src.questionnaire import DeployTarget, Platform


def generate_rolling_steps(platform: Platform, target: DeployTarget) -> str:
    """
    Generate rolling deployment steps for the given platform and target.

    Args:
        platform: The CI/CD platform.
        target: The deployment target.

    Returns:
        Platform-specific YAML/script snippet for rolling deployment.
    """
    if platform == Platform.GITHUB_ACTIONS:
        return _github_actions_rolling(target)
    elif platform == Platform.GITLAB_CI:
        return _gitlab_ci_rolling(target)
    elif platform == Platform.JENKINS:
        return _jenkins_rolling(target)
    elif platform == Platform.AZURE_DEVOPS:
        return _azure_devops_rolling(target)
    elif platform == Platform.CIRCLECI:
        return _circleci_rolling(target)
    return "# Rolling deployment not configured\n"


def _github_actions_rolling(target: DeployTarget) -> str:
    """Generate rolling deploy steps for GitHub Actions."""
    if target == DeployTarget.KUBERNETES:
        return """
      - name: Rolling deploy to Kubernetes
        run: |
          kubectl rollout status deployment/app --timeout=300s
          kubectl get pods -l app=my-app
        """
    elif target == DeployTarget.AWS:
        return """
      - name: Rolling deploy to AWS
        run: |
          aws elasticbeanstalk update-environment \\
            --environment-name prod \\
            --version-label ${{ github.sha }}
          aws elasticbeanstalk wait environment-updated --environment-name prod
        """
    return """
      - name: Rolling deploy
        run: echo 'Rolling deployment in progress'
    """


def _gitlab_ci_rolling(target: DeployTarget) -> str:
    """Generate rolling deploy steps for GitLab CI."""
    if target == DeployTarget.KUBERNETES:
        return """
rolling_deploy:
  stage: deploy
  script:
    - kubectl rollout status deployment/app --timeout=300s
    - kubectl get pods -l app=my-app
  when: manual
"""
    return """
rolling_deploy:
  stage: deploy
  script:
    - echo "Rolling deployment completed"
  when: manual
"""


def _jenkins_rolling(target: DeployTarget) -> str:
    """Generate rolling deploy steps for Jenkins."""
    if target == DeployTarget.KUBERNETES:
        return """
        stage('Rolling Deploy') {
            steps {
                sh 'kubectl rollout status deployment/app --timeout=300s'
                sh 'kubectl get pods -l app=my-app'
            }
        }"""
    return """
        stage('Rolling Deploy') {
            steps {
                sh 'echo "Rolling deployment completed"'
            }
        }"""


def _azure_devops_rolling(target: DeployTarget) -> str:
    """Generate rolling deploy steps for Azure DevOps."""
    if target == DeployTarget.KUBERNETES:
        return """
            - task: KubernetesManifest@0
              displayName: 'Rolling deploy'
              inputs:
                action: 'deploy'
                manifests: |
                  $(Pipeline.Workspace)/manifests/
                strategy: 'rolling'
                percentage: '25'
"""
    return """
            - script: |
                echo "Rolling deployment completed"
              displayName: 'Rolling deploy'
"""


def _circleci_rolling(target: DeployTarget) -> str:
    """Generate rolling deploy steps for CircleCI."""
    if target == DeployTarget.KUBERNETES:
        return """
      - run:
          name: Rolling deploy to Kubernetes
          command: |
            kubectl rollout status deployment/app --timeout=300s
            kubectl get pods -l app=my-app
"""
    return """
      - run:
          name: Rolling deploy
          command: echo "Rolling deployment completed"
"""
