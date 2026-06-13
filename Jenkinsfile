pipeline {
    agent any

    environment {
        IMAGE_NAME     = "zuriyat/sentiment-api"
        IMAGE_TAG      = "unstable"
        CONTAINER_NAME = "sentiment-api-test"
    }

    stages {

        // STAGE 1: Grab the latest code from GitHub (whatever triggered this build)
        stage('Fetch') {
            steps {
                echo "Stage 1: Fetching latest code from GitHub..."
                checkout scm
            }
        }

        // STAGE 2: Build the Docker image and spin up a test container
        stage('Build and Run') {
            steps {
                echo "Stage 2: Building Docker image and starting test container..."
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

                    # Remove any leftover test container from a previous run
                    docker rm -f ${CONTAINER_NAME} || true

                    # Run the new image, exposing the API port (5000) and metrics port (8000)
                    docker run -d --name ${CONTAINER_NAME} -p 5000:5000 -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}

                    # Give the Flask app + model a moment to load
                    sleep 15
                '''
            }
        }

        // STAGE 3: Run pytest API tests against the running container
        stage('Unit Test') {
            steps {
                echo "Stage 3: Running pytest unit tests..."
                sh '''
                    pip install -r requirements.txt --break-system-packages || true
                    API_BASE_URL=http://localhost:5000 python3 -m pytest tests/test_api.py -v
                '''
            }
        }

        // STAGE 4: Run Selenium UI tests against the running container
        stage('UI Test') {
            steps {
                echo "Stage 4: Running Selenium UI tests..."
                sh '''
                    API_BASE_URL=http://localhost:5000 python3 -m pytest tests/test_ui.py -v
                '''
            }
        }

        // STAGE 5: Push the tested image to Docker Hub
        stage('Build and Push') {
            steps {
                echo "Stage 5: Pushing image to Docker Hub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }

        // STAGE 6: Deploy the new image to the blue deployment on Minikube
        stage('Deploy to Minikube') {
            steps {
                echo "Stage 6: Deploying to Minikube (blue deployment)..."
                withKubeConfig([credentialsId: 'kubeconfig']) {
                    sh '''
                        kubectl set image deployment/sentiment-blue-deployment sentiment-api=${IMAGE_NAME}:${IMAGE_TAG}
                        kubectl rollout status deployment/sentiment-blue-deployment --timeout=120s
                    '''
                }
            }
        }
    }

    // Always clean up the test container, pass or fail
    post {
        always {
            echo "Cleaning up test container..."
            sh 'docker rm -f ${CONTAINER_NAME} || true'
        }
    }
}
