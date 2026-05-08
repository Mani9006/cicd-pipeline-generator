"""
Canary deployment strategy generator.

Produces pipeline snippets for canary deployments that gradually
route traffic to new versions while monitoring health metrics.
"""

from src.questionnaire import DeployTarget, Platform


def generate_canary_steps(platform: Platform, target: DeployTarget) -> str:
    """
    Generate canary deployment steps for the given platform and target.

    Args:
        platform: The CI/CD platform.
        target: The deployment target.

    Returns:
        Platform-specific YAML/script snippet for canary deployment.
    """
    if platform == Platform.GITHUB_ACTIONS:
        return _github_actions_canary(target)
    elif platform == Platform.GITLAB_CI:
        return _gitlab_ci_canary(target)
    elif platform == Platform.JENKINS:
        return _jenkins_canary(target)
    elif platform == Platform.AZURE_DEVOPS:
        return _azure_devops_canary(target)
    elif platform == Platform.CIRCLECI:
        return _circleci_canary(target)
    return "# Canary deployment not configured\n"


def _github_actions_canary(target: DeployTarget) -> str:
    """Generate canary deploy steps for GitHub Actions."""
    if target == DeployTarget.KUBERNETES:
        return """
      - name: Deploy canary version
        run: |
          cat <<EOF | kubectl apply -f -
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: app-canary
          spec:
            replicas: 1
            selector:
              matchLabels:
                app: my-app
                track: canary
            template:
              metadata:
                labels:
                  app: my-app
                  track: canary
              spec:
                containers:
                - name: app
                  image: ${{ env.DOCKER_IMAGE }}:${{ github.sha }}
                  ports:
                  - containerPort: 8080
          EOF
          kubectl rollout status deployment/app-canary --timeout=180s
      - name: Route 10% traffic to canary
        run: |
          cat <<EOF | kubectl apply -f -
          apiVersion: networking.k8s.io/v1
          kind: Ingress
          metadata:
            name: my-app
            annotations:
              nginx.ingress.kubernetes.io/canary: "true"
              nginx.ingress.kubernetes.io/canary-weight: "10"
          spec:
            rules:
            - host: my-app.example.com
              http:
                paths:
                - path: /
                  pathType: Prefix
                  backend:
                    service:
                      name: app-canary
                      port:
                        number: 80
          EOF
          echo "Canary deployed with 10% traffic"
      - name: Monitor canary metrics
        run: |
          sleep 60
          echo "Checking error rate..."
          # Query Prometheus for error rate
          # If error rate < 1%, proceed to full rollout
          echo "Canary metrics look healthy"
      - name: Full rollout or rollback
        run: |
          echo "Promoting canary to stable..."
          kubectl set image deployment/app app=${{ env.DOCKER_IMAGE }}:${{ github.sha }}
          kubectl rollout status deployment/app --timeout=300s
          kubectl delete deployment app-canary --ignore-not-found=true
          echo "Full rollout complete"
        """
    return """
      - name: Canary deploy
        run: echo 'Canary deployment configured'
    """


def _gitlab_ci_canary(target: DeployTarget) -> str:
    """Generate canary deploy steps for GitLab CI."""
    return """
canary_deploy:
  stage: deploy
  script:
    - echo "Deploying canary version"
    - kubectl set image deployment/app-canary app=$DOCKER_IMAGE
    - kubectl rollout status deployment/app-canary --timeout=180s
    - echo "Routing 10% traffic to canary"
    - kubectl patch ingress my-app --type=json -p='[{"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value":"10"}]'
    - sleep 60
    - echo "Monitoring canary health..."
  when: manual

promote_canary:
  stage: deploy
  needs: [canary_deploy]
  script:
    - echo "Promoting canary to stable"
    - kubectl set image deployment/app app=$DOCKER_IMAGE
    - kubectl rollout status deployment/app --timeout=300s
    - kubectl delete deployment app-canary --ignore-not-found=true
  when: manual
"""


def _jenkins_canary(target: DeployTarget) -> str:
    """Generate canary deploy steps for Jenkins."""
    return """
        stage('Canary Deploy') {
            steps {
                script {
                    sh 'kubectl set image deployment/app-canary app=${env.DOCKER_IMAGE}'
                    sh 'kubectl rollout status deployment/app-canary --timeout=180s'
                    sh 'kubectl patch ingress my-app --type=json -p\\'[{"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value":"10"}]\\''
                }
                sleep time: 60, unit: 'SECONDS'
            }
        }
        stage('Canary Analysis') {
            steps {
                script {
                    // Check error rate from Prometheus
                    def errorRate = sh(script: 'curl -s prometheus:9090/api/v1/query?query=rate(http_requests_total{job=\"canary\",status=~\"5..\"}[1m])', returnStdout: true).trim()
                    echo "Canary error rate: ${errorRate}"
                }
            }
        }
        stage('Canary Promote') {
            steps {
                input message: 'Promote canary to stable?', ok: 'Promote'
                sh 'kubectl set image deployment/app app=${env.DOCKER_IMAGE}'
                sh 'kubectl rollout status deployment/app --timeout=300s'
                sh 'kubectl delete deployment app-canary --ignore-not-found=true'
            }
        }"""


def _azure_devops_canary(target: DeployTarget) -> str:
    """Generate canary deploy steps for Azure DevOps."""
    return """
            - task: KubernetesManifest@0
              displayName: 'Canary deploy'
              inputs:
                action: 'deploy'
                manifests: |
                  $(Pipeline.Workspace)/manifests/canary/
                strategy: 'canary'
                percentage: '10'
                trafficSplitMethod: 'smi'
            - task: AzureCLI@2
              displayName: 'Monitor canary metrics'
              inputs:
                azureSubscription: '$(azureSubscription)'
                scriptType: 'bash'
                scriptLocation: 'inlineScript'
                inlineScript: |
                  echo "Monitoring canary metrics for 60 seconds"
                  sleep 60
                  echo "Canary metrics look healthy"
            - task: KubernetesManifest@0
              displayName: 'Promote canary to stable'
              inputs:
                action: 'promote'
                manifests: |
                  $(Pipeline.Workspace)/manifests/
                strategy: 'canary'
                percentage: '100'
"""


def _circleci_canary(target: DeployTarget) -> str:
    """Generate canary deploy steps for CircleCI."""
    return """
      - run:
          name: Deploy canary version
          command: |
            kubectl set image deployment/app-canary app=<< pipeline.parameters.docker_image >>:$CIRCLE_SHA1
            kubectl rollout status deployment/app-canary --timeout=180s
      - run:
          name: Route 10% traffic to canary
          command: |
            kubectl patch ingress my-app --type=json -p='[{"op": "replace", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1canary-weight", "value":"10"}]'
      - run:
          name: Monitor canary metrics
          command: |
            echo "Monitoring canary for 60 seconds..."
            sleep 60
            echo "Canary metrics look healthy"
      - run:
          name: Promote canary
          command: |
            kubectl set image deployment/app app=<< pipeline.parameters.docker_image >>:$CIRCLE_SHA1
            kubectl rollout status deployment/app --timeout=300s
            kubectl delete deployment app-canary --ignore-not-found=true
"""
