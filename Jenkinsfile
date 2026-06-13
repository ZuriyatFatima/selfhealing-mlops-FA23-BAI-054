pipeline {
    agent any

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
                    docker build -t ${IMAGE_NAME}:unstable .
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d --name ${CONTAINER_NAME} -p 5000:5000 ${IMAGE_NAME}:unstable
                    echo "Waiting 60s for DistilBERT model to load..."
                    sleep 60
                '''
            }
        }

        stage('Unit Test') {
            steps {
                echo "Stage 3: Running pytest unit tests..."
                sh '''
                    pip3 install requests pytest --break-system-packages || true
                    API_BASE_URL=http://localhost:5000 python3 -m pytest tests/test_api.py -v
                '''
            }
        }

        stage('UI Test') {
            steps {
                echo "Stage 4: Running Selenium UI tests..."
                sh '''
                    pip3 install selenium pytest --break-system-packages || true
                    API_BASE_URL=http://localhost:5000 python3 -m pytest tests/test_ui.py -v
                '''
            }
        }

        stage('Build and Push') {
            steps {
                echo "Stage 5: Building both images and pushing to Docker Hub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${IMAGE_NAME}:unstable
                        docker build -t ${IMAGE_NAME}:stable -f Dockerfile.stable .
                        docker push ${IMAGE_NAME}:stable
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                echo "Stage 6: Deploying to Minikube..."
                withKubeConfig([credentialsId: 'kubeconfig']) {
                    sh '''
                        kubectl apply -f k8s/pvc.yaml
                        kubectl apply -f k8s/blue-deployment.yaml
                        kubectl apply -f k8s/green-deployment.yaml
                        kubectl apply -f k8s/service.yaml
                        kubectl set image deployment/sentiment-blue-deployment sentiment-api=${IMAGE_NAME}:unstable
                        kubectl rollout status deployment/sentiment-blue-deployment --timeout=180s
                    '''
                }
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
