pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }
    environment {
        IMAGE_NAME     = "zuriyat/sentiment-api"
        CONTAINER_NAME = "sentiment-api-test"
    }
    stages {
        stage('Fetch') {
            steps {
                echo "Stage 1: Fetching latest code from GitHub..."
                checkout scm
            }
        }
        stage('Build and Run') {
            steps {
                echo "Stage 2: Building Docker image and starting test container..."
                sh '''
                    docker rm -f ${CONTAINER_NAME} || true
                    docker pull ${IMAGE_NAME}:unstable
                    docker run -d --name ${CONTAINER_NAME} -p 5000:5000 ${IMAGE_NAME}:unstable
                    echo "Waiting for API to be ready..."
                    for i in $(seq 1 24); do
                        sleep 5
                        STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://172.17.0.1:5000/health 2>/dev/null || echo "000")
                        echo "Attempt $i: HTTP $STATUS"
                        if [ "$STATUS" = "200" ]; then
                            echo "API is ready!"
                            break
                        fi
                    done
                '''
            }
        }
        stage('Unit Test') {
            steps {
                echo "Stage 3: Running pytest unit tests..."
                sh '''
                    pip3 install requests pytest --break-system-packages || true
                    API_BASE_URL=http://172.17.0.1:5000 python3 -m pytest tests/test_api.py -v
                '''
            }
        }
        stage('UI Test') {
            steps {
                echo "Stage 4: Running Selenium UI tests on EC2 host via SSH..."
                sh '''
                    ssh -i /var/jenkins_home/.ssh/host_key \
                        -o StrictHostKeyChecking=no \
                        ubuntu@172.17.0.1 \
                        "cd /home/ubuntu/selfhealing-mlops-FA23-BAI-054 && API_BASE_URL=http://localhost:5000 python3 -m pytest tests/test_ui.py -v"
                '''
            }
        }
        stage('Build and Push') {
            steps {
                echo "Stage 5: Building both images and pushing to Docker Hub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker build -t ${IMAGE_NAME}:unstable .
                        docker push ${IMAGE_NAME}:unstable
                        docker build -t ${IMAGE_NAME}:stable -f Dockerfile.stable .
                        docker push ${IMAGE_NAME}:stable
                    '''
                }
            }
        }
        stage('Deploy to Minikube') {
            steps {
                echo "Stage 6: Deploying to Minikube via SSH..."
                sh '''
                    ssh -i /var/jenkins_home/.ssh/host_key \
                        -o StrictHostKeyChecking=no \
                        ubuntu@172.17.0.1 \
                        "set -e
                        kubectl apply -f /home/ubuntu/selfhealing-mlops-FA23-BAI-054/k8s/pvc.yaml
                        kubectl apply -f /home/ubuntu/selfhealing-mlops-FA23-BAI-054/k8s/blue-deployment.yaml
                        kubectl apply -f /home/ubuntu/selfhealing-mlops-FA23-BAI-054/k8s/green-deployment.yaml
                        kubectl apply -f /home/ubuntu/selfhealing-mlops-FA23-BAI-054/k8s/service.yaml
                        kubectl set image deployment/sentiment-blue-deployment sentiment-api=zuriyat/sentiment-api:unstable
                        kubectl rollout status deployment/sentiment-blue-deployment --timeout=180s
                        echo '=== Pods ==='
                        kubectl get pods -o wide
                        echo '=== Services ==='
                        kubectl get svc"
                '''
            }
        }
    }
    post {
        always {
            echo "Cleaning up test container..."
            sh 'docker rm -f ${CONTAINER_NAME} || true'
            sh 'docker system prune -f || true'
        }
    }
}
