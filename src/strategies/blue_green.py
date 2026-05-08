"""
Blue-green deployment strategy generator.

Produces pipeline snippets for blue-green deployments that maintain
two identical environments and switch traffic between them.
"""

from src.questionnaire import DeployTarget, Platform


def generate_blue_green_steps(platform: Platform, target: DeployTarget) -> str:
    """
    Generate blue-green deployment steps for the given platform and target.

    Args:
        platform: The CI/CD platform.
        target: The deployment target.

    Returns:
        Platform-specific YAML/script snippet for blue-green deployment.
    """
    if platform == Platform.GITHUB_ACTIONS:
        return _github_actions_blue_green(target)
    elif platform == Platform.GITLAB_CI:
        return _gitlab_ci_blue_green(target)
    elif platform == Platform.JENKINS:
        return _jenkins_blue_green(target)
    elif platform == Platform.AZURE_DEVOPS:
        return _azure_devops_blue_green(target)
    elif platform == Platform.CIRCLECI:
        return _circleci_blue_green(target)
    return "# Blue-green deployment not configured\n"


def _github_actions_blue_green(target: DeployTarget) -> str:
    """Generate blue-green deploy steps for GitHub Actions."""
    if target == DeployTarget.KUBERNETES:
        return """
      - name: Blue-green deploy
        run: |
          ACTIVE_COLOR=$(kubectl get service my-app -o jsonpath='{.spec.selector.color}')
          INACTIVE_COLOR=$([ "$ACTIVE_COLOR" == "blue" ] && echo "green" || echo "blue")
          echo "Deploying to $INACTIVE_COLOR"
          kubectl set image deployment/app-$INACTIVE_COLOR app=${{ env.DOCKER_IMAGE }}:${{ github.sha }}
          kubectl rollout status deployment/app-$INACTIVE_COLOR --timeout=300s
      - name: Switch traffic
        run: |
          kubectl patch service my-app -p '{"spec":{"selector":{"color":"'$INACTIVE_COLOR'"}}}'
          echo "Traffic switched to $INACTIVE_COLOR"
      - name: Verify deployment
        run: |
          kubectl get pods -l app=my-app
          kubectl get service my-app -o wide
        """
    elif target == DeployTarget.AWS:
        return """
      - name: Blue-green deploy to Elastic Beanstalk
        run: |
          aws elasticbeanstalk create-application-version \\
            --application-name my-app \\
            --version-label ${{ github.sha }} \\
            --source-bundle S3Bucket=my-bucket,S3Key=my-app.zip
          aws elasticbeanstalk swap-environment-cnames \\
            --source-environment-name my-app-blue \\
            --destination-environment-name my-app-green
        """
    return """
      - name: Blue-green deploy
        run: echo 'Blue-green deployment configured'
    """


def _gitlab_ci_blue_green(target: DeployTarget) -> str:
    """Generate blue-green deploy steps for GitLab CI."""
    return """
blue_green_deploy:
  stage: deploy
  script:
    - echo "Determining active environment"
    - ACTIVE=$(kubectl get service my-app -o jsonpath='{.spec.selector.color}')
    - INACTIVE=$([ "$ACTIVE" == "blue" ] && echo "green" || echo "blue")
    - echo "Deploying to $INACTIVE environment"
    - kubectl set image deployment/app-$INACTIVE app=$DOCKER_IMAGE
    - kubectl rollout status deployment/app-$INACTIVE --timeout=300s
    - echo "Switching traffic to $INACTIVE"
    - kubectl patch service my-app -p '{"spec":{"selector":{"color":"'$INACTIVE'"}}}'
  when: manual
"""


def _jenkins_blue_green(target: DeployTarget) -> str:
    """Generate blue-green deploy steps for Jenkins."""
    return """
        stage('Blue-Green Deploy') {
            steps {
                script {
                    def active = sh(
                        script: 'kubectl get service my-app -o jsonpath="{.spec.selector.color}"',
                        returnStdout: true
                    ).trim()
                    def inactive = (active == "blue") ? "green" : "blue"
                    sh "kubectl set image deployment/app-${inactive} app=${env.DOCKER_IMAGE}"
                    sh "kubectl rollout status deployment/app-${inactive} --timeout=300s"
                    input message: "Switch traffic to ${inactive}?", ok: 'Switch'
                    sh "kubectl patch service my-app -p '{\\"spec\\":{\\"selector\\":{\\"color\\":\\"${inactive}\\"}}}'"
                }
            }
        }"""


def _azure_devops_blue_green(target: DeployTarget) -> str:
    """Generate blue-green deploy steps for Azure DevOps."""
    return """
            - task: KubernetesManifest@0
              displayName: 'Blue-green deploy'
              inputs:
                action: 'deploy'
                manifests: |
                  $(Pipeline.Workspace)/manifests/
                strategy: 'canary'
                percentage: '100'
                trafficSplitMethod: 'smi'
"""


def _circleci_blue_green(target: DeployTarget) -> str:
    """Generate blue-green deploy steps for CircleCI."""
    return """
      - run:
          name: Blue-green deploy
          command: |
            ACTIVE=$(kubectl get service my-app -o jsonpath='{.spec.selector.color}')
            INACTIVE=$([ "$ACTIVE" == "blue" ] && echo "green" || echo "blue")
            kubectl set image deployment/app-$INACTIVE app=<< pipeline.parameters.docker_image >>:$CIRCLE_SHA1
            kubectl rollout status deployment/app-$INACTIVE --timeout=300s
            echo "Deployment to $INACTIVE complete. Run swap job to switch traffic."
      - run:
          name: Switch traffic
          command: |
            read -p "Switch traffic? (y/n) " CONFIRM
            if [ "$CONFIRM" = "y" ]; then
              kubectl patch service my-app -p '{"spec":{"selector":{"color":"'green'"}}}'
            fi
          when: manual
"""
